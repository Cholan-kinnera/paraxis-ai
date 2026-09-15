"""
DRF Serializers for SLA and SLATracking models.
"""
from rest_framework import serializers
from core.models.sla import SLA, SLATracking


class SLASerializer(serializers.ModelSerializer):
    class Meta:
        model = SLA
        fields = [
            "id",
            "organization",
            "campus",
            "name",
            "description",
            "priority",
            "task_type",
            "category",
            "response_target",
            "resolution_target",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SLATrackingSerializer(serializers.ModelSerializer):
    sla_name = serializers.CharField(source="sla.name", read_only=True)

    class Meta:
        model = SLATracking
        fields = [
            "id",
            "task",
            "sla",
            "sla_name",
            "started_at",
            "response_due_at",
            "resolution_due_at",
            "response_completed_at",
            "resolution_completed_at",
            "response_breached_at",
            "resolution_breached_at",
            "state",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields
