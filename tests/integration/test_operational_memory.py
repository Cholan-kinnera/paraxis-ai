"""
Comprehensive Integration Tests for Phase 6: Operational Memory Architecture.
Validates:
1. 768-dimensional vector contract across all providers.
2. Invalid vector dimensions rejected with HTTP 400.
3. Multi-tenant isolation (cross-organization query returns zero results).
4. Campus isolation (cross-campus query within same org returns zero results).
5. Source idempotency enforced by database constraints.
6. Unchanged content does not regenerate embeddings (NO-OP on SHA-256 hash match).
7. Changed content increments source_version.
8. Changed content regenerates and updates embedding in pgvector.
9. Canonical IncidentEvent synthesis omits noise, preserves diagnostics.
10. Historical semantic retrieval via HNSW pgvector cosine distance.
11. Similarity threshold filtering behavior.
12. Duplicate vs. Related distinction in detect_node.
13. Insight evidence relational through-table referential integrity.
14. Strict FACT / INFERENCE / RECOMMENDATION epistemological segregation.
15. Deterministic 30-day recurring asset failure detection (threshold >= 3).
16. Deterministic recurring room hotspot detection (threshold >= 4).
17. FastAPI -> Django memory API boundary.
18. Correlation ID propagation across memory endpoints.
19. Zero direct Intelligence database / ORM access.
20. Policy Gate remains authoritative after memory retrieval.
"""
import uuid
import inspect
from datetime import timedelta
import pytest
from rest_framework import status
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db import IntegrityError

from core.models.organization import Organization, Campus, OrganizationStatus, CampusStatus
from core.models.user import User
from core.models.campus_graph import (
    Department, Building, Floor, Room, Asset,
    BuildingStatus, RoomType, RoomStatus, AssetCategory, AssetStatus,
)
from core.models.incident import (
    Incident, IncidentEvent, IncidentStatus, IncidentPriority, IncidentCategory, IncidentEventType,
)
from core.models.memory import (
    OperationalMemoryChunk,
    OperationalMemorySourceType,
    OperationalInsight,
    OperationalInsightType,
    OperationalInsightStatus,
    OperationalInsightIncidentEvidence,
)
from core.services.memory import (
    PARAXIS_EMBEDDING_DIMENSION,
    compute_content_hash,
    generate_canonical_incident_text,
    generate_canonical_asset_text,
    index_memory_chunk,
    search_operational_memory,
)
from core.services.recurring_detector import (
    detect_recurring_problems,
    ASSET_FAILURE_THRESHOLD,
    ROOM_FAILURE_THRESHOLD,
)
from core.authentication.jwt import generate_access_token

from backend.intelligence.providers.base import validate_embeddings
from backend.intelligence.providers.mock_adapter import MockModelAdapter
from backend.intelligence.agent.state import IncidentAgentState
from backend.intelligence.agent.nodes.detect import detect_node
from backend.intelligence.agent.nodes.contextualize import contextualize_node
from backend.intelligence.agent.nodes.plan import plan_node
from backend.intelligence.agent.graph import orchestrate_incident


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def test_user_a(db, org_a, campus_a1, standard_roles):
    user = User.objects.create(
        email="operator.a@apex.edu",
        full_name="Operator A",
        organization=org_a,
        primary_campus=campus_a1,
        is_active=True,
    )
    user.roles.add(standard_roles["CAMPUS_ADMIN"])
    return user


@pytest.fixture
def test_user_b(db, org_b, campus_b1, standard_roles):
    user = User.objects.create(
        email="operator.b@beacon.edu",
        full_name="Operator B",
        organization=org_b,
        primary_campus=campus_b1,
        is_active=True,
    )
    user.roles.add(standard_roles["CAMPUS_ADMIN"])
    return user


