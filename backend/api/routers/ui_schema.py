from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.deps import get_ui_cache_store
from backend.core.config import Settings, get_settings
from backend.core.models import UISchemaRequest, UISchemaResponse

router = APIRouter(prefix="/ui-schema", tags=["ui-schema"])


@router.post("", response_model=UISchemaResponse)
async def generate_ui_schema_endpoint(
    request: UISchemaRequest,
    settings: Annotated[Settings, Depends(get_settings)],
    ui_cache_store=Depends(get_ui_cache_store),
):
    from backend.rag.ui_generator import generate_ui_schema_from_data

    ui_schema = await generate_ui_schema_from_data(
        data=request.data,
        intent=request.intent,
        settings=settings,
    )
    return UISchemaResponse(ui_schema=ui_schema)
