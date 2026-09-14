"""
Idempotent development seed command for Paraxis AI Core Platform.
Populates standard organization, campuses, system roles, permissions, and test users.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models.organization import Organization, Campus, OrganizationStatus, CampusStatus
from core.models.access import Role, Permission
from core.models.user import User
from core.models.campus_graph import (
    Department,
    Building,
    Floor,
    Room,
    Asset,
    DepartmentStatus,
    BuildingStatus,
    RoomType,
    RoomStatus,
    AssetCategory,
    AssetStatus,
)
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
    # Phase 2 Campus Operational Graph Permissions
    ("department:read", "View departments", "facility"),
    ("department:create", "Create department", "facility"),
    ("department:update", "Update department", "facility"),
    ("department:delete", "Delete department", "facility"),
    ("building:read", "View campus buildings", "facility"),
    ("building:create", "Create building", "facility"),
    ("building:update", "Update building", "facility"),
    ("building:delete", "Delete building", "facility"),
    ("floor:read", "View floors", "facility"),
    ("floor:create", "Create floor", "facility"),
    ("floor:update", "Update floor", "facility"),
    ("floor:delete", "Delete floor", "facility"),
    ("room:read", "View rooms", "facility"),
    ("room:create", "Create room", "facility"),
    ("room:update", "Update room", "facility"),
    ("room:delete", "Delete room", "facility"),
    ("asset:read", "View assets", "facility"),
    ("asset:create", "Create asset", "facility"),
    ("asset:update", "Update asset", "facility"),
    ("asset:delete", "Delete asset", "facility"),
]

ROLE_PERMISSIONS_MAP = {
    "STUDENT": [
        "incident:create",
        "incident:view_self",
        "incident:confirm_resolution",
        "attendance:view_self",
        "building:read",
        "floor:read",
        "room:read",
    ],
    "FACULTY": [
        "incident:create",
        "incident:create_priority",
        "attendance:mark_session",
        "attendance:view_roster",
        "building:read",
        "floor:read",
        "room:read",
        "department:read",
    ],
    "TECHNICIAN": [
        "task:view_assigned",
        "task:acknowledge",
        "task:start",
        "task:complete",
        "asset:view",
        "asset:read",
        "building:read",
        "floor:read",
        "room:read",
        "department:read",
    ],
    "WARDEN": [
        "hostel:view_queue",
        "incident:escalate",
        "mess:view_forecast",
        "attendance:view_absentees",
        "building:read",
        "floor:read",
        "room:read",
    ],
    "SAFETY_OFFICER": [
        "safety:view_confidential",
        "safety:investigate",
        "notification:emergency_broadcast",
        "building:read",
        "floor:read",
        "room:read",
    ],
    "CAMPUS_ADMIN": [
        "incident:manage_all",
        "task:reassign",
        "approval:decide",
        "policy:manage",
        "audit:view",
        "asset:view",
        "department:read",
        "department:create",
        "department:update",
        "department:delete",
        "building:read",
        "building:create",
        "building:update",
        "building:delete",
        "floor:read",
        "floor:create",
        "floor:update",
        "floor:delete",
        "room:read",
        "room:create",
        "room:update",
        "room:delete",
        "asset:read",
        "asset:create",
        "asset:update",
        "asset:delete",
    ],
    "SUPER_ADMIN": [
        "tenant:provision",
        "campus:manage",
        "system:configure",
        "audit:export_all",
        "incident:manage_all",
        "approval:decide",
        "audit:view",
        "department:read",
        "department:create",
        "department:update",
        "department:delete",
        "building:read",
        "building:create",
        "building:update",
        "building:delete",
        "floor:read",
        "floor:create",
        "floor:update",
        "floor:delete",
        "room:read",
        "room:create",
        "room:update",
        "room:delete",
        "asset:read",
        "asset:create",
        "asset:update",
        "asset:delete",
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

        # 5. Campus Operational Graph (Departments, Buildings, Floors, Rooms, Assets)
        self.stdout.write(self.style.NOTICE("📍 Provisioning Campus Operational Graph..."))

        # Departments
        depts_data = [
            {"code": "IT", "name": "Information Technology Services", "email": "it-support@apex.edu"},
            {"code": "FACILITIES", "name": "Facilities & Maintenance", "email": "facilities@apex.edu"},
            {"code": "ELECTRICAL", "name": "Electrical Infrastructure", "email": "electrical@apex.edu"},
            {"code": "SECURITY", "name": "Campus Security & Trust", "email": "security-desk@apex.edu"},
            {"code": "ADMIN", "name": "Campus Administration", "email": "admin-office@apex.edu"},
        ]
        dept_objs = {}
        for d_info in depts_data:
            dept, created = Department.all_objects.get_or_create(
                organization=org,
                campus=eng_campus,
                code=d_info["code"],
                defaults={
                    "name": d_info["name"],
                    "contact_email": d_info["email"],
                    "status": DepartmentStatus.ACTIVE,
                },
            )
            dept_objs[d_info["code"]] = dept
            self.stdout.write(f"  • Department: {dept.name} ({'created' if created else 'exists'})")

        # Buildings
        bldgs_data = [
            {"code": "ENG-BLK", "name": "Engineering Block B", "floors": 3},
            {"code": "SCI-BLK", "name": "Science Block", "floors": 3},
            {"code": "LIB-CTR", "name": "Central Library", "floors": 2},
        ]
        bldg_objs = {}
        for b_info in bldgs_data:
            bldg, created = Building.all_objects.get_or_create(
                organization=org,
                campus=eng_campus,
                code=b_info["code"],
                defaults={
                    "name": b_info["name"],
                    "floors_count": b_info["floors"],
                    "status": BuildingStatus.OPERATIONAL,
                },
            )
            bldg_objs[b_info["code"]] = bldg
            self.stdout.write(f"  • Building: {bldg.name} ({'created' if created else 'exists'})")

        # Floors for ENG-BLK
        eng_bldg = bldg_objs["ENG-BLK"]
        floors_data = [
            {"num": 0, "label": "Ground Floor"},
            {"num": 1, "label": "1st Floor"},
            {"num": 2, "label": "2nd Floor"},
        ]
        floor_objs = {}
        for fl_info in floors_data:
            floor, created = Floor.all_objects.get_or_create(
                organization=org,
                campus=eng_campus,
                building=eng_bldg,
                floor_number=fl_info["num"],
                defaults={"label": fl_info["label"]},
            )
            floor_objs[fl_info["num"]] = floor
            self.stdout.write(f"  • Floor: {floor.label} ({'created' if created else 'exists'})")

        # Rooms for ENG-BLK
        rooms_data = [
            {"floor_num": 0, "number": "001", "name": "Server & Utility Room", "type": RoomType.UTILITY, "cap": 5},
            {"floor_num": 1, "number": "101", "name": "Lecture Hall A", "type": RoomType.CLASSROOM, "cap": 60},
            {"floor_num": 2, "number": "204", "name": "Computer Networks Lab", "type": RoomType.LAB, "cap": 40},
        ]
        room_objs = {}
        for rm_info in rooms_data:
            fl = floor_objs[rm_info["floor_num"]]
            room, created = Room.all_objects.get_or_create(
                organization=org,
                campus=eng_campus,
                building=eng_bldg,
                floor=fl,
                room_number=rm_info["number"],
                defaults={
                    "name": rm_info["name"],
                    "room_type": rm_info["type"],
                    "capacity": rm_info["cap"],
                    "status": RoomStatus.AVAILABLE,
                },
            )
            room_objs[rm_info["number"]] = room
            self.stdout.write(f"  • Room: {room} ({'created' if created else 'exists'})")

        # Assets
        assets_data = [
            {
                "tag": "AST-AP-004",
                "name": "Wi-Fi Access Point AP-04",
                "category": AssetCategory.NETWORKING,
                "dept": dept_objs["IT"],
                "room": room_objs["204"],
            },
            {
                "tag": "AST-SW-001",
                "name": "Core Switch 48-Port Cisco",
                "category": AssetCategory.NETWORKING,
                "dept": dept_objs["IT"],
                "room": room_objs["001"],
            },
            {
                "tag": "AST-AC-101",
                "name": "Split AC Unit 2-Ton Daikin",
                "category": AssetCategory.HVAC,
                "dept": dept_objs["FACILITIES"],
                "room": room_objs["101"],
            },
            {
                "tag": "AST-GEN-001",
                "name": "Diesel Backup Generator 250kVA",
                "category": AssetCategory.ELECTRICAL,
                "dept": dept_objs["ELECTRICAL"],
                "room": room_objs["001"],
            },
            {
                "tag": "AST-CAM-012",
                "name": "CCTV Camera Main Entrance",
                "category": AssetCategory.SECURITY_EQUIPMENT,
                "dept": dept_objs["SECURITY"],
                "room": None,
                "building": eng_bldg,
            },
        ]

        for a_info in assets_data:
            rm = a_info.get("room")
            fl = rm.floor if rm else None
            bld = rm.building if rm else a_info.get("building")
            asset, created = Asset.all_objects.get_or_create(
                organization=org,
                campus=eng_campus,
                asset_tag=a_info["tag"],
                defaults={
                    "name": a_info["name"],
                    "category": a_info["category"],
                    "department": a_info["dept"],
                    "building": bld,
                    "floor": fl,
                    "room": rm,
                    "status": AssetStatus.OPERATIONAL,
                },
            )
            self.stdout.write(f"  • Asset: {asset.name} [{asset.asset_tag}] ({'created' if created else 'exists'})")

        log_audit_event(
            action="system.seed_dev_data",
            entity_type="System",
            entity_id="development_seed",
            actor=None,
            actor_type="SYSTEM",
            organization=org,
            post_state={"status": "complete", "users_seeded": len(dev_users_data), "assets_seeded": len(assets_data)},
        )

        self.stdout.write(self.style.SUCCESS("✅ Development seed data successfully provisioned!"))
