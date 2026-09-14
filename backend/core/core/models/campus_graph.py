"""
Campus Operational Graph models for Paraxis AI.
Represents physical and organizational infrastructure:
Department, Building, Floor, Room, and Asset.
"""
from django.core.exceptions import ValidationError
from django.db import models
from core.models.base import TenantScopedModel


class DepartmentStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    INACTIVE = "INACTIVE", "Inactive"


class BuildingStatus(models.TextChoices):
    OPERATIONAL = "OPERATIONAL", "Operational"
    RENOVATION = "RENOVATION", "Renovation"
    DECOMMISSIONED = "DECOMMISSIONED", "Decommissioned"


class RoomType(models.TextChoices):
    CLASSROOM = "CLASSROOM", "Classroom"
    LAB = "LAB", "Laboratory"
    OFFICE = "OFFICE", "Office"
    SEMINAR_HALL = "SEMINAR_HALL", "Seminar Hall"
    HOSTEL_ROOM = "HOSTEL_ROOM", "Hostel Room"
    UTILITY = "UTILITY", "Utility / Service"
    MESS = "MESS", "Mess / Dining Hall"


class RoomStatus(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Available"
    OCCUPIED = "OCCUPIED", "Occupied"
    UNDER_MAINTENANCE = "UNDER_MAINTENANCE", "Under Maintenance"


class AssetCategory(models.TextChoices):
    NETWORKING = "NETWORKING", "Networking & IT"
    HVAC = "HVAC", "HVAC & Climate"
    ELECTRICAL = "ELECTRICAL", "Electrical & Power"
    PLUMBING = "PLUMBING", "Plumbing & Sanitation"
    SECURITY_EQUIPMENT = "SECURITY_EQUIPMENT", "Security & Surveillance"
    FURNITURE = "FURNITURE", "Furniture & Fixtures"
    GENERAL = "GENERAL", "General Equipment"


class AssetStatus(models.TextChoices):
    OPERATIONAL = "OPERATIONAL", "Operational"
    DEGRADED = "DEGRADED", "Degraded Performance"
    OUT_OF_SERVICE = "OUT_OF_SERVICE", "Out of Service"
    RETIRED = "RETIRED", "Retired"


class Department(TenantScopedModel):
    """
    Functional operational unit within a campus (e.g. IT Services, Facilities, Security).
    """
    campus_scoped = True

    name = models.CharField(max_length=255, help_text="Department name")
    code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Department code, unique per campus (e.g., 'IT', 'MAINTENANCE')",
    )
    description = models.TextField(blank=True, help_text="Description of department responsibilities")
    contact_email = models.EmailField(blank=True, help_text="Primary departmental contact email")
    escalation_contact = models.ForeignKey(
        "core.User",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_departments",
        help_text="Designated escalation contact / manager",
    )
    status = models.CharField(
        max_length=32,
        choices=DepartmentStatus.choices,
        default=DepartmentStatus.ACTIVE,
        db_index=True,
        help_text="Department operational status",
    )

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Department"
        verbose_name_plural = "Departments"
        db_table = "departments"
        constraints = [
            models.UniqueConstraint(
                fields=["campus", "code"],
                name="unique_campus_department_code",
            ),
        ]

    def __str__(self) -> str:
        campus_code = self.campus.code if self.campus else "NO-CAMPUS"
        return f"{self.name} [{self.code}] ({campus_code})"

    def clean(self):
        super().clean()
        if not self.campus_id:
            raise ValidationError({"campus": "Department must be bound to a Campus."})
        if self.campus and self.organization_id and self.campus.organization_id != self.organization_id:
            raise ValidationError({"campus": "Campus must belong to the same Organization."})
        if self.escalation_contact:
            if self.escalation_contact.organization_id != self.organization_id:
                raise ValidationError({"escalation_contact": "Escalation contact must belong to the department's Organization."})