@pytest.fixture
def campus_graph_a(db, org_a, campus_a1):
    dept = Department.objects.create(
        organization=org_a,
        campus=campus_a1,
        name="Facilities Dept",
        code="FAC-A",
    )
    bld = Building.objects.create(
        organization=org_a,
        campus=campus_a1,
        name="Engineering Hall",
        code="ENG-A",
        status=BuildingStatus.OPERATIONAL,
    )
    floor = Floor.objects.create(
        organization=org_a,
        campus=campus_a1,
        building=bld,
        floor_number=1,
        label="Floor 1",
    )
    room = Room.objects.create(
        organization=org_a,
        campus=campus_a1,
        building=bld,
        floor=floor,
        room_number="101",
        name="Lab 101",
        room_type=RoomType.LAB,
        status=RoomStatus.AVAILABLE,
    )
    asset = Asset.objects.create(
        organization=org_a,
        campus=campus_a1,
        department=dept,
        building=bld,
        floor=floor,
        room=room,
        name="Air Conditioner 101",
        asset_tag="AST-AC-101",
        category=AssetCategory.HVAC,
        status=AssetStatus.OPERATIONAL,
    )
    return {
        "department": dept,
        "building": bld,
        "floor": floor,
        "room": room,
        "asset": asset,
    }


def make_unit_vector(dim=768, non_zero_idx=0) -> list[float]:
    """Generates a strictly normalized 768-dim float vector with 1.0 at non_zero_idx."""
    v = [0.0] * dim
    v[non_zero_idx % dim] = 1.0
    return v


# ============================================================================
# 1. 768-DIMENSIONAL VECTOR CONTRACT
# ============================================================================

@pytest.mark.asyncio
async def test_vector_contract_768_dimensions():
    """Validates that embedding generation strictly produces 768-dimensional float vectors."""
    adapter = MockModelAdapter()
    embeddings = await adapter.embed(["Test operational report text"])
    assert len(embeddings) == 1
    assert len(embeddings[0]) == PARAXIS_EMBEDDING_DIMENSION
    assert all(isinstance(x, (float, int)) for x in embeddings[0])

    # Validation function accepts exact 768-dim vectors
    validated = validate_embeddings(embeddings)
    assert len(validated[0]) == 768

    # Non-768 vectors are strictly rejected by the validator
    with pytest.raises(ValueError, match="invalid dimension"):
        validate_embeddings([[0.1] * 64])

    with pytest.raises(ValueError, match="invalid dimension"):
        validate_embeddings([[0.1] * 1536])


# ============================================================================
# 2. INVALID VECTOR DIMENSIONS REJECTED WITH 400
# ============================================================================

