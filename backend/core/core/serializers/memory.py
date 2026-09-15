"""
Serializers for Paraxis AI Operational Memory & Insights.
Enforces 768-dimensional vector validation, tenant isolation, and strict data contracts.
Adheres to ADR-002, ADR-003, and Phase 6 Architecture Plan v2.
"""
from rest_framework import serializers
from core.models.memory import (
    OperationalMemoryChunk,
    OperationalMemorySourceType,
    OperationalInsight,
    OperationalInsightType,
    OperationalInsightStatus,
    OperationalInsightIncidentEvidence,
)

PARAXIS_EMBEDDING_DIMENSION = 768


class OperationalMemorySearchSerializer(serializers.Serializer):
    """Input contract for POST /api/v1/memory/search/."""
    query_embedding = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
        help_text="768-dimensional float embedding vector",
    )
    limit = serializers.IntegerField(
        default=5,
        min_value=1,
        max_value=50,
        required=False,
        help_text="Maximum number of nearest neighbors to return",
    )
    threshold = serializers.FloatField(
        required=False,
        min_value=0.0,
        max_value=1.0,
        allow_null=True,
        help_text="Minimum cosine similarity score threshold (0.0 - 1.0)",
    )
    source_type = serializers.ChoiceField(
        choices=OperationalMemorySourceType.choices,
        required=False,
        allow_null=True,
    )
    category = serializers.CharField(required=False, allow_blank=True, max_length=50)
    building_id = serializers.UUIDField(required=False, allow_null=True)
    room_id = serializers.UUIDField(required=False, allow_null=True)
    asset_id = serializers.UUIDField(required=False, allow_null=True)

    def validate_query_embedding(self, value):
        if len(value) != PARAXIS_EMBEDDING_DIMENSION:
            raise serializers.ValidationError(
                f"Query embedding dimension {len(value)} is invalid; strictly expected {PARAXIS_EMBEDDING_DIMENSION} dimensions."
            )
        return value


class OperationalMemorySearchResultSerializer(serializers.Serializer):
    """Output contract for individual memory search result."""
    id = serializers.UUIDField()
    source_type = serializers.CharField()
    source_id = serializers.CharField()
    source_version = serializers.IntegerField()
    source_updated_at = serializers.CharField()
    title = serializers.CharField()
    canonical_text = serializers.CharField()
    category = serializers.CharField(allow_blank=True)
    building_id = serializers.UUIDField(allow_null=True)
    room_id = serializers.UUIDField(allow_null=True)
    asset_id = serializers.UUIDField(allow_null=True)
    metadata_payload = serializers.DictField()
    similarity_score = serializers.FloatField()


class OperationalInsightEvidenceSerializer(serializers.ModelSerializer):
    """Evidence link serializer."""
    incident_id = serializers.UUIDField(source="incident.id")
    incident_title = serializers.CharField(source="incident.title", read_only=True)
    incident_category = serializers.CharField(source="incident.category", read_only=True)

    class Meta:
        model = OperationalInsightIncidentEvidence
        fields = [
            "id",
            "incident_id",
            "incident_title",
            "incident_category",
            "relevance_score",
            "evidence_notes",
            "created_at",
        ]


class OperationalInsightSerializer(serializers.ModelSerializer):
    """Output serializer for OperationalInsight with relational evidence links."""
    evidence = OperationalInsightEvidenceSerializer(source="evidence_links", many=True, read_only=True)
    target_asset_name = serializers.CharField(source="target_asset.name", read_only=True, allow_null=True)
    target_room_number = serializers.CharField(source="target_room.room_number", read_only=True, allow_null=True)
    target_building_name = serializers.CharField(source="target_building.name", read_only=True, allow_null=True)

    class Meta:
        model = OperationalInsight
        fields = [
            "id",
            "insight_type",
            "status",
            "confidence_score",
            "incident_count",
            "fact_summary",
            "inference_analysis",
            "recommendation",
            "target_asset",
            "target_asset_name",
            "target_room",
            "target_room_number",
            "target_building",
            "target_building_name",
            "window_start",
            "window_end",
            "created_at",
            "updated_at",
            "evidence",
        ]


class OperationalMemoryIndexSerializer(serializers.Serializer):
    """Input contract for POST /api/v1/memory/index/."""
    source_type = serializers.ChoiceField(choices=OperationalMemorySourceType.choices)
    source_id = serializers.CharField(max_length=64)
    title = serializers.CharField(max_length=255)
    canonical_text = serializers.CharField()
    embedding = serializers.ListField(
        child=serializers.FloatField(),
        allow_empty=False,
    )
    embedding_provider = serializers.CharField(default="mock", max_length=50)
    embedding_model = serializers.CharField(default="mock-paraxis-v1", max_length=100)
    category = serializers.CharField(required=False, allow_blank=True, default="", max_length=50)
    building_id = serializers.UUIDField(required=False, allow_null=True)
    room_id = serializers.UUIDField(required=False, allow_null=True)
    asset_id = serializers.UUIDField(required=False, allow_null=True)
    metadata_payload = serializers.DictField(required=False, default=dict)

    def validate_embedding(self, value):
        if len(value) != PARAXIS_EMBEDDING_DIMENSION:
            raise serializers.ValidationError(
                f"Embedding vector dimension {len(value)} is invalid; strictly expected {PARAXIS_EMBEDDING_DIMENSION} dimensions."
            )
        return value
