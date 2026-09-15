"""
API Views for Paraxis AI Operational Memory & Institutional Knowledge.
Exposes POST /api/v1/memory/search/ and GET /api/v1/memory/insights/.
Enforces fail-closed multi-tenancy, vector dimension validation, and correlation tracing.
Adheres to ADR-002, ADR-003, ADR-006, and Phase 6 Architecture Plan v2.
"""
import uuid
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError

from core.permissions.rbac import IsAuthenticatedUser
from core.models.memory import OperationalInsight
from core.models.campus_graph import Building, Room, Asset
from core.serializers.memory import (
    OperationalMemorySearchSerializer,
    OperationalMemorySearchResultSerializer,
    OperationalInsightSerializer,
    OperationalMemoryIndexSerializer,
)
from core.services.memory import (
    search_operational_memory,
    index_memory_chunk,
)

logger = logging.getLogger("paraxis.core.views.memory")


def get_authenticated_tenant_context(request) -> tuple[uuid.UUID, uuid.UUID]:
    """
    Derives and verifies organization and campus context from the authenticated user token.
    Fails closed if the caller lacks active organization or campus tenancy.
    NEVER trusts tenant IDs supplied in request payloads or unauthenticated query parameters.
    """
    user = request.user
    if not user or not user.is_authenticated or not user.is_active:
        raise PermissionDenied("Authentication required to access operational memory.")

    organization_id = getattr(request, "active_organization_id", None) or user.organization_id
    if not organization_id:
        raise PermissionDenied("User lacks organization context.")

    campus_id = getattr(request, "active_campus_id", None) or user.primary_campus_id
    if not campus_id:
        raise PermissionDenied("User lacks verified active campus context.")

    return organization_id, campus_id


class OperationalMemorySearchView(APIView):
    """
    POST /api/v1/memory/search/
    Internal semantic memory retrieval endpoint.
    Performs pgvector cosine similarity search over OperationalMemoryChunk.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request, *args, **kwargs):
        organization_id, campus_id = get_authenticated_tenant_context(request)

        serializer = OperationalMemorySearchSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated = serializer.validated_data

        query_embedding = validated["query_embedding"]
        limit = validated.get("limit", 5)
        threshold = validated.get("threshold")
        source_type = validated.get("source_type")
        category = validated.get("category")
        building_id = validated.get("building_id")
        room_id = validated.get("room_id")
        asset_id = validated.get("asset_id")

        results = search_operational_memory(
            organization_id=organization_id,
            campus_id=campus_id,
            query_embedding=query_embedding,
            limit=limit,
            threshold=threshold,
            source_type=source_type,
            category=category,
            building_id=building_id,
            room_id=room_id,
            asset_id=asset_id,
        )

        return Response(
            {
                "data": results,
                "meta": {
                    "total_results": len(results),
                    "limit": limit,
                    "threshold": threshold,
                    "query_dimension": len(query_embedding),
                },
            },
            status=status.HTTP_200_OK,
        )


class OperationalInsightListView(APIView):
    """
    GET /api/v1/memory/insights/
    Lists institutional knowledge and recurring problem insights for the active campus.
    """
    permission_classes = [IsAuthenticatedUser]

    def get(self, request, *args, **kwargs):
        organization_id, campus_id = get_authenticated_tenant_context(request)

        qs = OperationalInsight.objects.filter(
            organization_id=organization_id,
            campus_id=campus_id,
        ).select_related(
            "target_asset", "target_room", "target_building"
        ).prefetch_related(
            "evidence_links__incident"
        )

        # Optional query filters
        status_filter = request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        insight_type_filter = request.query_params.get("insight_type")
        if insight_type_filter:
            qs = qs.filter(insight_type=insight_type_filter)

        asset_filter = request.query_params.get("target_asset")
        if asset_filter:
            qs = qs.filter(target_asset_id=asset_filter)

        room_filter = request.query_params.get("target_room")
        if room_filter:
            qs = qs.filter(target_room_id=room_filter)

        serializer = OperationalInsightSerializer(qs, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)


class OperationalMemoryIndexView(APIView):
    """
    POST /api/v1/memory/index/
    Internal API allowing ingestion of pre-vectorized operational memory chunks into Django Core.
    """
    permission_classes = [IsAuthenticatedUser]

    def post(self, request, *args, **kwargs):
        organization_id, campus_id = get_authenticated_tenant_context(request)

        serializer = OperationalMemoryIndexSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        building = None
        if data.get("building_id"):
            building = Building.objects.filter(
                id=data["building_id"], organization_id=organization_id, campus_id=campus_id
            ).first()

        room = None
        if data.get("room_id"):
            room = Room.objects.filter(
                id=data["room_id"], organization_id=organization_id, campus_id=campus_id
            ).first()

        asset = None
        if data.get("asset_id"):
            asset = Asset.objects.filter(
                id=data["asset_id"], organization_id=organization_id, campus_id=campus_id
            ).first()

        chunk, created_or_updated = index_memory_chunk(
            organization_id=organization_id,
            campus_id=campus_id,
            source_type=data["source_type"],
            source_id=data["source_id"],
            title=data["title"],
            canonical_text=data["canonical_text"],
            embedding=data["embedding"],
            embedding_provider=data.get("embedding_provider", "mock"),
            embedding_model=data.get("embedding_model", "mock-paraxis-v1"),
            category=data.get("category", ""),
            building=building,
            room=room,
            asset=asset,
            metadata_payload=data.get("metadata_payload", {}),
        )

        return Response(
            {
                "data": {
                    "id": str(chunk.id),
                    "source_version": chunk.source_version,
                    "content_hash": chunk.content_hash,
                    "updated": created_or_updated,
                }
            },
            status=status.HTTP_201_CREATED if created_or_updated else status.HTTP_200_OK,
        )