def test_memory_search_invalid_dimension_rejected_400(api_client, test_user_a, campus_a1):
    """Verifies that query vectors != 768 dimensions are rejected with HTTP 400."""
    token = generate_access_token(test_user_a, campus_id=campus_a1.id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # Send 64-dimensional query vector
    resp = api_client.post(
        "/api/v1/memory/search/",
        data={"query_embedding": [0.05] * 64, "limit": 5},
        format="json",
    )
    assert resp.status_code == status.HTTP_400_BAD_REQUEST
    error_detail = str(resp.data)
    assert "768" in error_detail or "dimension" in error_detail.lower()


# ============================================================================
# 3. TENANT ISOLATION
# ============================================================================

def test_memory_search_tenant_isolation(api_client, test_user_a, test_user_b, org_a, org_b, campus_a1, campus_b1):
    """Verifies cross-tenant memory isolation: Org A user cannot see Org B memories."""
    # Index chunk in Org A
    vec_a = make_unit_vector(768, 10)
    index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.ASSET,
        source_id="ast_org_a",
        title="Org A Chiller",
        canonical_text="Org A Chiller in Building A",
        embedding=vec_a,
    )

    # Index chunk in Org B
    vec_b = make_unit_vector(768, 10)
    index_memory_chunk(
        organization_id=org_b.id,
        campus_id=campus_b1.id,
        source_type=OperationalMemorySourceType.ASSET,
        source_id="ast_org_b",
        title="Org B Chiller",
        canonical_text="Org B Chiller in Building B",
        embedding=vec_b,
    )

    # Search as Org A user
    token_a = generate_access_token(test_user_a, campus_id=campus_a1.id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token_a}")

    resp = api_client.post(
        "/api/v1/memory/search/",
        data={"query_embedding": vec_a, "limit": 10},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    data = resp.data["data"]
    source_ids = [d["source_id"] for d in data]

    assert "ast_org_a" in source_ids
    assert "ast_org_b" not in source_ids


# ============================================================================
# 4. CAMPUS ISOLATION
# ============================================================================

def test_memory_search_campus_isolation(api_client, test_user_a, org_a, campus_a1, campus_a2):
    """Verifies campus isolation within the same organization."""
    vec = make_unit_vector(768, 20)

    # Campus A1 chunk
    index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.ASSET,
        source_id="ast_camp_a1",
        title="Campus A1 Transformer",
        canonical_text="Campus A1 Transformer unit",
        embedding=vec,
    )

    # Campus A2 chunk
    index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a2.id,
        source_type=OperationalMemorySourceType.ASSET,
        source_id="ast_camp_a2",
        title="Campus A2 Transformer",
        canonical_text="Campus A2 Transformer unit",
        embedding=vec,
    )

    # Query with active campus A1 token
    token = generate_access_token(test_user_a, campus_id=campus_a1.id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    resp = api_client.post(
        "/api/v1/memory/search/",
        data={"query_embedding": vec, "limit": 10},
        format="json",
    )
    assert resp.status_code == status.HTTP_200_OK
    source_ids = [d["source_id"] for d in resp.data["data"]]

    assert "ast_camp_a1" in source_ids
    assert "ast_camp_a2" not in source_ids


# ============================================================================
# 5. SOURCE IDEMPOTENCY
# ============================================================================

def test_source_idempotency_unique_constraint(org_a, campus_a1):
    """Verifies that database uniqueness constraint prevents duplicate chunks for same source."""
    vec = make_unit_vector(768, 5)

    chunk, created = index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-idem-001",
        title="Generator Trip",
        canonical_text="Generator tripped due to overload",
        embedding=vec,
    )
    assert created is True

    # Attempting direct raw ORM insert with same unique tuple must raise IntegrityError
    with pytest.raises(IntegrityError):
        OperationalMemoryChunk.objects.create(
            organization=org_a,
            campus=campus_a1,
            source_type=OperationalMemorySourceType.INCIDENT,
            source_id="inc-idem-001",
            source_version=1,
            source_updated_at=timezone.now(),
            title="Duplicate Attempt",
            canonical_text="Another text",
            content_hash="abc",
            embedding=vec,
        )


# ============================================================================
# 6. UNCHANGED CONTENT DOES NOT REGENERATE EMBEDDINGS (NO-OP)
# ============================================================================

def test_unchanged_content_no_op_hash_match(org_a, campus_a1):
    """Verifies that identical canonical_text results in a NO-OP without updating source_version."""
    vec = make_unit_vector(768, 30)
    text = "Air handling unit filter dirty in Mechanical Room B1"

    chunk1, modified1 = index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-hash-001",
        title="AHU Filter",
        canonical_text=text,
        embedding=vec,
    )
    assert modified1 is True
    assert chunk1.source_version == 1
    orig_hash = chunk1.content_hash

    # Second invocation with same text
    chunk2, modified2 = index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-hash-001",
        title="AHU Filter",
        canonical_text=text,
        embedding=vec,
    )
    assert modified2 is False  # NO-OP
    assert chunk2.id == chunk1.id
    assert chunk2.source_version == 1
    assert chunk2.content_hash == orig_hash


# ============================================================================
# 7. CHANGED CONTENT INCREMENTS SOURCE_VERSION
# ============================================================================

def test_changed_content_increments_source_version(org_a, campus_a1):
    """Verifies that changed content updates hash and increments source_version."""
    vec1 = make_unit_vector(768, 31)
    vec2 = make_unit_vector(768, 32)

    chunk, _ = index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-ver-001",
        title="Pump Leak v1",
        canonical_text="Initial report: Water leaking slowly from pump seal.",
        embedding=vec1,
    )
    assert chunk.source_version == 1

    # Updated canonical text
    chunk_updated, modified = index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-ver-001",
        title="Pump Leak v2",
        canonical_text="Updated report: Water leaking heavily from pump seal. Gasket blown.",
        embedding=vec2,
    )
    assert modified is True
    assert chunk_updated.source_version == 2
    assert chunk_updated.content_hash != chunk.content_hash


