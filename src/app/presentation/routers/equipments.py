from datetime import date

from fastapi import APIRouter, Depends, Query, status

from app.application.queries import EquipmentFilters
from app.application.services import EquipmentService
from app.domain.enums import EquipmentStatus
from app.presentation.dependencies import get_equipment_service
from app.presentation.schemas import (
    EquipmentAssignmentRequest,
    EquipmentCreateRequest,
    EquipmentHistoryResponse,
    EquipmentListResponse,
    EquipmentMovementResponse,
    EquipmentResponse,
    EquipmentTransferRequest,
    EquipmentUnassignRequest,
    EquipmentUpdateRequest,
)

router = APIRouter(prefix="/equipment", tags=["equipment"])


@router.get("/", response_model=EquipmentListResponse)
async def list_equipments(
    category_id: int | None = Query(None, gt=0),
    assigned_to_employee_id: int | None = Query(None, gt=0),
    status_filter: EquipmentStatus | None = Query(None, alias="status"),
    name: str | None = Query(None),
    inventory_number: str | None = Query(None),
    purchase_date_from: date | None = Query(None),
    purchase_date_to: date | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: EquipmentService = Depends(get_equipment_service),
) -> EquipmentListResponse:
    filters = EquipmentFilters(
        category_id=category_id,
        assigned_to_employee_id=assigned_to_employee_id,
        status=status_filter,
        name=name,
        inventory_number=inventory_number,
        purchase_date_from=purchase_date_from,
        purchase_date_to=purchase_date_to,
        skip=skip,
        limit=limit,
    )
    items, total = await service.list(filters)
    return EquipmentListResponse(
        items=[EquipmentResponse.from_entity(item) for item in items],
        total=total,
        offset=skip,
        limit=limit,
    )


@router.get("/{equipment_id}", response_model=EquipmentResponse)
async def get_equipment(
    equipment_id: int,
    service: EquipmentService = Depends(get_equipment_service),
) -> EquipmentResponse:
    return EquipmentResponse.from_entity(await service.get(equipment_id))


@router.post("/", response_model=EquipmentResponse, status_code=status.HTTP_201_CREATED)
async def create_equipment(
    payload: EquipmentCreateRequest,
    service: EquipmentService = Depends(get_equipment_service),
) -> EquipmentResponse:
    return EquipmentResponse.from_entity(await service.create(payload.to_command()))


@router.put("/{equipment_id}", response_model=EquipmentResponse)
async def update_equipment(
    equipment_id: int,
    payload: EquipmentUpdateRequest,
    service: EquipmentService = Depends(get_equipment_service),
) -> EquipmentResponse:
    return EquipmentResponse.from_entity(await service.update(payload.to_command(equipment_id)))


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_equipment(
    equipment_id: int,
    service: EquipmentService = Depends(get_equipment_service),
) -> None:
    await service.delete(equipment_id)


@router.post("/{equipment_id}/assign", response_model=EquipmentMovementResponse, status_code=status.HTTP_201_CREATED)
async def assign_equipment(
    equipment_id: int,
    payload: EquipmentAssignmentRequest,
    service: EquipmentService = Depends(get_equipment_service),
) -> EquipmentMovementResponse:
    return EquipmentMovementResponse.from_entity(await service.assign(payload.to_command(equipment_id)))


@router.post("/{equipment_id}/transfer", response_model=EquipmentMovementResponse, status_code=status.HTTP_201_CREATED)
async def transfer_equipment(
    equipment_id: int,
    payload: EquipmentTransferRequest,
    service: EquipmentService = Depends(get_equipment_service),
) -> EquipmentMovementResponse:
    return EquipmentMovementResponse.from_entity(await service.transfer(payload.to_command(equipment_id)))


@router.post("/{equipment_id}/unassign", response_model=EquipmentMovementResponse, status_code=status.HTTP_201_CREATED)
async def unassign_equipment(
    equipment_id: int,
    payload: EquipmentUnassignRequest,
    service: EquipmentService = Depends(get_equipment_service),
) -> EquipmentMovementResponse:
    return EquipmentMovementResponse.from_entity(await service.unassign(payload.to_command(equipment_id)))


@router.get("/{equipment_id}/history", response_model=EquipmentHistoryResponse)
async def get_equipment_history(
    equipment_id: int,
    service: EquipmentService = Depends(get_equipment_service),
) -> EquipmentHistoryResponse:
    movements = await service.history(equipment_id)
    return EquipmentHistoryResponse(
        equipment_id=equipment_id,
        movements=[EquipmentMovementResponse.from_entity(item) for item in movements],
    )
