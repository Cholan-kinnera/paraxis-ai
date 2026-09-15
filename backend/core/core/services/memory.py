"""
Operational Memory & Knowledge Persistence Services for Paraxis AI.
Owns canonical text synthesis, SHA-256 hashing, idempotent vector ingestion,
and pgvector cosine similarity search execution in Django Core.
Adheres to ADR-002, ADR-003, and Phase 6 Architecture Plan v2.
"""
import hashlib
import logging
import uuid
from typing import Optional, Dict, Any, List, Tuple
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from pgvector.django import CosineDistance

from core.models.memory import (
    OperationalMemoryChunk,
    OperationalMemorySourceType,
)
from core.models.incident import Incident, IncidentStatus, IncidentEvent
from core.models.task import Task, TaskStatus
from core.models.campus_graph import Asset

logger = logging.getLogger("paraxis.core.memory")

PARAXIS_EMBEDDING_DIMENSION = 768


def compute_content_hash(text: str) -> str:
    """Computes deterministic SHA-256 hash of normalized canonical text."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


def generate_canonical_incident_text(incident: Incident) -> Tuple[str, str, Dict[str, Any]]:
    """
    Constructs a high-signal canonical operational memory document for a resolved incident.
    Excludes low-signal noise while synthesizing identity, context, timeline, and resolution.
    """
    title = f"Incident: {incident.title} [{incident.category}]"
    lines = [
        f"INCIDENT IDENTIFIER: {incident.id}",
        f"TITLE: {incident.title}",
        f"CATEGORY: {incident.category}",
        f"PRIORITY: {incident.priority}",
        f"STATUS: {incident.status}",
    ]

    loc_parts = []
    if incident.building:
        loc_parts.append(f"Building {incident.building.name}")
    if incident.floor:
        floor_lbl = incident.floor.label or f"Level {incident.floor.floor_number}"
        loc_parts.append(f"Floor {floor_lbl}")
    if incident.room:
        loc_parts.append(f"Room {incident.room.room_number}")
    if loc_parts:
        lines.append(f"LOCATION: {', '.join(loc_parts)}")

    if incident.asset:
        lines.append(
            f"ASSET: {incident.asset.name} (Tag: {incident.asset.asset_tag}, Category: {incident.asset.category})"
        )

    lines.append(f"INITIAL REPORT: {incident.description.strip()}")

    # Filtered timeline: only include substantive status changes and diagnostic notes
    events = IncidentEvent.all_objects.filter(incident=incident).order_by("created_at")
    timeline_entries = []
    for ev in events:
        ts = ev.created_at.strftime("%Y-%m-%d %H:%M")
        desc = getattr(ev, "description", None) or getattr(ev, "notes", "")
        if desc and desc.strip():
            timeline_entries.append(f"[{ts}] {ev.event_type}: {desc.strip()}")
        elif ev.event_type in ["ASSIGNED", "IN_PROGRESS", "ESCALATED", "RESOLVED", "VERIFIED"]:
            to_st = (ev.metadata or {}).get("to_status") or getattr(ev, "to_status", None) or ev.event_type
            timeline_entries.append(f"[{ts}] State transition to {to_st}")

    if timeline_entries:
        lines.append("DIAGNOSTIC TIMELINE:")
        for entry in timeline_entries:
            lines.append(f"  - {entry}")

    if incident.resolution_notes and incident.resolution_notes.strip():
        lines.append(f"RESOLUTION: {incident.resolution_notes.strip()}")
    if incident.resolved_at:
        lines.append(f"RESOLVED AT: {incident.resolved_at.isoformat()}")

    canonical_text = "\n".join(lines)
    metadata = {
        "incident_id": str(incident.id),
        "category": incident.category,
        "priority": incident.priority,
        "status": incident.status,
        "building_id": str(incident.building_id) if incident.building_id else None,
        "room_id": str(incident.room_id) if incident.room_id else None,
        "asset_id": str(incident.asset_id) if incident.asset_id else None,
        "resolved_at": incident.resolved_at.isoformat() if incident.resolved_at else None,
    }

    return title, canonical_text, metadata


def generate_canonical_task_text(task: Task) -> Tuple[str, str, Dict[str, Any]]:
    """Constructs canonical operational memory for a completed operational task."""
    title = f"Task: {task.title} [{task.priority}]"
    lines = [
        f"TASK IDENTIFIER: {task.id}",
        f"TITLE: {task.title}",
        f"DESCRIPTION: {task.description}",
        f"PRIORITY: {task.priority}",
        f"STATUS: {task.status}",
    ]
    if task.assigned_department:
        lines.append(f"DEPARTMENT: {task.assigned_department.name}")
    if task.assigned_user:
        lines.append(f"TECHNICIAN: {task.assigned_user.get_full_name() or task.assigned_user.email}")
    if task.started_at:
        lines.append(f"STARTED AT: {task.started_at.isoformat()}")
    if task.completed_at:
        lines.append(f"COMPLETED AT: {task.completed_at.isoformat()}")

    canonical_text = "\n".join(lines)
    metadata = {
        "task_id": str(task.id),
        "incident_id": str(task.incident_id),
        "status": task.status,
        "department_id": str(task.assigned_department_id) if task.assigned_department_id else None,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
    return title, canonical_text, metadata


def generate_canonical_asset_text(asset: Asset) -> Tuple[str, str, Dict[str, Any]]:
    """Constructs canonical operational memory for a campus infrastructure asset."""
    title = f"Asset Specification: {asset.name} ({asset.asset_tag})"
    lines = [
        f"ASSET IDENTIFIER: {asset.id}",
        f"NAME: {asset.name}",
        f"TAG: {asset.asset_tag}",
        f"CATEGORY: {asset.category}",
        f"STATUS: {asset.status}",
    ]
    if asset.building:
        lines.append(f"BUILDING: {asset.building.name}")
    if asset.room:
        lines.append(f"ROOM: {asset.room.room_number}")
    if asset.serial_number:
        lines.append(f"SERIAL NUMBER: {asset.serial_number}")
    if asset.metadata:
        lines.append(f"SPECIFICATIONS & METADATA: {asset.metadata}")

    canonical_text = "\n".join(lines)
    metadata = {
        "asset_id": str(asset.id),
        "tag": asset.asset_tag,
        "category": asset.category,
        "status": asset.status,
    }
    return title, canonical_text, metadata


@transaction.atomic
def index_memory_chunk(
    organization_id: uuid.UUID,
    campus_id: uuid.UUID,
    source_type: str,
    source_id: str,
    title: str,
    canonical_text: str,
    embedding: List[float],
    embedding_provider: str = "mock",
    embedding_model: str = "mock-paraxis-v1",
    category: str = "",
    building=None,
    room=None,
    asset=None,
    metadata_payload: Optional[Dict[str, Any]] = None,
    source_updated_at=None,
) -> Tuple[OperationalMemoryChunk, bool]:
    """
    Persists or updates an OperationalMemoryChunk with strict idempotency and change detection.

    Behavior:
    - Same source + same content hash: NO-OP, returns (existing_chunk, False)
    - Same source + changed content hash: increments source_version, updates embedding and metadata, returns (chunk, True)
    - New source: creates chunk with source_version=1, returns (chunk, True)

    Strictly validates embedding dimension == 768.
    """
    if not isinstance(embedding, list) or len(embedding) != PARAXIS_EMBEDDING_DIMENSION:
        actual_dim = len(embedding) if isinstance(embedding, list) else type(embedding).__name__
        raise ValidationError(
            f"Embedding dimension {actual_dim} does not match canonical {PARAXIS_EMBEDDING_DIMENSION}"
        )

    content_hash = compute_content_hash(canonical_text)
    source_updated_at = source_updated_at or timezone.now()
    metadata_payload = metadata_payload or {}

    existing_chunk = OperationalMemoryChunk.all_objects.filter(
        organization_id=organization_id,
        campus_id=campus_id,
        source_type=source_type,
        source_id=source_id,
    ).first()

    if existing_chunk:
        if existing_chunk.content_hash == content_hash:
            # NO-OP: Content has not changed
            logger.debug(
                f"Memory chunk unchanged for {source_type}:{source_id} (hash={content_hash[:8]}). Skipping."
            )
            return existing_chunk, False

        # Changed content: update in place and increment version counter
        existing_chunk.title = title
        existing_chunk.canonical_text = canonical_text
        existing_chunk.content_hash = content_hash
        existing_chunk.embedding = embedding
        existing_chunk.embedding_provider = embedding_provider
        existing_chunk.embedding_model = embedding_model
        existing_chunk.category = category
        existing_chunk.building = building
        existing_chunk.room = room
        existing_chunk.asset = asset
        existing_chunk.metadata_payload = metadata_payload
        existing_chunk.source_updated_at = source_updated_at
        existing_chunk.source_version += 1
        existing_chunk.save()
        logger.info(
            f"Updated memory chunk for {source_type}:{source_id} to v{existing_chunk.source_version}."
        )
        return existing_chunk, True

    # New chunk creation
    chunk = OperationalMemoryChunk.objects.create(
        organization_id=organization_id,
        campus_id=campus_id,
        source_type=source_type,
        source_id=source_id,
        source_version=1,
        source_updated_at=source_updated_at,
        title=title,
        canonical_text=canonical_text,
        content_hash=content_hash,
        embedding=embedding,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        category=category,
        building=building,
        room=room,
        asset=asset,
        metadata_payload=metadata_payload,
    )
    logger.info(f"Indexed new memory chunk for {source_type}:{source_id} (v1).")
    return chunk, True


def search_operational_memory(
    organization_id: uuid.UUID,
    campus_id: uuid.UUID,
    query_embedding: List[float],
    limit: int = 5,
    threshold: Optional[float] = None,
    source_type: Optional[str] = None,
    category: Optional[str] = None,
    building_id: Optional[uuid.UUID] = None,
    room_id: Optional[uuid.UUID] = None,
    asset_id: Optional[uuid.UUID] = None,
) -> List[Dict[str, Any]]:
    """
    Executes pgvector cosine similarity search over OperationalMemoryChunk.
    Guarantees strict tenant/campus isolation.
    Validates query vector == 768 dimensions.
    Returns structured results with similarity scores (1.0 - CosineDistance).
    """
    if not isinstance(query_embedding, list) or len(query_embedding) != PARAXIS_EMBEDDING_DIMENSION:
        actual_dim = len(query_embedding) if isinstance(query_embedding, list) else type(query_embedding).__name__
        raise ValidationError(
            f"Query embedding dimension {actual_dim} does not match canonical {PARAXIS_EMBEDDING_DIMENSION}"
        )

    # Scoped QuerySet: strictly enforce tenant & campus isolation
    qs = OperationalMemoryChunk.all_objects.filter(
        organization_id=organization_id,
        campus_id=campus_id,
    )

    if source_type:
        qs = qs.filter(source_type=source_type)
    if category:
        qs = qs.filter(category=category)
    if building_id:
        qs = qs.filter(building_id=building_id)
    if room_id:
        qs = qs.filter(room_id=room_id)
    if asset_id:
        qs = qs.filter(asset_id=asset_id)

    # Perform HNSW pgvector cosine distance calculation
    qs = qs.annotate(distance=CosineDistance("embedding", query_embedding)).order_by("distance")

    results = []
    safe_limit = max(1, min(50, limit))

    for chunk in qs[:safe_limit]:
        sim_score = max(0.0, min(1.0, 1.0 - float(chunk.distance)))

        if threshold is not None and sim_score < threshold:
            continue

        results.append({
            "id": str(chunk.id),
            "source_type": chunk.source_type,
            "source_id": chunk.source_id,
            "source_version": chunk.source_version,
            "source_updated_at": chunk.source_updated_at.isoformat(),
            "title": chunk.title,
            "canonical_text": chunk.canonical_text,
            "category": chunk.category,
            "building_id": str(chunk.building_id) if chunk.building_id else None,
            "room_id": str(chunk.room_id) if chunk.room_id else None,
            "asset_id": str(chunk.asset_id) if chunk.asset_id else None,
            "metadata_payload": chunk.metadata_payload,
            "similarity_score": round(sim_score, 4),
        })

    return results