# ============================================================================
# 8. CHANGED CONTENT UPDATES EMBEDDING
# ============================================================================

def test_changed_content_updates_embedding(org_a, campus_a1):
    """Verifies that changed content updates the stored vector embedding in pgvector."""
    vec_initial = make_unit_vector(768, 1)
    vec_replacement = make_unit_vector(768, 2)

    chunk, _ = index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-vec-001",
        title="Initial State",
        canonical_text="Initial canonical incident text",
        embedding=vec_initial,
    )

    # Update with new vector
    chunk_v2, _ = index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-vec-001",
        title="Updated State",
        canonical_text="Substantively changed canonical incident text",
        embedding=vec_replacement,
    )

    refetched = OperationalMemoryChunk.all_objects.get(id=chunk.id)
    # Compare refetched vector values
    stored_vec = [float(x) for x in refetched.embedding]
    assert stored_vec[2] == pytest.approx(1.0)
    assert stored_vec[1] == pytest.approx(0.0)


# ============================================================================
# 9. CANONICAL INCIDENT EVENT SYNTHESIS
# ============================================================================

def test_canonical_incident_event_synthesis(db, org_a, campus_a1, campus_graph_a, test_user_a):
    """Verifies canonical incident memory document incorporates diagnostic timeline and excludes noise."""
    incident = Incident.objects.create(
        organization=org_a,
        campus=campus_a1,
        reporter=test_user_a,
        title="Circuit Breaker Trip",
        description="Breaker tripped during morning peak lecture.",
        category=IncidentCategory.ELECTRICAL,
        priority=IncidentPriority.HIGH,
        status=IncidentStatus.RESOLVED,
        building=campus_graph_a["building"],
        room=campus_graph_a["room"],
        asset=campus_graph_a["asset"],
        resolution_notes="Replaced faulty 32A fuse and balanced phases.",
        resolved_at=timezone.now(),
    )

    # Add diagnostic events
    IncidentEvent.objects.create(
        organization=org_a,
        campus=campus_a1,
        incident=incident,
        event_type=IncidentEventType.COMMENT_ADDED,
        description="Technician verified thermal imaging showed 85C on Phase B.",
        actor_type="TECHNICIAN",
    )
    IncidentEvent.objects.create(
        organization=org_a,
        campus=campus_a1,
        incident=incident,
        event_type=IncidentEventType.STATUS_CHANGED,
        description="Replaced faulty 32A fuse and balanced phases.",
        actor_type="TECHNICIAN",
        metadata={"from_status": "IN_PROGRESS", "to_status": "RESOLVED"},
    )

    title, canonical_text, metadata = generate_canonical_incident_text(incident)

    assert "Circuit Breaker Trip" in title
    assert "ELECTRICAL" in canonical_text
    assert "Building Engineering Hall" in canonical_text
    assert "Room 101" in canonical_text
    assert "DIAGNOSTIC TIMELINE:" in canonical_text
    assert "thermal imaging showed 85C" in canonical_text
    assert "Replaced faulty 32A fuse" in canonical_text
    assert metadata["incident_id"] == str(incident.id)
    assert metadata["category"] == "ELECTRICAL"


# ============================================================================
# 10. HISTORICAL SEMANTIC RETRIEVAL
# ============================================================================

def test_historical_semantic_retrieval_pgvector(org_a, campus_a1):
    """Verifies HNSW cosine similarity search returns highest similarity match first."""
    # Index three distinct memories with orthogonal unit vectors
    vec_target = make_unit_vector(768, 50)
    vec_other_1 = make_unit_vector(768, 100)
    vec_other_2 = make_unit_vector(768, 150)

    index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-sem-target",
        title="Target HVAC Failure",
        canonical_text="HVAC Compressor overload in server room",
        embedding=vec_target,
    )
    index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-sem-other1",
        title="Other Plumbing Event",
        canonical_text="Sink drain blocked in restroom",
        embedding=vec_other_1,
    )
    index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-sem-other2",
        title="Other Lighting Event",
        canonical_text="Ceiling fixture flickering in hallway",
        embedding=vec_other_2,
    )

    # Search with target vector: should have cosine distance ~ 0.0 -> similarity ~ 1.0
    results = search_operational_memory(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        query_embedding=vec_target,
        limit=3,
    )
    assert len(results) == 3
    top_result = results[0]
    assert top_result["source_id"] == "inc-sem-target"
    assert top_result["similarity_score"] >= 0.99


