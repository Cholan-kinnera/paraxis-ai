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
from core.models.incident import (
    Incident,
    IncidentEvent,
    IncidentStatus,
    IncidentPriority,
    IncidentCategory,
    IncidentEventType,
)
from datetime import timedelta
from core.models.sla import SLA, SLATracking, SLAState
from core.models.task import (
    Task,
    TaskEvent,
    TaskStatus,
    TaskType,
    TaskEventType,
)
from core.services.sla import attach_sla_to_task
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
    ("task:create", "Create operational tasks", "task"),
    ("task:read", "View operational tasks", "task"),
    ("task:update", "Update operational tasks", "task"),
    ("task:cancel", "Cancel operational tasks", "task"),
    ("task:view_assigned", "View assigned tasks", "task"),
    ("task:acknowledge", "Acknowledge task assignment", "task"),
    ("task:start", "Start task work", "task"),
    ("task:complete", "Complete task work", "task"),
    ("task:reassign", "Reassign task to another technician", "task"),
    ("task:manage_all", "Manage all campus tasks", "task"),
    # SLAs
    ("sla:read", "View SLA policies", "governance"),
    ("sla:manage", "Manage SLA policies", "governance"),
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
        "task:read",
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
        "task:create",
        "task:read",
        "task:update",
        "task:reassign",
        "task:start",
        "task:complete",
        "task:cancel",
        "task:manage_all",
        "sla:read",
        "sla:manage",
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
        "task:create",
        "task:read",
        "task:update",
        "task:reassign",
        "task:start",
        "task:complete",
        "task:cancel",
        "task:manage_all",
        "sla:read",
        "sla:manage",
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

        user_objs = {}
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
            user_objs[user.email] = user

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

        # 7. Seed Operational Incidents (Phase 3)
        self.stdout.write("Seeding operational incidents...")
        incidents_data = [
            {
                "title": "Hardware Systems Lab Wi-Fi Access Point Offline",
                "description": "The Cisco AP in Room 101 has lost connection. Several students in the lab are unable to access lab servers.",
                "category": IncidentCategory.IT_NETWORK,
                "priority": IncidentPriority.HIGH,
                "status": IncidentStatus.IN_PROGRESS,
                "reporter": user_objs.get("student.eng@apex.edu"),
                "department": dept_objs.get("IT"),
                "assigned_to": user_objs.get("technician@apex.edu"),
                "building": eng_bldg,
                "room": room_objs.get("101"),
                "asset": Asset.all_objects.filter(campus=eng_campus, asset_tag="AST-AP-101").first(),
            },
            {
                "title": "Split AC in Hardware Lab Blowing Warm Air",
                "description": "The Daikin 2-ton split AC is blowing ambient air instead of cooling. Ambient lab temperature rising.",
                "category": IncidentCategory.HVAC,
                "priority": IncidentPriority.MEDIUM,
                "status": IncidentStatus.ASSIGNED,
                "reporter": user_objs.get("faculty@apex.edu"),
                "department": dept_objs.get("FACILITIES"),
                "building": eng_bldg,
                "room": room_objs.get("101"),
                "asset": Asset.all_objects.filter(campus=eng_campus, asset_tag="AST-AC-101").first(),
            },
            {
                "title": "Corridor Light Flickering Near Server Room Entrance",
                "description": "Fluorescent fixture outside server room 001 is flickering rapidly, causing a visual hazard.",
                "category": IncidentCategory.ELECTRICAL,
                "priority": IncidentPriority.LOW,
                "status": IncidentStatus.INGESTED,
                "reporter": user_objs.get("student.eng@apex.edu"),
                "department": dept_objs.get("ELECTRICAL"),
                "building": eng_bldg,
                "room": room_objs.get("001"),
            },
        ]

        for inc_info in incidents_data:
            rm = inc_info.get("room")
            fl = rm.floor if rm else None
            bld = rm.building if rm else inc_info.get("building")
            inc, created = Incident.all_objects.get_or_create(
                organization=org,
                campus=eng_campus,
                title=inc_info["title"],
                defaults={
                    "description": inc_info["description"],
                    "category": inc_info["category"],
                    "priority": inc_info["priority"],
                    "status": inc_info["status"],
                    "reporter": inc_info["reporter"],
                    "department": inc_info.get("department"),
                    "assigned_to": inc_info.get("assigned_to"),
                    "building": bld,
                    "floor": fl,
                    "room": rm,
                    "asset": inc_info.get("asset"),
                },
            )
            if created:
                IncidentEvent.objects.create(
                    organization=org,
                    campus=eng_campus,
                    incident=inc,
                    event_type=IncidentEventType.REPORTED,
                    description=f"Incident reported: {inc.title}",
                    actor=inc.reporter,
                    metadata={"priority": inc.priority, "status": inc.status},
                )
            self.stdout.write(f"  • Incident: {inc.title} [{inc.status}] ({'created' if created else 'exists'})")

        # 8. Seed SLA Policies (Phase 4)
        self.stdout.write("Seeding SLA policies...")
        sla_data = [
            {
                "name": "Critical Incident SLA",
                "priority": IncidentPriority.CRITICAL,
                "response_target": timedelta(minutes=15),
                "resolution_target": timedelta(hours=2),
            },
            {
                "name": "High Priority SLA",
                "priority": IncidentPriority.HIGH,
                "response_target": timedelta(minutes=30),
                "resolution_target": timedelta(hours=4),
            },
            {
                "name": "Medium Priority SLA",
                "priority": IncidentPriority.MEDIUM,
                "response_target": timedelta(hours=2),
                "resolution_target": timedelta(hours=24),
            },
            {
                "name": "Low Priority SLA",
                "priority": IncidentPriority.LOW,
                "response_target": timedelta(hours=4),
                "resolution_target": timedelta(hours=48),
            },
        ]
        for s_info in sla_data:
            sla_obj, created = SLA.all_objects.get_or_create(
                organization=org,
                campus=eng_campus,
                name=s_info["name"],
                defaults={
                    "priority": s_info["priority"],
                    "response_target": s_info["response_target"],
                    "resolution_target": s_info["resolution_target"],
                    "active": True,
                },
            )
            self.stdout.write(f"  • SLA: {sla_obj.name} ({'created' if created else 'exists'})")

        # 9. Seed Operational Tasks (Phase 4)
        self.stdout.write("Seeding operational tasks for North-Star Wi-Fi incident...")
        wifi_inc = Incident.all_objects.filter(campus=eng_campus, title__icontains="Wi-Fi Access Point").first()
        if wifi_inc:
            tasks_data = [
                {
                    "title": "Inspect AP-204 PoE & Radio Status",
                    "description": "Examine physical AP-204 unit in Room 101, verify PoE injector power lights and reboot radio module.",
                    "task_type": TaskType.INSPECTION,
                    "priority": IncidentPriority.HIGH,
                    "status": TaskStatus.IN_PROGRESS,
                    "assigned_user": user_objs.get("technician@apex.edu"),
                    "assigned_department": dept_objs.get("IT"),
                },
                {
                    "title": "Verify Network Connectivity & Gateway Ping",
                    "description": "Run automated subnet ping and verify DNS resolution from student terminals in Room 101.",
                    "task_type": TaskType.FOLLOW_UP,
                    "priority": IncidentPriority.HIGH,
                    "status": TaskStatus.PENDING,
                    "assigned_user": None,
                    "assigned_department": dept_objs.get("IT"),
                },
                {
                    "title": "Confirm Student Resolution & Close Loop",
                    "description": "Verify with student lab representatives that access to lab presentation servers has resumed.",
                    "task_type": TaskType.COMMUNICATION,
                    "priority": IncidentPriority.MEDIUM,
                    "status": TaskStatus.PENDING,
                    "assigned_user": None,
                    "assigned_department": dept_objs.get("IT"),
                },
            ]

            admin_user = user_objs.get("campus.admin@apex.edu") or user_objs.get("superadmin@apex.edu")

            for t_info in tasks_data:
                task_obj, created = Task.all_objects.get_or_create(
                    organization=org,
                    campus=eng_campus,
                    incident=wifi_inc,
                    title=t_info["title"],
                    defaults={
                        "description": t_info["description"],
                        "task_type": t_info["task_type"],
                        "priority": t_info["priority"],
                        "status": t_info["status"],
                        "assigned_user": t_info.get("assigned_user"),
                        "assigned_department": t_info.get("assigned_department"),
                        "created_by": admin_user,
                    },
                )
                attach_sla_to_task(task_obj)
                if created:
                    TaskEvent.all_objects.create(
                        organization=org,
                        campus=eng_campus,
                        task=task_obj,
                        event_type=TaskEventType.CREATED,
                        actor=admin_user,
                        message=f"Task seeded: {task_obj.title}",
                    )
                    if task_obj.status == TaskStatus.IN_PROGRESS:
                        TaskEvent.all_objects.create(
                            organization=org,
                            campus=eng_campus,
                            task=task_obj,
                            event_type=TaskEventType.STARTED,
                            actor=task_obj.assigned_user,
                            message="Technician on site, diagnostic tests initiated.",
                        )
                self.stdout.write(f"  • Task: {task_obj.title} [{task_obj.status}] ({'created' if created else 'exists'})")

        log_audit_event(
            action="system.seed_dev_data",
            entity_type="System",
            entity_id="development_seed",
            actor=None,
            actor_type="SYSTEM",
            organization=org,
            post_state={"status": "complete", "users_seeded": len(dev_users_data), "assets_seeded": len(assets_data), "incidents_seeded": len(incidents_data)},
        )

        self.stdout.write(self.style.SUCCESS("✅ Development seed data successfully provisioned!"))
