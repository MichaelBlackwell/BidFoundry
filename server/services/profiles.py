"""Company profile management service."""

from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from server.models.database import CompanyProfile
from server.models.schemas import CompanyProfileCreate, CompanyProfileUpdate


class ProfilesService:
    """Service for managing company profiles."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self, limit: int = 100, offset: int = 0) -> tuple[list[CompanyProfile], int]:
        """
        Get all company profiles with pagination.

        Returns:
            Tuple of (profiles list, total count)
        """
        # Get total count
        count_stmt = select(func.count()).select_from(CompanyProfile)
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar() or 0

        # Get profiles with pagination
        stmt = (
            select(CompanyProfile)
            .order_by(CompanyProfile.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.db.execute(stmt)
        profiles = list(result.scalars().all())

        return profiles, total

    async def get_by_id(self, profile_id: str) -> Optional[CompanyProfile]:
        """Get a company profile by ID."""
        stmt = select(CompanyProfile).where(CompanyProfile.id == profile_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, data: CompanyProfileCreate) -> CompanyProfile:
        """Create a new company profile."""
        profile = CompanyProfile(
            name=data.name,
            description=data.description,
            naics_codes=data.naics_codes,
            certifications=data.certifications,
            past_performance=data.past_performance,
            full_profile=data.full_profile,
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update(self, profile_id: str, data: CompanyProfileUpdate) -> Optional[CompanyProfile]:
        """
        Update an existing company profile.

        Returns:
            Updated profile or None if not found
        """
        profile = await self.get_by_id(profile_id)
        if not profile:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True, by_alias=False)
        for field, value in update_data.items():
            setattr(profile, field, value)

        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def delete(self, profile_id: str) -> bool:
        """
        Delete a company profile.

        Returns:
            True if deleted, False if not found
        """
        profile = await self.get_by_id(profile_id)
        if not profile:
            return False

        await self.db.delete(profile)
        await self.db.flush()
        return True