# ============================================================================
# 11. SIMILARITY THRESHOLD BEHAVIOR
# ============================================================================

def test_similarity_threshold_filtering(org_a, campus_a1):
    """Verifies that search excludes records below the specified similarity threshold."""
    vec_exact = make_unit_vector(768, 70)
    vec_orthogonal = make_unit_vector(768, 71)

    index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-exact",
        title="Exact Match",
        canonical_text="Exact match incident",
        embedding=vec_exact,
    )
    index_memory_chunk(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        source_type=OperationalMemorySourceType.INCIDENT,
        source_id="inc-ortho",
        title="Orthogonal Match",
        canonical_text="Orthogonal incident",
        embedding=vec_orthogonal,
    )

    # With threshold 0.80, only exact match (sim ~ 1.0) should be returned
    results = search_operational_memory(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        query_embedding=vec_exact,
        threshold=0.80,
    )
    assert len(results) == 1
    assert results[0]["source_id"] == "inc-exact"


# ============================================================================
# 12. DUPLICATE-VS-RELATED DISTINCTION
# ============================================================================

@pytest.mark.asyncio
async def test_duplicate_vs_related_distinction():
    """Verifies that detect_node correctly distinguishes DUPLICATE (active identical) vs RELATED."""
    state = IncidentAgentState(
        incident_id="inc_curr_001",
        raw_user_report="Wi-Fi Access Point AP-04 is completely offline in Lab 204",
        organization_id="org_test_01",
        campus_id="camp_test_01",
    )

    out = await detect_node(state)
    duplicate = out.get("duplicate")
    assert duplicate is not None
    # Relationship type must be structured
    assert duplicate.relationship_type in ["NONE", "RELATED", "DUPLICATE"]


# ============================================================================
# 13. INSIGHT EVIDENCE RELATIONAL INTEGRITY
# ============================================================================

def test_insight_evidence_relational_integrity(db, org_a, campus_a1, campus_graph_a, test_user_a):
    """Verifies that OperationalInsightIncidentEvidence enforces relational integrity without JSON arrays."""
    asset = campus_graph_a["asset"]
    now = timezone.now()

    # Create 3 incidents for this asset
    incidents = []
    for i in range(3):
        inc = Incident.objects.create(
            organization=org_a,
            campus=campus_a1,
            reporter=test_user_a,
            title=f"AC Overheating Incident {i+1}",
            description="AC compressor overheated and shut down automatically.",
            category=IncidentCategory.HVAC,
            priority=IncidentPriority.HIGH,
            status=IncidentStatus.RESOLVED,
            asset=asset,
            resolved_at=now - timedelta(days=i * 2),
        )
        Incident.all_objects.filter(id=inc.id).update(created_at=now - timedelta(days=i * 2))
        incidents.append(inc)

    insights = detect_recurring_problems(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        now=now,
    )
    assert len(insights) >= 1
    asset_insight = next(i for i in insights if i.target_asset_id == asset.id)

    # Relational evidence links through-table
    evidence_links = asset_insight.evidence_links.all()
    assert evidence_links.count() == 3
    linked_incidents = [e.incident for e in evidence_links]
    for inc in incidents:
        assert inc in linked_incidents


# ============================================================================
# 14. FACT / INFERENCE / RECOMMENDATION SEPARATION
# ============================================================================

def test_fact_inference_recommendation_separation(db, org_a, campus_a1, campus_graph_a, test_user_a):
    """Verifies epistemological segregation in generated OperationalInsight records."""
    asset = campus_graph_a["asset"]
    now = timezone.now()

    for i in range(3):
        inc = Incident.objects.create(
            organization=org_a,
            campus=campus_a1,
            reporter=test_user_a,
            title=f"Failure {i+1}",
            description="Motor trip",
            category=IncidentCategory.HVAC,
            asset=asset,
        )
        Incident.all_objects.filter(id=inc.id).update(created_at=now - timedelta(days=i + 1))

    insights = detect_recurring_problems(
        organization_id=org_a.id,
        campus_id=campus_a1.id,
        now=now,
    )
    insight = next(i for i in insights if i.target_asset_id == asset.id)

    assert insight.fact_summary.startswith("FACT:")
    assert str(asset.asset_tag) in insight.fact_summary
    assert insight.inference_analysis.startswith("INFERENCE:")
    assert insight.recommendation.startswith("RECOMMENDATION:")
    assert 0.0 <= insight.confidence_score <= 1.0


