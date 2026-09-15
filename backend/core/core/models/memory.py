"""
Operational Memory & Institutional Knowledge models for Paraxis AI.
Owns pgvector semantic storage, canonical chunks, and deterministic insights.
Adheres to ADR-002, ADR-003, ADR-006, and Phase 6 Architecture Plan v2.
"""
import uuid
from django.db import models
from django.core.exceptions import ValidationError
from pgvector.django import VectorField, HnswIndex

from core.models.base import TenantScopedModel


class OperationalMemorySourceType(models.TextChoices):
    INCIDENT = "INCIDENT", "Resolved Incident"
    TASK = "TASK", "Completed Task"
    ASSET = "ASSET", "Campus Asset Specification"


class OperationalMemoryChunk(TenantScopedModel):
    """
    Canonical operational memory chunk with 768-dim pgvector embedding.
    Maintains strict tenant/campus scoping and 1:1 source idempotency.
    """
    campus_scoped = True

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique memory chunk identifier",
    )

    # Source Provenance
    source_type = models.CharField(
        max_length=50,
        choices=OperationalMemorySourceType.choices,
        db_index=True,
        help_text="Type of operational source",
    )
    source_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Primary key identifier of source entity in Django Core",
    )
    source_version = models.PositiveIntegerField(
        default=1,
        help_text="Monotonically increasing version counter for change detection",
    )
    source_updated_at = models.DateTimeField(
        help_text="Timestamp of source record when this memory chunk was generated",
    )

    # Canonical Content & Cryptographic Hash
    title = models.CharField(
        max_length=255,
        help_text="Brief headline for the memory chunk",
    )
    canonical_text = models.TextField(
        help_text="Normalized canonical text representation embedded into vector space",
    )
    content_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA-256 hash of canonical_text for change detection and idempotency",
    )

    # High-Dimensional Vector (Paraxis Canonical Dimension = 768)
    embedding = VectorField(
        dimensions=768,
        help_text="Dense 768-dimensional float embedding vector",
    )

    # Embedding Provenance
    embedding_provider = models.CharField(
        max_length=50,
        default="mock",
        help_text="AI Provider used to compute embedding (e.g. mock, google, openai)",
    )
    embedding_model = models.CharField(
        max_length=100,
        default="mock-paraxis-v1",
        help_text="Model name used for vectorization",
    )

    # Spatial & Domain Metadata (Enables fast hybrid SQL pre-filtering)
    category = models.CharField(
        max_length=50,
        blank=True,
        db_index=True,
        help_text="Operational domain category",
    )
    building = models.ForeignKey(
        "core.Building",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memory_chunks",
        help_text="Optional physical building anchor",
    )
    room = models.ForeignKey(
        "core.Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memory_chunks",
        help_text="Optional physical room anchor",
    )
    asset = models.ForeignKey(
        "core.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="memory_chunks",
        help_text="Optional campus infrastructure asset anchor",
    )

    # Structured Telemetry
    metadata_payload = models.JSONField(
        default=dict,
        blank=True,
        help_text="Structured operational metadata (downtime, technician, resolution milestones)",
    )

    def clean(self):
        super().clean()
        if self.building_id and self.building.campus_id != self.campus_id:
            raise ValidationError({"building": "Building belongs to a different Campus."})
        if self.room_id and self.room.campus_id != self.campus_id:
            raise ValidationError({"room": "Room belongs to a different Campus."})
        if self.asset_id and self.asset.campus_id != self.campus_id:
            raise ValidationError({"asset": "Asset belongs to a different Campus."})

    class Meta:
        db_table = "operational_memory_chunks"
        constraints = [
            models.UniqueConstraint(
                fields=["organization", "campus", "source_type", "source_id"],
                name="unique_tenant_campus_memory_source",
            )
        ]
        indexes = [
            HnswIndex(
                name="op_mem_hnsw_cosine_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            models.Index(fields=["organization", "campus", "source_type"]),
            models.Index(fields=["organization", "campus", "category"]),
            models.Index(fields=["organization", "campus", "asset"]),
        ]


class OperationalInsightType(models.TextChoices):
    RECURRING_ASSET_FAILURE = "RECURRING_ASSET_FAILURE", "Recurring Asset Failure"
    LOCATION_HOTSPOT = "LOCATION_HOTSPOT", "Location Incident Hotspot"
    CROSS_CIRCUIT_CASCADE = "CROSS_CIRCUIT_CASCADE", "Cross-Circuit Power Cascade"


class OperationalInsightStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active Concern"
    ACKNOWLEDGED = "ACKNOWLEDGED", "Acknowledged by Facility Staff"
    RESOLVED = "RESOLVED", "Remediated / Verified"


class OperationalInsight(TenantScopedModel):
    """
    Persisted institutional knowledge identifying recurring failures or anomalies.
    Maintains strict epistemological segregation: FACT vs. INFERENCE vs. RECOMMENDATION.
    """
    campus_scoped = True

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique insight identifier",
    )

    insight_type = models.CharField(
        max_length=50,
        choices=OperationalInsightType.choices,
        db_index=True,
        help_text="Classification of the operational anomaly",
    )

    # Strict Epistemological Segregation
    fact_summary = models.TextField(
        help_text="Empirical verifiable facts: timestamps, incident IDs, downtime measurements",
    )
    inference_analysis = models.TextField(
        help_text="Probabilistic deductions: pattern analysis, suspected degradation mechanisms",
    )
    recommendation = models.TextField(
        help_text="Actionable suggestions for human operational personnel",
    )

    confidence_score = models.FloatField(
        default=0.0,
        help_text="Calculated algorithmic confidence score (0.0 to 1.0)",
    )

    # Target Operational Entities
    target_asset = models.ForeignKey(
        "core.Asset",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operational_insights",
        help_text="Impacted equipment if applicable",
    )
    target_room = models.ForeignKey(
        "core.Room",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operational_insights",
        help_text="Impacted room if applicable",
    )
    target_building = models.ForeignKey(
        "core.Building",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="operational_insights",
        help_text="Impacted building if applicable",
    )

    # Temporal Window Bounds
    window_start = models.DateTimeField(
        help_text="Start timestamp of the observation window",
    )
    window_end = models.DateTimeField(
        help_text="End timestamp of the observation window",
    )
    incident_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of empirical incidents contributing to this insight",
    )

    status = models.CharField(
        max_length=32,
        choices=OperationalInsightStatus.choices,
        default=OperationalInsightStatus.ACTIVE,
        db_index=True,
        help_text="Current operational review status",
    )

    # Relational Evidence Linking
    incidents = models.ManyToManyField(
        "core.Incident",
        through="OperationalInsightIncidentEvidence",
        related_name="contributed_insights",
        help_text="Relational evidence incidents supporting this insight",
    )

    class Meta:
        db_table = "operational_insights"
        ordering = ["-created_at"]


class OperationalInsightIncidentEvidence(TenantScopedModel):
    """
    Relational link tying an OperationalInsight to its specific empirical incident evidence.
    Enforces referential integrity without untyped JSON arrays.
    """
    campus_scoped = True

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    insight = models.ForeignKey(
        OperationalInsight,
        on_delete=models.CASCADE,
        related_name="evidence_links",
        help_text="Parent operational insight",
    )
    incident = models.ForeignKey(
        "core.Incident",
        on_delete=models.CASCADE,
        related_name="insight_evidence_links",
        help_text="Empirical incident evidence record",
    )
    relevance_score = models.FloatField(
        default=1.0,
        help_text="Relative contribution weight of this incident to the insight",
    )
    evidence_notes = models.TextField(
        blank=True,
        help_text="Optional diagnostic notes linking this incident to the recurring pattern",
    )

    class Meta:
        db_table = "operational_insight_evidence"
        constraints = [
            models.UniqueConstraint(
                fields=["insight", "incident"],
                name="unique_insight_incident_evidence",
            )
        ]
