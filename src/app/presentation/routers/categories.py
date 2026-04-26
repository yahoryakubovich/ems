from fastapi import APIRouter, Depends, Query, status

from app.application.services import CategoryService
from app.presentation.dependencies import get_category_service
from app.presentation.schemas import (
    CategoryCreateRequest,
    CategoryListResponse,
    CategoryResponse,
    CategoryUpdateRequest,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=CategoryListResponse)
async def list_categories(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: CategoryService = Depends(get_category_service),
) -> CategoryListResponse:
    items, total = await service.list(skip=skip, limit=limit)
    return CategoryListResponse(
        items=[CategoryResponse.from_entity(item) for item in items],
        total=total,
        offset=skip,
        limit=limit,
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    return CategoryResponse.from_entity(await service.get(category_id))


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreateRequest,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    return CategoryResponse.from_entity(await service.create(payload.to_command()))


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    payload: CategoryUpdateRequest,
    service: CategoryService = Depends(get_category_service),
) -> CategoryResponse:
    return CategoryResponse.from_entity(await service.update(payload.to_command(category_id)))


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
) -> None:
    await service.delete(category_id)
