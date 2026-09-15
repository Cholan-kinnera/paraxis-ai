"""
DRF Serializers for Task and TaskEvent models.
Enforces security invariants and ensures domain fields cannot be bypassed via PATCH.
"""
from rest_framework import serializers
from core.models.task import Task, TaskEvent, TaskStatus, TaskType
from core.models.incident import Incident, IncidentPriority
from core.models.user import User
from core.models.campus_graph import Department
from core.serializers.sla import SLATrackingSerializer


class TaskEventSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True)

    class Meta:
        model = TaskEvent
        fields = [
            "id",
            "task",
            "event_type",
            "actor",
            "actor_email",
            "actor_type",
            "from_status",
            "to_status",
            "message",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields


class TaskSerializer(serializers.ModelSerializer):
    incident_title = serializers.CharField(source="incident.title", read_only=True)
    assigned_user_name = serializers.SerializerMethodField()
    assigned_department_name = serializers.CharField(source="assigned_department.name", read_only=True)
    sla_tracking = SLATrackingSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            "id",
            "organization",
            "campus",
            "incident",
            "incident_title",
            "title",
            "description",
            "status",
            "priority",
            "task_type",
            "assigned_user",
            "assigned_user_name",
            "assigned_department",
            "assigned_department_name",
            "created_by",
            "sla",
            "sla_tracking",
            "due_at",
            "started_at",
            "completed_at",
            "cancelled_at",
            "metadata",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "organization",
            "campus",
            "status",
            "due_at",
            "started_at",
            "completed_at",
            "cancelled_at",
            "created_at",
            "updated_at",
        ]

    def get_assigned_user_name(self, obj):
        if obj.assigned_user:
            return obj.assigned_user.full_name or obj.assigned_user.email
        return None


class TaskCreateSerializer(serializers.Serializer):
    incident = serializers.PrimaryKeyRelatedField(
        queryset=Incident.all_objects.all(),
        required=False,
    )
    incident_id = serializers.PrimaryKeyRelatedField(
        queryset=Incident.all_objects.all(),
        source="incident",
        required=False,
    )
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    task_type = serializers.ChoiceField(choices=TaskType.choices, default=TaskType.OTHER)
    priority = serializers.ChoiceField(choices=IncidentPriority.choices, required=False, allow_null=True)
    assigned_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    assigned_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="assigned_user",
        required=False,
        allow_null=True,
    )
    assigned_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.all_objects.all(),
        required=False,
        allow_null=True,
    )
    assigned_department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.all_objects.all(),
        source="assigned_department",
        required=False,
        allow_null=True,
    )
    metadata = serializers.JSONField(required=False, default=dict)

    def validate(self, attrs):
        if not attrs.get("incident"):
            raise serializers.ValidationError({"incident": "Incident is required to create a task."})
        return attrs


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Constrained serializer for generic PATCH requests.
    Explicitly prohibits mutating lifecycle status, timestamps, and tenant links.
    Domain actions (assignment, start, complete, cancel) MUST use action endpoints.
    """
    class Meta:
        model = Task
        fields = [
            "title",
            "description",
            "priority",
            "task_type",
            "metadata",
        ]


class TaskAssignSerializer(serializers.Serializer):
    assigned_user = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        allow_null=True,
    )
    assigned_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True),
        source="assigned_user",
        required=False,
        allow_null=True,
    )
    assigned_department = serializers.PrimaryKeyRelatedField(
        queryset=Department.all_objects.all(),
        required=False,
        allow_null=True,
    )
    assigned_department_id = serializers.PrimaryKeyRelatedField(
        queryset=Department.all_objects.all(),
        source="assigned_department",
        required=False,
        allow_null=True,
    )

    def validate(self, attrs):
        if not attrs.get("assigned_user") and not attrs.get("assigned_department"):
            raise serializers.ValidationError("Either assigned_user or assigned_department must be specified.")
        return attrs


class TaskActionSerializer(serializers.Serializer):
    notes = serializers.CharField(required=False, allow_blank=True, default="")
    reason = serializers.CharField(required=False, allow_blank=True, default="")


class TaskEventSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source="actor.full_name", read_only=True)
    actor_email = serializers.CharField(source="actor.email", read_only=True)

    class Meta:
        model = TaskEvent
        fields = [
            "id",
            "task_id",
            "event_type",
            "actor_id",
            "actor_name",
            "actor_email",
            "actor_type",
            "from_status",
            "to_status",
            "message",
            "metadata",
            "created_at",
        ]
        read_only_fields = fields