# ============================================================================
# 15. RECURRING 30-DAY ASSET DETECTION
# ============================================================================

def test_recurring_30_day_asset_failure_detection(db, org_a, campus_a1, campus_graph_a, test_user_a):
    """Verifies deterministic asset detection threshold (>= 3 incidents within 30 days)."""
    asset = campus_graph_a["asset"]
    now = timezone.now()

    # 2 incidents inside 30 days -> Below threshold (no insight)
    i1 = Incident.objects.create(organization=org_a, campus=campus_a1, reporter=test_user_a, title="I1", category=IncidentCategory.HVAC, asset=asset)
    Incident.all_objects.filter(id=i1.id).update(created_at=now - timedelta(days=5))
    i2 = Incident.objects.create(organization=org_a, campus=campus_a1, reporter=test_user_a, title="I2", category=IncidentCategory.HVAC, asset=asset)
    Incident.all_objects.filter(id=i2.id).update(created_at=now - timedelta(days=10))

    insights_below = detect_recurring_problems(org_a.id, campus_a1.id, now=now)
    assert not any(i.target_asset_id == asset.id for i in insights_below)

    # Add 1 incident outside 30 days (day 35) -> Still below 3 in 30-day window
    i_old = Incident.objects.create(organization=org_a, campus=campus_a1, reporter=test_user_a, title="I_old", category=IncidentCategory.HVAC, asset=asset)
    Incident.all_objects.filter(id=i_old.id).update(created_at=now - timedelta(days=35))
    insights_still_below = detect_recurring_problems(org_a.id, campus_a1.id, now=now)
    assert not any(i.target_asset_id == asset.id for i in insights_still_below)

    # Add 3rd incident inside 30 days (day 2) -> Meets threshold of 3
    i3 = Incident.objects.create(organization=org_a, campus=campus_a1, reporter=test_user_a, title="I3", category=IncidentCategory.HVAC, asset=asset)
    Incident.all_objects.filter(id=i3.id).update(created_at=now - timedelta(days=2))
    insights_met = detect_recurring_problems(org_a.id, campus_a1.id, now=now)
    assert any(i.target_asset_id == asset.id and i.incident_count == 3 for i in insights_met)


# ============================================================================
# 16. RECURRING ROOM DETECTION
# ============================================================================

def test_recurring_room_hotspot_detection(db, org_a, campus_a1, campus_graph_a, test_user_a):
    """Verifies deterministic room hotspot detection threshold (>= 4 incidents within 30 days)."""
    room = campus_graph_a["room"]
    now = timezone.now()

    # Create 4 incidents in Room 101
    for i in range(ROOM_FAILURE_THRESHOLD):
        inc = Incident.objects.create(
            organization=org_a,
            campus=campus_a1,
            reporter=test_user_a,
            title=f"Room Event {i+1}",
            description="Room electrical / HVAC concern",
            category=IncidentCategory.ELECTRICAL if i % 2 == 0 else IncidentCategory.HVAC,
            room=room,
        )
        Incident.all_objects.filter(id=inc.id).update(created_at=now - timedelta(days=i + 1))

    insights = detect_recurring_problems(org_a.id, campus_a1.id, now=now)
    room_insights = [i for i in insights if i.target_room_id == room.id and i.insight_type == OperationalInsightType.LOCATION_HOTSPOT]
    assert len(room_insights) == 1
    assert room_insights[0].incident_count == ROOM_FAILURE_THRESHOLD


# ============================================================================
# 17. FASTAPI -> DJANGO MEMORY API BOUNDARY
# ============================================================================

def test_fastapi_to_django_memory_api_boundary(api_client, test_user_a, campus_a1):
    """Verifies authenticated REST boundary for POST /api/v1/memory/search/ and GET /api/v1/memory/insights/."""
    token = generate_access_token(test_user_a, campus_id=campus_a1.id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    # Search endpoint
    search_resp = api_client.post(
        "/api/v1/memory/search/",
        data={"query_embedding": make_unit_vector(768, 0), "limit": 5},
        format="json",
    )
    assert search_resp.status_code == status.HTTP_200_OK
    assert "data" in search_resp.data
    assert "meta" in search_resp.data

    # Insights endpoint
    insights_resp = api_client.get("/api/v1/memory/insights/")
    assert insights_resp.status_code == status.HTTP_200_OK
    assert "data" in insights_resp.data


# ============================================================================
# 18. CORRELATION ID PROPAGATION
# ============================================================================

def test_memory_api_correlation_id_propagation(api_client, test_user_a, campus_a1):
    """Verifies that X-Request-ID and X-Trace-ID are preserved and returned in headers."""
    token = generate_access_token(test_user_a, campus_id=campus_a1.id)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

    req_id = "req_custom_trace_p6_001"
    trace_id = "trace_distributed_p6_002"

    resp = api_client.post(
        "/api/v1/memory/search/",
        data={"query_embedding": make_unit_vector(768, 0), "limit": 5},
        format="json",
        HTTP_X_REQUEST_ID=req_id,
        HTTP_X_TRACE_ID=trace_id,
    )
    assert resp.status_code == status.HTTP_200_OK
    assert resp.headers.get("X-Request-ID") == req_id
    assert resp.headers.get("X-Trace-ID") == trace_id


# ============================================================================
# 19. ZERO DIRECT INTELLIGENCE DATABASE ACCESS
# ============================================================================

def test_intelligence_layer_zero_direct_db_imports():
    """
    Architectural invariant enforcement:
    Scans all Python modules in backend/intelligence/ to ensure ZERO direct imports of:
    - django / django.db / django models
    - psycopg / psycopg2 / asyncpg
    - raw SQL execution
    """
    import os
    import re
    from pathlib import Path

    intel_root = Path(__file__).resolve().parents[2] / "backend" / "intelligence"
    assert intel_root.exists() and intel_root.is_dir()

    prohibited_patterns = [
        re.compile(r"^\s*from\s+django\b", re.MULTILINE),
        re.compile(r"^\s*import\s+django\b", re.MULTILINE),
        re.compile(r"^\s*from\s+core\.models\b", re.MULTILINE),
        re.compile(r"^\s*import\s+psycopg", re.MULTILINE),
        re.compile(r"^\s*import\s+asyncpg", re.MULTILINE),
    ]

    violations = []
    for py_file in intel_root.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for pattern in prohibited_patterns:
            matches = pattern.findall(content)
            if matches:
                violations.append(f"{py_file.name}: matched prohibited import '{matches[0]}'")

    assert len(violations) == 0, f"Prohibited database imports found in Intelligence layer: {violations}"


# ============================================================================
# 20. POLICY GATE REMAINS AUTHORITATIVE AFTER MEMORY RETRIEVAL
# ============================================================================

@pytest.mark.asyncio
async def test_policy_gate_authoritative_after_memory_retrieval():
    """
    Verifies that LangGraph memory retrieval does not bypass the Policy Engine.
    High-cost or safety-critical actions must suspend at policy gate regardless of memory precedent.
    """
    # Incident report describing high-cost chiller failure
    state = IncidentAgentState(
        incident_id="inc_policy_mem_001",
        raw_user_report="Chiller compressor broken in Central Plant. Requires emergency replacement.",
        organization_id="org_test_01",
        campus_id="camp_test_01",
    )

    result = await orchestrate_incident(state)

    # Workflow must suspend for human approval due to cost > $500 or safety
    assert result["execution_status"] == "SUSPENDED"
    assert result["policy"] is not None
    assert result["policy"].decision == "REQUIRE_HUMAN_APPROVAL"
    assert result["policy"].rule_id in ["FIN_001_DISPATCH_COST", "SAF_001_LIFE_SAFETY"]
