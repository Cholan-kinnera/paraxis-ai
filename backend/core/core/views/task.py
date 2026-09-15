"""
API views for Task & Dispatch Management (Phase 4).
Enforces tenant isolation, lifecycle state-machine validations, and immutable timeline auditing.
"""
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError as DRFValidationError
from django.core.exceptions import ValidationError as DjangoValidationError

from core.models.task import Task, TaskEvent
from core.models.incident import Incident
from core.serializers.task import (
    TaskSerializer,
    TaskCreateSerializer,
    TaskUpdateSerializer,
    TaskAssignSerializer,
    TaskActionSerializer,
    TaskEventSerializer,
)
from core.permissions.rbac import IsAuthenticatedUser
from core.services.task_dispatch import (
    create_task_from_incident,
    assign_task,
    start_task,
    complete_task,
    cancel_task,
)
from core.services.sla import check_and_record_breaches


def get_scoped_task_queryset(request, select_related=True):
    """
    Returns a Task queryset strictly scoped to the caller's tenant.
    Filters out soft-deleted records.
    Fails closed if the caller lacks organization context.
    """
    user = request.user
    if not user or not user.is_authenticated or not user.is_active:
        return Task.all_objects.none()

    if user.is_superuser:
        qs = Task.all_objects.filter(deleted_at__isnull=True)
    elif user.organization_id:
        qs = Task.all_objects.filter(
            organization_id=user.organization_id,
            deleted_at__isnull=True,
        )
        campus_id = getattr(request, "active_campus_id", None) or user.primary_campus_id
        if campus_id:
            qs = qs.filter(campus_id=campus_id)
        else:
            return Task.all_objects.none()
    else:
        return Task.all_objects.none()

    # RBAC Scoping:
    # Full view: Super Admin, Campus Admin, task:manage_all
    # Technician: assigned_user == user
    # Student: incident__reporter == user
    has_full_view = (
        user.is_superuser
        or user.has_role("SUPER_ADMIN")
        or user.has_role("CAMPUS_ADMIN")
        or user.has_perm_code("task:manage_all")
    )
    if not has_full_view:
        if user.has_perm_code("task:view_assigned") or user.has_role("TECHNICIAN"):
            qs = qs.filter(assigned_user_id=user.id)
        elif user.has_perm_code("incident:view_self") or user.has_role("STUDENT"):
            qs = qs.filter(incident__reporter_id=user.id)
        elif user.has_perm_code("task:read"):
            pass  # Campus-wide read for observers/dispatchers
        else:
            return Task.all_objects.none()

    if select_related:
        qs = qs.select_related(
            "incident",
            "assigned_user",
            "assigned_department",
            "created_by",
            "sla",
            "sla_tracking",
        )
    return qs


class TaskListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/tasks/ (List operational tasks in caller's campus)
    POST /api/v1/tasks/ (Dispatch a new task from an incident)
    """
    permission_classes = [IsAuthenticatedUser]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return TaskCreateSerializer
        return TaskSerializer

    def get_queryset(self):
        qs = get_scoped_task_queryset(self.request)

        # Periodic SLA evaluation on read
        for task in qs[:20]:
            try:
                check_and_record_breaches(task)
            except Exception:
                pass

        params = self.request.query_params
        incident_param = params.get("incident")
        if incident_param:
            qs = qs.filter(incident_id=incident_param)

        status_param = params.get("status")
        if status_param:
            qs = qs.filter(status=status_param)

        priority_param = params.get("priority")
        if priority_param:
            qs = qs.filter(priority=priority_param)

        task_type_param = params.get("task_type")
        if task_type_param:
            qs = qs.filter(task_type=task_type_param)

        assigned_user_param = params.get("assigned_user")
        if assigned_user_param:
            qs = qs.filter(assigned_user_id=assigned_user_param)

        assigned_dept_param = params.get("assigned_department")
        if assigned_dept_param:
            qs = qs.filter(assigned_department_id=assigned_dept_param)

        return qs

    def create(self, request, *args, **kwargs):
        user = request.user
        is_authorized = (
            user.is_superuser
            or user.has_role("SUPER_ADMIN")
            or user.has_role("CAMPUS_ADMIN")
            or user.has_perm_code("task:create")
            or user.has_perm_code("task:manage_all")
        )
        if not is_authorized:
            raise PermissionDenied("You do not have permission to create operational tasks.")

        serializer = TaskCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        incident = data["incident"]

        # Enforce that incident belongs to user's scoped campus
        if not user.is_superuser:
            campus_id = getattr(request, "active_campus_id", None) or user.primary_campus_id
            if incident.organization_id != user.organization_id or incident.campus_id != campus_id:
                raise PermissionDenied("Cannot create task for an incident outside your authorized campus.")

        try:
            task = create_task_from_incident(
                incident=incident,
                title=data["title"],
                description=data.get("description", ""),
                task_type=data.get("task_type"),
                priority=data.get("priority"),
                assigned_user=data.get("assigned_user"),
                assigned_department=data.get("assigned_department"),
                created_by=user,
                actor=user,
                metadata=data.get("metadata"),
                request=request,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

        return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)


class TaskDetailView(generics.RetrieveUpdateAPIView):
    """
    GET   /api/v1/tasks/<uuid:pk>/ (Retrieve task details with SLA tracking)
    PATCH /api/v1/tasks/<uuid:pk>/ (Update non-lifecycle fields only)
    """
    permission_classes = [IsAuthenticatedUser]

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return TaskUpdateSerializer
        return TaskSerializer

    def get_object(self):
        qs = get_scoped_task_queryset(self.request)
        try:
            task = qs.get(pk=self.kwargs["pk"])
            check_and_record_breaches(task)
            return task
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

    def update(self, request, *args, **kwargs):
        task = self.get_object()
        user = request.user
        is_authorized = (
            user.is_superuser
            or user.has_role("SUPER_ADMIN")
            or user.has_role("CAMPUS_ADMIN")
            or user.has_perm_code("task:update")
            or user.has_perm_code("task:manage_all")
        )
        if not is_authorized:
            raise PermissionDenied("You do not have permission to modify task details.")

        serializer = TaskUpdateSerializer(task, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(TaskSerializer(task).data, status=status.HTTP_200_OK)


class TaskEventsTimelineView(generics.ListAPIView):
    """
    GET /api/v1/tasks/<uuid:pk>/events/ (Retrieve immutable audit timeline)
    """
    serializer_class = TaskEventSerializer
    permission_classes = [IsAuthenticatedUser]

    def get_queryset(self):
        task_qs = get_scoped_task_queryset(self.request, select_related=False)
        if not task_qs.filter(pk=self.kwargs["pk"]).exists():
            raise NotFound("Task not found.")

        return TaskEvent.all_objects.filter(task_id=self.kwargs["pk"]).select_related("actor")


class TaskAssignView(APIView):
    """
    POST /api/v1/tasks/<uuid:pk>/assign/
    Assign or reassign an operational task.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request, pk):
        user = request.user
        is_authorized = (
            user.is_superuser
            or user.has_role("SUPER_ADMIN")
            or user.has_role("CAMPUS_ADMIN")
            or user.has_perm_code("task:reassign")
            or user.has_perm_code("task:manage_all")
        )
        if not is_authorized:
            raise PermissionDenied("You do not have permission to assign tasks.")

        task_qs = get_scoped_task_queryset(request)
        try:
            task = task_qs.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

        serializer = TaskAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_task = assign_task(
                task=task,
                assigned_user=serializer.validated_data.get("assigned_user"),
                assigned_department=serializer.validated_data.get("assigned_department"),
                actor=user,
                request=request,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

        return Response(TaskSerializer(updated_task).data, status=status.HTTP_200_OK)


class TaskStartView(APIView):
    """
    POST /api/v1/tasks/<uuid:pk>/start/
    Transition task to IN_PROGRESS and start work clock.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request, pk):
        task_qs = get_scoped_task_queryset(request)
        try:
            task = task_qs.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

        user = request.user
        is_authorized = (
            user.is_superuser
            or user.has_role("SUPER_ADMIN")
            or user.has_role("CAMPUS_ADMIN")
            or user.has_perm_code("task:start")
            or user.has_perm_code("task:manage_all")
            or task.assigned_user_id == user.id
        )
        if not is_authorized:
            raise PermissionDenied("You do not have permission to start this task.")

        try:
            updated_task = start_task(task=task, actor=user, request=request)
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

        return Response(TaskSerializer(updated_task).data, status=status.HTTP_200_OK)


class TaskCompleteView(APIView):
    """
    POST /api/v1/tasks/<uuid:pk>/complete/
    Transition task to COMPLETED and stop resolution SLA clock.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request, pk):
        task_qs = get_scoped_task_queryset(request)
        try:
            task = task_qs.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

        user = request.user
        is_authorized = (
            user.is_superuser
            or user.has_role("SUPER_ADMIN")
            or user.has_role("CAMPUS_ADMIN")
            or user.has_perm_code("task:complete")
            or user.has_perm_code("task:manage_all")
            or task.assigned_user_id == user.id
        )
        if not is_authorized:
            raise PermissionDenied("You do not have permission to complete this task.")

        serializer = TaskActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_task = complete_task(
                task=task,
                resolution_notes=serializer.validated_data.get("notes", ""),
                actor=user,
                request=request,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

        return Response(TaskSerializer(updated_task).data, status=status.HTTP_200_OK)


class TaskCancelView(APIView):
    """
    POST /api/v1/tasks/<uuid:pk>/cancel/
    Transition task to CANCELLED terminal state.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request, pk):
        task_qs = get_scoped_task_queryset(request)
        try:
            task = task_qs.get(pk=pk)
        except Task.DoesNotExist:
            raise NotFound("Task not found.")

        user = request.user
        is_authorized = (
            user.is_superuser
            or user.has_role("SUPER_ADMIN")
            or user.has_role("CAMPUS_ADMIN")
            or user.has_perm_code("task:cancel")
            or user.has_perm_code("task:manage_all")
        )
        if not is_authorized:
            raise PermissionDenied("You do not have permission to cancel this task.")

        serializer = TaskActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            updated_task = cancel_task(
                task=task,
                reason=serializer.validated_data.get("reason", ""),
                actor=user,
                request=request,
            )
        except DjangoValidationError as exc:
            raise DRFValidationError(exc.message_dict if hasattr(exc, "message_dict") else exc.messages)

        return Response(TaskSerializer(updated_task).data, status=status.HTTP_200_OK)
