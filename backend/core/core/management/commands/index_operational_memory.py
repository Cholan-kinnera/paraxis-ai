"""
Django Management Command: index_operational_memory
Populates pgvector operational memory from canonical campus entities:
- Resolved / Verified / Closed Incidents
- Completed Tasks
- Physical Infrastructure Assets

Idempotent: Identifies entities by (tenant, campus, source_type, source_id).
Avoids re-generating embeddings if SHA-256 canonical_text content hash is unchanged.
Adheres to ADR-002, ADR-003, and Phase 6 Architecture Plan v2.
"""
import asyncio
import uuid
import logging
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.context import set_current_tenant
from core.models.organization import Organization, Campus
from core.models.incident import Incident, IncidentStatus
from core.models.task import Task, TaskStatus
from core.models.campus_graph import Asset
from core.models.memory import (
    OperationalMemoryChunk,
    OperationalMemorySourceType,
)
from core.services.memory import (
    generate_canonical_incident_text,
    generate_canonical_task_text,
    generate_canonical_asset_text,
    compute_content_hash,
    index_memory_chunk,
)
import sys
from pathlib import Path
repo_root = Path(__file__).resolve().parents[5]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from core.services.recurring_detector import detect_recurring_problems
from backend.intelligence.providers.factory import get_model_client

logger = logging.getLogger("paraxis.core.commands.index_operational_memory")


