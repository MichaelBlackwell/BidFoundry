"""Company profile API endpoints."""

from fastapi import APIRouter, HTTPException, Query, status

from server.dependencies import DbSession
from server.models.schemas import (
    CompanyProfileCreate,
    CompanyProfileListResponse,
    CompanyProfileResponse,
    CompanyProfileUpdate,
)
from server.services.profiles import ProfilesService

router = APIRouter()


@router.get("", response_model=CompanyProfileListResponse)
async def list_profiles(
    db: DbSession,
    limit: int = Query(default=20, ge=1, le=100, description="Maximum number of results"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> CompanyProfileListResponse:
    """List all company profiles with pagination."""
    service = ProfilesService(db)
    profiles, total = await service.get_all(limit=limit, offset=offset)

    return CompanyProfileListResponse(
        profiles=[CompanyProfileResponse.model_validate(p) for p in profiles],
        total=total,
    )


@router.get("/{profile_id}", response_model=CompanyProfileResponse)
async def get_profile(
    profile_id: str,
    db: DbSession,
) -> CompanyProfileResponse:
    """Get a company profile by ID."""
    service = ProfilesService(db)
    profile = await service.get_by_id(profile_id)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROFILE_NOT_FOUND",
                "message": f"Company profile not found: {profile_id}",
                "details": {"profileId": profile_id},
            },
        )

    return CompanyProfileResponse.model_validate(profile)


@router.post("", response_model=CompanyProfileResponse, status_code=status.HTTP_201_CREATED)
async def create_profile(
    data: CompanyProfileCreate,
    db: DbSession,
) -> CompanyProfileResponse:
    """Create a new company profile."""
    service = ProfilesService(db)
    profile = await service.create(data)
    return CompanyProfileResponse.model_validate(profile)


@router.put("/{profile_id}", response_model=CompanyProfileResponse)
async def update_profile(
    profile_id: str,
    data: CompanyProfileUpdate,
    db: DbSession,
) -> CompanyProfileResponse:
    """Update an existing company profile."""
    service = ProfilesService(db)
    profile = await service.update(profile_id, data)

    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROFILE_NOT_FOUND",
                "message": f"Company profile not found: {profile_id}",
                "details": {"profileId": profile_id},
            },
        )

    return CompanyProfileResponse.model_validate(profile)


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_profile(
    profile_id: str,
    db: DbSession,
) -> None:
    """Delete a company profile."""
    service = ProfilesService(db)
    deleted = await service.delete(profile_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "PROFILE_NOT_FOUND",
                "message": f"Company profile not found: {profile_id}",
                "details": {"profileId": profile_id},
            },
        )
