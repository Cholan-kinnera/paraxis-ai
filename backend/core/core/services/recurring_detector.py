"""
Deterministic Recurring Problem & Operational Anomaly Detector for Paraxis AI.
Identifies recurring asset failures and location hotspots within a rolling 30-day window.
Guarantees strict epistemological segregation: FACT vs. INFERENCE vs. RECOMMENDATION.
Adheres to ADR-003, ADR-006, and Phase 6 Architecture Plan v2.
"""
import logging
import uuid
from datetime import timedelta
from typing import List, Optional
from django.utils import timezone
from django.db import transaction

from core.context import set_current_tenant
from core.models.memory import (
    OperationalInsight,
    OperationalInsightType,
    OperationalInsightStatus,
    OperationalInsightIncidentEvidence,
)
from core.models.incident import Incident
from core.models.campus_graph import Asset, Room

logger = logging.getLogger("paraxis.core.recurring_detector")

DEFAULT_WINDOW_DAYS = 30
ASSET_FAILURE_THRESHOLD = 3
ROOM_FAILURE_THRESHOLD = 4


@transaction.atomic
def detect_recurring_problems(
    organization_id: uuid.UUID,
    campus_id: uuid.UUID,
    window_days: int = DEFAULT_WINDOW_DAYS,
    now=None,
) -> List[OperationalInsight]:
    """
    Scans empirical incident records within the tenant campus across the rolling time window.
    Evaluates:
    1. Recurring Asset Failures (>= 3 incidents on the same asset)
    2. Room Incidents Hotspot (>= 4 incidents in the same room)

    Creates or updates OperationalInsight records and links empirical evidence through
    OperationalInsightIncidentEvidence relational records.
    """
    set_current_tenant(organization_id, campus_id)
    reference_time = now or timezone.now()
    window_start = reference_time - timedelta(days=window_days)
    window_end = reference_time + timedelta(seconds=5)

    # Base empirical incident queryset scoped to tenant and time window
    incidents_qs = Incident.all_objects.filter(
        organization_id=organization_id,
        campus_id=campus_id,
        created_at__gte=window_start,
        created_at__lte=window_end,
        deleted_at__isnull=True,
    ).select_related("asset", "room", "building")

    generated_insights: List[OperationalInsight] = []

    # -------------------------------------------------------------------------
    # RULE 1: Recurring Asset Failures (Threshold: >= 3 incidents on same asset)
    # -------------------------------------------------------------------------
    asset_incidents: dict[uuid.UUID, List[Incident]] = {}
    for inc in incidents_qs:
        if inc.asset_id:
            asset_incidents.setdefault(inc.asset_id, []).append(inc)

    for asset_id, inc_list in asset_incidents.items():
        if len(inc_list) >= ASSET_FAILURE_THRESHOLD:
            asset = inc_list[0].asset
            incident_ids_str = ", ".join(str(i.id) for i in inc_list)
            categories = sorted(set(i.category for i in inc_list))

            # Strictly verifiable records only
            fact_summary = (
                f"FACT: Asset '{asset.name}' (Tag: {asset.asset_tag}, Category: {asset.category}) "
                f"recorded {len(inc_list)} operational incidents between {window_start.strftime('%Y-%m-%d')} "
                f"and {window_end.strftime('%Y-%m-%d')}. "
                f"Categories: {', '.join(categories)}. "
                f"Empirical Incident IDs: {incident_ids_str}."
            )

            # Probabilistic deductions based on recurrence
            inference_analysis = (
                f"INFERENCE: {len(inc_list)} failure events within a {window_days}-day window "
                f"indicates chronic asset degradation, recurring component malfunction, or "
                f"inadequate root-cause resolution during preceding work orders."
            )

            # Actionable recommendations for facilities personnel
            recommendation = (
                f"RECOMMENDATION: Dispatch a qualified senior technician to conduct a comprehensive "
                f"diagnostic overhaul of {asset.name}. Verify supply lines and environmental operating conditions, "
                f"and review prior technician resolution logs to determine if full component replacement is required."
            )

            # Algorithmic confidence: scales with number of failures above threshold
            confidence = min(0.98, round(0.70 + (len(inc_list) - ASSET_FAILURE_THRESHOLD) * 0.08, 2))

            # Check if an active insight already exists for this asset in this window
            insight, created = OperationalInsight.objects.get_or_create(
                organization_id=organization_id,
                campus_id=campus_id,
                insight_type=OperationalInsightType.RECURRING_ASSET_FAILURE,
                target_asset=asset,
                status=OperationalInsightStatus.ACTIVE,
                defaults={
                    "target_building": asset.building,
                    "target_room": asset.room,
                    "window_start": window_start,
                    "window_end": window_end,
                    "incident_count": len(inc_list),
                    "fact_summary": fact_summary,
                    "inference_analysis": inference_analysis,
                    "recommendation": recommendation,
                    "confidence_score": confidence,
                },
            )

            if not created:
                # Update existing active insight with current window and counts
                insight.window_start = window_start
                insight.window_end = window_end
                insight.incident_count = len(inc_list)
                insight.fact_summary = fact_summary
                insight.inference_analysis = inference_analysis
                insight.recommendation = recommendation
                insight.confidence_score = confidence
                insight.save()

            # Synchronize relational evidence links
            for inc in inc_list:
                OperationalInsightIncidentEvidence.objects.get_or_create(
                    organization_id=organization_id,
                    campus_id=campus_id,
                    insight=insight,
                    incident=inc,
                    defaults={
                        "relevance_score": 1.0,
                        "evidence_notes": f"Empirical failure reported at {inc.created_at.isoformat()}",
                    },
                )

            generated_insights.append(insight)
            logger.info(
                f"Generated/updated asset recurring failure insight for asset {asset.name} ({len(inc_list)} incidents)."
            )

    # -------------------------------------------------------------------------
    # RULE 2: Location Hotspots (Threshold: >= 4 incidents in same room)
    # -------------------------------------------------------------------------
    room_incidents: dict[uuid.UUID, List[Incident]] = {}
    for inc in incidents_qs:
        if inc.room_id:
            room_incidents.setdefault(inc.room_id, []).append(inc)

    for room_id, inc_list in room_incidents.items():
        if len(inc_list) >= ROOM_FAILURE_THRESHOLD:
            room = inc_list[0].room
            incident_ids_str = ", ".join(str(i.id) for i in inc_list)
            categories = sorted(set(i.category for i in inc_list))
            bld_name = room.building.name if room.building else "Campus Facility"

            fact_summary = (
                f"FACT: Room {room.room_number} in {bld_name} recorded {len(inc_list)} operational "
                f"incidents between {window_start.strftime('%Y-%m-%d')} and {window_end.strftime('%Y-%m-%d')}. "
                f"Categories observed: {', '.join(categories)}. "
                f"Empirical Incident IDs: {incident_ids_str}."
            )

            inference_analysis = (
                f"INFERENCE: Abnormally high incident frequency ({len(inc_list)} in {window_days} days) "
                f"suggests localized environmental, electrical, or structural stress in Room {room.room_number}, "
                f"or heavy utilization exceeding designed space capacity."
            )

            recommendation = (
                f"RECOMMENDATION: Schedule an integrated facilities walk-through of Room {room.room_number}. "
                f"Examine electrical load distribution, plumbing integrity, and ventilation performance "
                f"simultaneously to detect compounding infrastructure issues."
            )

            confidence = min(0.95, round(0.65 + (len(inc_list) - ROOM_FAILURE_THRESHOLD) * 0.08, 2))

            insight, created = OperationalInsight.objects.get_or_create(
                organization_id=organization_id,
                campus_id=campus_id,
                insight_type=OperationalInsightType.LOCATION_HOTSPOT,
                target_room=room,
                status=OperationalInsightStatus.ACTIVE,
                defaults={
                    "target_building": room.building,
                    "window_start": window_start,
                    "window_end": window_end,
                    "incident_count": len(inc_list),
                    "fact_summary": fact_summary,
                    "inference_analysis": inference_analysis,
                    "recommendation": recommendation,
                    "confidence_score": confidence,
                },
            )

            if not created:
                insight.window_start = window_start
                insight.window_end = window_end
                insight.incident_count = len(inc_list)
                insight.fact_summary = fact_summary
                insight.inference_analysis = inference_analysis
                insight.recommendation = recommendation
                insight.confidence_score = confidence
                insight.save()

            for inc in inc_list:
                OperationalInsightIncidentEvidence.objects.get_or_create(
                    organization_id=organization_id,
                    campus_id=campus_id,
                    insight=insight,
                    incident=inc,
                    defaults={
                        "relevance_score": 1.0,
                        "evidence_notes": f"Incident reported at {inc.created_at.isoformat()} in room {room.room_number}",
                    },
                )

            generated_insights.append(insight)
            logger.info(
                f"Generated/updated location hotspot insight for room {room.room_number} ({len(inc_list)} incidents)."
            )

    return generated_insights