class Command(BaseCommand):
    help = "Idempotently backfills structured operational memory into pgvector."

    def add_arguments(self, parser):
        parser.add_argument(
            "--organization-id",
            type=str,
            help="Filter by specific Organization UUID",
        )
        parser.add_argument(
            "--campus-id",
            type=str,
            help="Filter by specific Campus UUID",
        )
        parser.add_argument(
            "--provider",
            type=str,
            default="mock",
            choices=["mock", "google", "openai"],
            help="Embedding provider to vectorize text (default: mock)",
        )
        parser.add_argument(
            "--reindex",
            action="store_true",
            help="Force re-generation of embeddings even if content hash is unchanged",
        )
        parser.add_argument(
            "--detect-insights",
            action="store_true",
            default=True,
            help="Execute recurring problem detection after indexing (default: True)",
        )

    def handle(self, *args, **options):
        org_id_str = options.get("organization_id")
        campus_id_str = options.get("campus_id")
        provider_name = options.get("provider", "mock")
        force_reindex = options.get("reindex", False)
        run_detect = options.get("detect_insights", True)

        org_filter = uuid.UUID(org_id_str) if org_id_str else None
        campus_filter = uuid.UUID(campus_id_str) if campus_id_str else None

        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"Starting Operational Memory Indexing (Provider: {provider_name}, Reindex: {force_reindex})..."
            )
        )

        model_client = get_model_client(provider_name)

        campuses_qs = Campus.objects.all()
        if org_filter:
            campuses_qs = campuses_qs.filter(organization_id=org_filter)
        if campus_filter:
            campuses_qs = campuses_qs.filter(id=campus_filter)

        total_created = 0
        total_updated = 0
        total_skipped = 0
        total_insights = 0

        for campus in campuses_qs:
            org = campus.organization
            set_current_tenant(org.id, campus.id)
            self.stdout.write(f"\nProcessing Tenant: {org.name} | Campus: {campus.name}")

            # -----------------------------------------------------------------
            # 1. Resolved / Verified / Closed Incidents
            # -----------------------------------------------------------------
            incidents = (
                Incident.all_objects.filter(
                    organization=org,
                    campus=campus,
                    status__in=[
                        IncidentStatus.RESOLVED,
                        IncidentStatus.VERIFIED,
                        IncidentStatus.CLOSED,
                    ],
                    deleted_at__isnull=True,
                )
                .select_related("building", "floor", "room", "asset")
                .prefetch_related("events")
            )

            for inc in incidents:
                title, canonical_text, metadata = generate_canonical_incident_text(inc)
                content_hash = compute_content_hash(canonical_text)

                existing = OperationalMemoryChunk.all_objects.filter(
                    organization=org,
                    campus=campus,
                    source_type=OperationalMemorySourceType.INCIDENT,
                    source_id=str(inc.id),
                ).first()

                if existing and existing.content_hash == content_hash and not force_reindex:
                    total_skipped += 1
                    continue

                # Generate 768-dim embedding
                embedding = asyncio.run(model_client.embed([canonical_text]))[0]

                chunk, was_modified = index_memory_chunk(
                    organization_id=org.id,
                    campus_id=campus.id,
                    source_type=OperationalMemorySourceType.INCIDENT,
                    source_id=str(inc.id),
                    title=title,
                    canonical_text=canonical_text,
                    embedding=embedding,
                    embedding_provider=provider_name,
                    embedding_model=f"{provider_name}-v1",
                    category=inc.category,
                    building=inc.building,
                    room=inc.room,
                    asset=inc.asset,
                    metadata_payload=metadata,
                    source_updated_at=inc.updated_at,
                )
                if was_modified:
                    if chunk.source_version == 1:
                        total_created += 1
                    else:
                        total_updated += 1
                else:
                    total_skipped += 1

            # -----------------------------------------------------------------
            # 2. Completed Tasks
            # -----------------------------------------------------------------
            tasks = Task.all_objects.filter(
                organization=org,
                campus=campus,
                status=TaskStatus.COMPLETED,
            ).select_related("assigned_department", "assigned_user")

            for task in tasks:
                title, canonical_text, metadata = generate_canonical_task_text(task)
                content_hash = compute_content_hash(canonical_text)

                existing = OperationalMemoryChunk.all_objects.filter(
                    organization=org,
                    campus=campus,
                    source_type=OperationalMemorySourceType.TASK,
                    source_id=str(task.id),
                ).first()

                if existing and existing.content_hash == content_hash and not force_reindex:
                    total_skipped += 1
                    continue

                embedding = asyncio.run(model_client.embed([canonical_text]))[0]

                chunk, was_modified = index_memory_chunk(
                    organization_id=org.id,
                    campus_id=campus.id,
                    source_type=OperationalMemorySourceType.TASK,
                    source_id=str(task.id),
                    title=title,
                    canonical_text=canonical_text,
                    embedding=embedding,
                    embedding_provider=provider_name,
                    embedding_model=f"{provider_name}-v1",
                    category=task.category if hasattr(task, "category") else "",
                    metadata_payload=metadata,
                    source_updated_at=task.updated_at,
                )
                if was_modified:
                    if chunk.source_version == 1:
                        total_created += 1
                    else:
                        total_updated += 1
                else:
                    total_skipped += 1

            # -----------------------------------------------------------------
            # 3. Assets
            # -----------------------------------------------------------------
            assets = Asset.all_objects.filter(
                organization=org,
                campus=campus,
            ).select_related("building", "room")

            for asset in assets:
                title, canonical_text, metadata = generate_canonical_asset_text(asset)
                content_hash = compute_content_hash(canonical_text)

                existing = OperationalMemoryChunk.all_objects.filter(
                    organization=org,
                    campus=campus,
                    source_type=OperationalMemorySourceType.ASSET,
                    source_id=str(asset.id),
                ).first()

                if existing and existing.content_hash == content_hash and not force_reindex:
                    total_skipped += 1
                    continue

                embedding = asyncio.run(model_client.embed([canonical_text]))[0]

                chunk, was_modified = index_memory_chunk(
                    organization_id=org.id,
                    campus_id=campus.id,
                    source_type=OperationalMemorySourceType.ASSET,
                    source_id=str(asset.id),
                    title=title,
                    canonical_text=canonical_text,
                    embedding=embedding,
                    embedding_provider=provider_name,
                    embedding_model=f"{provider_name}-v1",
                    category=asset.category,
                    building=asset.building,
                    room=asset.room,
                    asset=asset,
                    metadata_payload=metadata,
                    source_updated_at=asset.updated_at,
                )
                if was_modified:
                    if chunk.source_version == 1:
                        total_created += 1
                    else:
                        total_updated += 1
                else:
                    total_skipped += 1

            # -----------------------------------------------------------------
            # 4. Recurring Problem Detection
            # -----------------------------------------------------------------
            if run_detect:
                insights = detect_recurring_problems(
                    organization_id=org.id,
                    campus_id=campus.id,
                )
                total_insights += len(insights)
                self.stdout.write(f"  Generated {len(insights)} operational insights for {campus.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nOperational Memory Indexing Complete:\n"
                f"  Created:  {total_created}\n"
                f"  Updated:  {total_updated}\n"
                f"  Skipped (hash match): {total_skipped}\n"
                f"  Active Insights: {total_insights}"
            )
        )
