"""
Idempotent development seed command for Paraxis AI Core Platform.
Populates standard organization, campuses, system roles, permissions, and test users.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models.organization import Organization, Campus, OrganizationStatus, CampusStatus
from core.models.access import Role, Permission
from core.models.user import User
from core.services.audit import log_audit_event

DEV_PASSWORD = "DevPassword123!"

STANDARD_PERMISSIONS = [
    # Incidents
    ("incident:create", "Create incident report", "incident"),
    ("incident:view_self", "View incidents submitted by self", "incident"),
    ("incident:confirm_resolution", "Confirm incident resolution", "incident"),
    ("incident:create_priority", "Create priority incident report", "incident"),
    ("incident:manage_all", "Manage all campus incidents", "incident"),
    ("incident:escalate", "Escalate incident priority", "incident"),
    # Tasks
    ("task:view_assigned", "View assigned tasks", "task"),
    ("task:acknowledge", "Acknowledge task assignment", "task"),
    ("task:start", "Start task work", "task"),
    ("task:complete", "Complete task work", "task"),
    ("task:reassign", "Reassign task to another technician", "task"),
    # Assets & Facilities
    ("asset:view", "View campus assets", "facility"),
    ("hostel:view_queue", "View hostel maintenance queue", "facility"),
    ("mess:view_forecast", "View mess meal forecast", "facility"),
    # Attendance
    ("attendance:view_self", "View personal attendance", "academic"),
    ("attendance:mark_session", "Mark session attendance", "academic"),
    ("attendance:view_roster", "View student roster", "academic"),
    ("attendance:view_absentees", "View absent student list", "academic"),
    # Safety
    ("safety:view_confidential", "View confidential safety cases", "safety"),
    ("safety:investigate", "Conduct safety investigation", "safety"),
    ("notification:emergency_broadcast", "Issue campus emergency broadcast", "safety"),
    # Administration & Governance
    ("approval:decide", "Approve or reject operational proposals", "governance"),
    ("policy:manage", "Manage campus deterministic policies", "governance"),
    ("audit:view", "View campus audit trails", "governance"),
    ("tenant:provision", "Provision new organizations", "admin"),
    ("campus:manage", "Manage and provision campuses", "admin"),
    ("system:configure", "Configure system-wide parameters", "admin"),
    ("audit:export_all", "Export all organizational audit logs", "admin"),
]

ROLE_PERMISSIONS_MAP = {
    "STUDENT": [
        "incident:create",
        "incident:view_self",
        "incident:confirm_resolution",
        "attendance:view_self",
    ],
    "FACULTY": [
        "incident:create",
        "incident:create_priority",
        "attendance:mark_session",
        "attendance:view_roster",
    ],
    "TECHNICIAN": [
        "task:view_assigned",
        "task:acknowledge",
        "task:start",
        "task:complete",
        "asset:view",
    ],
    "WARDEN": [
        "hostel:view_queue",
        "incident:escalate",
        "mess:view_forecast",
        "attendance:view_absentees",
    ],
    "SAFETY_OFFICER": [
        "safety:view_confidential",
        "safety:investigate",
        "notification:emergency_broadcast",
    ],
    "CAMPUS_ADMIN": [
        "incident:manage_all",
        "task:reassign",
        "approval:decide",
        "policy:manage",
        "audit:view",
        "asset:view",
    ],
    "SUPER_ADMIN": [
        "tenant:provision",
        "campus:manage",
        "system:configure",
        "audit:export_all",
        "incident:manage_all",
        "approval:decide",
        "audit:view",
    ],
}


class Command(BaseCommand):
    help = "Idempotently seed development data for Paraxis AI"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🌱 Starting development data seed..."))

        # 1. Organization
        org, org_created = Organization.objects.get_or_create(
            slug="apex-university",
            defaults={
                "name": "Apex University System",
                "status": OrganizationStatus.ACTIVE,
            },
        )
        self.stdout.write(f"  • Organization: {org.name} ({'created' if org_created else 'exists'})")

        # 2. Campuses
        eng_campus, eng_created = Campus.objects.get_or_create(
            organization=org,
            code="ENG",
            defaults={
                "name": "Engineering Campus",
                "timezone": "UTC",
                "status": CampusStatus.ACTIVE,
                "address": {"city": "Tech City", "state": "State", "country": "India"},
            },
        )
        self.stdout.write(f"  • Campus: {eng_campus.name} ({'created' if eng_created else 'exists'})")

        med_campus, med_created = Campus.objects.get_or_create(
            organization=org,
            code="MED",
            defaults={
                "name": "Medical Campus",
                "timezone": "UTC",
                "status": CampusStatus.ACTIVE,
                "address": {"city": "Health City", "state": "State", "country": "India"},
            },
        )
        self.stdout.write(f"  • Campus: {med_campus.name} ({'created' if med_created else 'exists'})")

        # 3. Permissions
        perm_objs = {}
        for codename, name, module in STANDARD_PERMISSIONS:
            perm, _ = Permission.objects.get_or_create(
                codename=codename,
                defaults={"name": name, "module": module},
            )
            perm_objs[codename] = perm
        self.stdout.write(f"  • Permissions: {len(perm_objs)} standard capabilities initialized.")

        # 4. System Roles
        role_objs = {}
        for role_name, perms in ROLE_PERMISSIONS_MAP.items():
            role, _ = Role.objects.get_or_create(
                name=role_name,
                is_system_role=True,
                defaults={
                    "description": f"Standard system role: {role_name}",
                    "organization": None,
                },
            )
            # Bind permissions
            role_perms = [perm_objs[p] for p in perms if p in perm_objs]
            role.permissions.set(role_perms)
            role_objs[role_name] = role
        self.stdout.write(f"  • Roles: {len(role_objs)} standard system roles initialized.")

        # 5. Development Users
        dev_users_data = [
            {
                "email": "admin@apex.edu",
                "full_name": "Apex System Administrator",
                "roles": ["SUPER_ADMIN"],
                "is_staff": True,
                "is_superuser": True,
                "campus": None,
            },
            {
                "email": "campus.admin@apex.edu",
                "full_name": "Engineering Campus Administrator",
                "roles": ["CAMPUS_ADMIN"],
                "is_staff": False,
                "is_superuser": False,
                "campus": eng_campus,
            },
            {
                "email": "faculty@apex.edu",
                "full_name": "Prof. Arvind Sharma",
                "roles": ["FACULTY"],
                "is_staff": False,
                "is_superuser": False,
                "campus": eng_campus,
            },
            {
                "email": "student.eng@apex.edu",
                "full_name": "Aarav Patel",
                "roles": ["STUDENT"],
                "is_staff": False,
                "is_superuser": False,
                "campus": eng_campus,
            },
            {
                "email": "student.med@apex.edu",
                "full_name": "Diya Sen",
                "roles": ["STUDENT"],
                "is_staff": False,
                "is_superuser": False,
                "campus": med_campus,
            },
            {
                "email": "technician@apex.edu",
                "full_name": "Ramesh Kumar",
                "roles": ["TECHNICIAN"],
                "is_staff": False,
                "is_superuser": False,
                "campus": eng_campus,
            },
            {
                "email": "safety@apex.edu",
                "full_name": "Vikram Rathore",
                "roles": ["SAFETY_OFFICER"],
                "is_staff": False,
                "is_superuser": False,
                "campus": eng_campus,
            },
        ]

        for u_data in dev_users_data:
            user = User.objects.filter(organization=org, email=u_data["email"]).first()
            if not user:
                user = User.objects.create_user(
                    email=u_data["email"],
                    full_name=u_data["full_name"],
                    password=DEV_PASSWORD,
                    organization=org,
                    primary_campus=u_data["campus"],
                    is_staff=u_data["is_staff"],
                    is_superuser=u_data["is_superuser"],
                )
                self.stdout.write(f"  • User created: {user.email} (password: {DEV_PASSWORD})")
            else:
                user.full_name = u_data["full_name"]
                user.primary_campus = u_data["campus"]
                user.is_staff = u_data["is_staff"]
                user.is_superuser = u_data["is_superuser"]
                user.set_password(DEV_PASSWORD)
                user.save()
                self.stdout.write(f"  • User updated: {user.email}")

            # Assign roles
            assigned_roles = [role_objs[r] for r in u_data["roles"] if r in role_objs]
            user.roles.set(assigned_roles)

        log_audit_event(
            action="system.seed_dev_data",
            entity_type="System",
            entity_id="development_seed",
            actor=None,
            actor_type="SYSTEM",
            organization=org,
            post_state={"status": "complete", "users_seeded": len(dev_users_data)},
        )

        self.stdout.write(self.style.SUCCESS("✅ Development seed data successfully provisioned!"))
