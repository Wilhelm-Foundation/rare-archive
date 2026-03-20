"""Case library endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.database import Case, get_db

router = APIRouter()


class CaseCreate(BaseModel):
    case_id: str
    category: str = "general"
    vignette: str
    known_diagnosis: str | None = None
    difficulty: str = "medium"
    source: str | None = None
    metadata: dict | None = None


class CaseResponse(BaseModel):
    id: int
    case_id: str
    category: str
    vignette: str
    known_diagnosis: str | None
    difficulty: str
    source: str | None


class CaseBatchCreate(BaseModel):
    cases: list[CaseCreate]


@router.post("/create", response_model=CaseResponse)
async def create_case(
    case: CaseCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a clinical case to the library."""
    existing = await db.execute(
        select(Case).where(Case.case_id == case.case_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Case ID already exists")

    db_case = Case(
        case_id=case.case_id,
        category=case.category,
        vignette=case.vignette,
        known_diagnosis=case.known_diagnosis,
        difficulty=case.difficulty,
        source=case.source,
        metadata_=case.metadata or {},
    )
    db.add(db_case)
    await db.commit()
    await db.refresh(db_case)

    return CaseResponse(
        id=db_case.id,
        case_id=db_case.case_id,
        category=db_case.category,
        vignette=db_case.vignette,
        known_diagnosis=db_case.known_diagnosis,
        difficulty=db_case.difficulty,
        source=db_case.source,
    )


@router.post("/batch", response_model=dict)
async def batch_create_cases(
    batch: CaseBatchCreate,
    db: AsyncSession = Depends(get_db),
):
    """Batch-insert cases. Skips duplicates."""
    created = 0
    skipped = 0
    for case in batch.cases:
        existing = await db.execute(
            select(Case).where(Case.case_id == case.case_id)
        )
        if existing.scalar_one_or_none():
            skipped += 1
            continue
        db.add(Case(
            case_id=case.case_id,
            category=case.category,
            vignette=case.vignette,
            known_diagnosis=case.known_diagnosis,
            difficulty=case.difficulty,
            source=case.source,
            metadata_=case.metadata or {},
        ))
        created += 1
    await db.commit()
    return {"created": created, "skipped": skipped}


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Retrieve a case by ID."""
    result = await db.execute(
        select(Case).where(Case.case_id == case_id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return CaseResponse(
        id=case.id,
        case_id=case.case_id,
        category=case.category,
        vignette=case.vignette,
        known_diagnosis=case.known_diagnosis,
        difficulty=case.difficulty,
        source=case.source,
    )


@router.get("/random/pick", response_model=CaseResponse)
async def random_case(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get a random case, optionally filtered by category."""
    query = select(Case)
    if category:
        query = query.where(Case.category == category)
    query = query.order_by(func.random()).limit(1)

    result = await db.execute(query)
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="No cases found")

    return CaseResponse(
        id=case.id,
        case_id=case.case_id,
        category=case.category,
        vignette=case.vignette,
        known_diagnosis=case.known_diagnosis,
        difficulty=case.difficulty,
        source=case.source,
    )


@router.get("/", response_model=dict)
async def list_cases(
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List cases with pagination."""
    query = select(Case)
    if category:
        query = query.where(Case.category == category)

    # Count
    count_q = select(func.count(Case.id))
    if category:
        count_q = count_q.where(Case.category == category)
    total = (await db.execute(count_q)).scalar()

    query = query.order_by(Case.id).offset(offset).limit(limit)
    result = await db.execute(query)
    cases = result.scalars().all()

    return {
        "total": total,
        "cases": [
            CaseResponse(
                id=c.id,
                case_id=c.case_id,
                category=c.category,
                vignette=c.vignette[:200] + "..." if len(c.vignette) > 200 else c.vignette,
                known_diagnosis=c.known_diagnosis,
                difficulty=c.difficulty,
                source=c.source,
            )
            for c in cases
        ],
    }