class Building(TenantScopedModel):
    """
    Physical multi-story or standalone campus structure (e.g. Science Hall, Library).
    """
    campus_scoped = True

    name = models.CharField(max_length=255, help_text="Building name")
    code = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Building code, unique per campus (e.g., 'ENG-B', 'LIB')",
    )
    description = models.TextField(blank=True, help_text="Building description and location details")
    floors_count = models.PositiveIntegerField(
        default=1,
        help_text="Number of physical levels above or below ground",
    )
    status = models.CharField(
        max_length=32,
        choices=BuildingStatus.choices,
        default=BuildingStatus.OPERATIONAL,
        db_index=True,
        help_text="Building operational status",
    )
    gis_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Geographic coordinates, polygon boundary, or GIS coordinates",
    )

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Building"
        verbose_name_plural = "Buildings"
        db_table = "buildings"
        constraints = [
            models.UniqueConstraint(
                fields=["campus", "code"],
                name="unique_campus_building_code",
            ),
        ]

    def __str__(self) -> str:
        campus_code = self.campus.code if self.campus else "NO-CAMPUS"
        return f"{self.name} [{self.code}] ({campus_code})"

    def clean(self):
        super().clean()
        if not self.campus_id:
            raise ValidationError({"campus": "Building must belong to a Campus."})
        if self.campus and self.organization_id and self.campus.organization_id != self.organization_id:
            raise ValidationError({"campus": "Campus must belong to the same Organization."})


class Floor(TenantScopedModel):
    """
    Physical level within a Building. Supports numeric ordering and human labels.
    """
    campus_scoped = True

    building = models.ForeignKey(
        Building,
        on_delete=models.PROTECT,
        related_name="floors",
        db_index=True,
        help_text="Parent building containing this floor",
    )
    floor_number = models.IntegerField(
        help_text="Numeric floor index (e.g. -1 for basement, 0 for ground, 1 for 1st floor)",
    )
    label = models.CharField(
        max_length=50,
        help_text="Human-readable floor designation (e.g. 'Basement', 'Ground Floor', '2nd Floor')",
    )
    description = models.TextField(blank=True, help_text="Floor layout notes or facilities")

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Floor"
        verbose_name_plural = "Floors"
        db_table = "floors"
        constraints = [
            models.UniqueConstraint(
                fields=["building", "floor_number"],
                name="unique_building_floor_number",
            ),
            models.UniqueConstraint(
                fields=["building", "label"],
                name="unique_building_floor_label",
            ),
        ]
        ordering = ["building", "floor_number"]

    def __str__(self) -> str:
        return f"{self.building.code} - {self.label} (Level {self.floor_number})"

    def clean(self):
        super().clean()
        if not self.building_id:
            raise ValidationError({"building": "Floor must belong to a Building."})
        # Automatically derive organization and campus from parent building
        if self.building:
            if not self.organization_id:
                self.organization_id = self.building.organization_id
            elif self.organization_id != self.building.organization_id:
                raise ValidationError({"building": "Building belongs to a different Organization."})

            if not self.campus_id:
                self.campus_id = self.building.campus_id
            elif self.campus_id != self.building.campus_id:
                raise ValidationError({"building": "Building belongs to a different Campus."})


class Room(TenantScopedModel):
    """
    Identifiable indoor space within a Floor and Building.
    """
    campus_scoped = True

    building = models.ForeignKey(
        Building,
        on_delete=models.PROTECT,
        related_name="rooms",
        db_index=True,
        help_text="Parent building containing this room",
    )
    floor = models.ForeignKey(
        Floor,
        on_delete=models.PROTECT,
        related_name="rooms",
        db_index=True,
        help_text="Specific floor level containing this room",
    )
    room_number = models.CharField(
        max_length=50,
        db_index=True,
        help_text="Room number or code (e.g. '101', 'LAB-204')",
    )
    name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Descriptive room name (e.g. 'Computer Networks Laboratory')",
    )
    room_type = models.CharField(
        max_length=32,
        choices=RoomType.choices,
        default=RoomType.CLASSROOM,
        db_index=True,
        help_text="Room categorization",
    )
    capacity = models.PositiveIntegerField(
        default=0,
        help_text="Max seating/standing occupant capacity",
    )
    status = models.CharField(
        max_length=32,
        choices=RoomStatus.choices,
        default=RoomStatus.AVAILABLE,
        db_index=True,
        help_text="Room operational availability",
    )

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Room"
        verbose_name_plural = "Rooms"
        db_table = "rooms"
        constraints = [
            models.UniqueConstraint(
                fields=["floor", "room_number"],
                name="unique_floor_room_number",
            ),
        ]
        ordering = ["building", "floor", "room_number"]

    def __str__(self) -> str:
        label = f" ({self.name})" if self.name else ""
        return f"{self.building.code} {self.room_number}{label}"

    def clean(self):
        super().clean()
        if not self.floor_id:
            raise ValidationError({"floor": "Room must belong to a Floor."})

        # Enforce location hierarchy: Floor must belong to Building
        if self.building_id and self.floor_id:
            if self.floor.building_id != self.building_id:
                raise ValidationError({"floor": "Floor does not belong to the selected Building."})
        elif self.floor_id and not self.building_id:
            self.building = self.floor.building

        # Derive and validate tenant scope from floor/building
        if self.building:
            if not self.organization_id:
                self.organization_id = self.building.organization_id
            elif self.organization_id != self.building.organization_id:
                raise ValidationError({"building": "Building belongs to a different Organization."})

            if not self.campus_id:
                self.campus_id = self.building.campus_id
            elif self.campus_id != self.building.campus_id:
                raise ValidationError({"building": "Building belongs to a different Campus."})


