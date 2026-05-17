from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_record_store
from backend.core.models import RecordResponse

router = APIRouter(prefix="/records", tags=["records"])


@router.get("/{record_id}", response_model=RecordResponse)
async def get_record(record_id: str, record_store=Depends(get_record_store)):
    record = await record_store.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Record {record_id!r} not found")
    return RecordResponse(**record)
