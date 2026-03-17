"""Expert registration and matching endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import Expert, get_db

router = APIRouter()


class ExpertRegistration(BaseModel):
    username: str
    display_name: str
    email: str | None = None
    subspecialty: str
    institution: str | None = None
    years_experience: int | None = None
    patient_categories: list[str] = []


class ExpertResponse(BaseModel):
    id: int
    username: str
    display_name: str
    subspecialty: str
    institution: str | None
    patient_categories: list[str]
    is_active: bool


@router.post("/register", response_model=ExpertResponse)
async def register_expert(
    registration: ExpertRegistration,
    db: AsyncSession = Depends(get_db),
):
    """Register a new clinical expert for RLHF evaluation."""
    existing = await db.execute(
        select(Expert).where(Expert.username == registration.username)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already registered")

    expert = Expert(
        username=registration.username,
        display_name=registration.display_name,
        email=registration.email,
        subspecialty=registration.subspecialty,
        institution=registration.institution,
        years_experience=registration.years_experience,
        patient_categories=registration.patient_categories,
    )
    db.add(expert)
    await db.commit()
    await db.refresh(expert)

    return ExpertResponse(
        id=expert.id,
        username=expert.username,
        display_name=expert.display_name,
        subspecialty=expert.subspecialty,
        institution=expert.institution,
        patient_categories=expert.patient_categories or [],
        is_active=bool(expert.is_active),
    )


@router.get("/", response_model=list[ExpertResponse])
async def list_experts(db: AsyncSession = Depends(get_db)):
    """List all registered experts."""
    result = await db.execute(select(Expert).where(Expert.is_active == 1))
    experts = result.scalars().all()
    return [
        ExpertResponse(
            id=e.id,
            username=e.username,
            display_name=e.display_name,
            subspecialty=e.subspecialty,
            institution=e.institution,
            patient_categories=e.patient_categories or [],
            is_active=bool(e.is_active),
        )
        for e in experts
    ]


@router.get("/match/{patient_category}", response_model=list[ExpertResponse])
async def match_experts(
    patient_category: str,
    db: AsyncSession = Depends(get_db),
):
    """Find experts matching a patient category."""
    result = await db.execute(select(Expert).where(Expert.is_active == 1))
    experts = result.scalars().all()

    matched = [
        e for e in experts
        if patient_category in (e.patient_categories or [])
    ]

    return [
        ExpertResponse(
            id=e.id,
            username=e.username,
            display_name=e.display_name,
            subspecialty=e.subspecialty,
            institution=e.institution,
            patient_categories=e.patient_categories or [],
            is_active=bool(e.is_active),
        )
        for e in matched
    ]