class Asset(TenantScopedModel):
    """
    Physical maintainable asset or equipment grounded in campus space.
    """
    campus_scoped = True

    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="assets",
        db_index=True,
        help_text="Department responsible for maintaining this asset",
    )
    building = models.ForeignKey(
        Building,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        db_index=True,
        help_text="Building where the asset is installed",
    )
    floor = models.ForeignKey(
        Floor,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        db_index=True,
        help_text="Floor where the asset is installed",
    )
    room = models.ForeignKey(
        Room,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assets",
        db_index=True,
        help_text="Specific room containing this asset",
    )
    name = models.CharField(max_length=255, help_text="Asset display name")
    asset_tag = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Campus-unique barcode/asset identifier (e.g. 'AST-AP-004')",
    )
    serial_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Manufacturer hardware serial number",
    )
    category = models.CharField(
        max_length=32,
        choices=AssetCategory.choices,
        default=AssetCategory.GENERAL,
        db_index=True,
        help_text="Asset classification category",
    )
    status = models.CharField(
        max_length=32,
        choices=AssetStatus.choices,
        default=AssetStatus.OPERATIONAL,
        db_index=True,
        help_text="Operational condition of the asset",
    )
    install_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date the asset was commissioned or installed",
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Technical specifications, vendor details, IP/MAC addresses",
    )

    class Meta(TenantScopedModel.Meta):
        verbose_name = "Asset"
        verbose_name_plural = "Assets"
        db_table = "assets"
        constraints = [
            models.UniqueConstraint(
                fields=["campus", "asset_tag"],
                name="unique_campus_asset_tag",
            ),
        ]
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.name} [{self.asset_tag}] ({self.status})"

    def clean(self):
        super().clean()
        if not self.department_id:
            raise ValidationError({"department": "Asset must be assigned to a responsible Department."})

        # Derive tenant context from department if not set
        if self.department:
            if not self.organization_id:
                self.organization_id = self.department.organization_id
            elif self.organization_id != self.department.organization_id:
                raise ValidationError({"department": "Department belongs to a different Organization."})

            if not self.campus_id:
                self.campus_id = self.department.campus_id
            elif self.campus_id != self.department.campus_id:
                raise ValidationError({"department": "Department belongs to a different Campus."})

        # Location consistency enforcement
        if self.room:
            # Synchronize building and floor from room
            if self.floor and self.room.floor_id != self.floor_id:
                raise ValidationError({"room": "Room does not belong to the selected Floor."})
            if self.building and self.room.building_id != self.building_id:
                raise ValidationError({"room": "Room does not belong to the selected Building."})

            self.floor = self.room.floor
            self.building = self.room.building

            if self.room.campus_id != self.campus_id:
                raise ValidationError({"room": "Room belongs to a different Campus."})

        elif self.floor:
            if self.building and self.floor.building_id != self.building_id:
                raise ValidationError({"floor": "Floor does not belong to the selected Building."})
            self.building = self.floor.building

            if self.floor.campus_id != self.campus_id:
                raise ValidationError({"floor": "Floor belongs to a different Campus."})

        elif self.building:
            if self.building.campus_id != self.campus_id:
                raise ValidationError({"building": "Building belongs to a different Campus."})
