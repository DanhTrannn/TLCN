from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.deps import get_current_admin, get_db, verify_csrf
from app.models.customer import Customer
from app.modules.logistics.schemas import (
    DeliveryStaffCreateRequest,
    DeliveryStaffResponse,
    DeliveryStaffUpdateRequest,
    ShipmentResponse,
)
from app.modules.logistics.service import (
    create_delivery_staff,
    get_shipment_by_order_number,
    list_delivery_staff,
    list_shipments,
    update_delivery_staff,
)


def _format_uuid(val) -> str:
    if hasattr(val, "hex"):
        return val.hex() if callable(val.hex) else val.hex
    return str(val)


admin_logistics_router = APIRouter(prefix="/admin", tags=["admin-logistics"])
admin_router = admin_logistics_router


@admin_logistics_router.get("/delivery-staff", response_model=list[DeliveryStaffResponse])
def get_staff_list(_: Customer = Depends(get_current_admin), db: Session = Depends(get_db)):
    rows = list_delivery_staff(db)
    return [
        DeliveryStaffResponse(
            staff_id=r.staff_id,
            public_id=_format_uuid(r.public_id),
            full_name=r.full_name,
            phone=r.phone,
            vehicle_plate=r.vehicle_plate,
            is_active=r.is_active,
            created_at=r.created_at,
        )
        for r in rows
    ]


@admin_logistics_router.post("/delivery-staff", response_model=DeliveryStaffResponse, status_code=201)
def add_staff(
    payload: DeliveryStaffCreateRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    staff = create_delivery_staff(db, payload)
    db.commit()
    db.refresh(staff)
    return DeliveryStaffResponse(
        staff_id=staff.staff_id,
        public_id=_format_uuid(staff.public_id),
        full_name=staff.full_name,
        phone=staff.phone,
        vehicle_plate=staff.vehicle_plate,
        is_active=staff.is_active,
        created_at=staff.created_at,
    )


@admin_logistics_router.patch("/delivery-staff/{staff_id}", status_code=204)
def patch_staff(
    staff_id: int,
    payload: DeliveryStaffUpdateRequest,
    _: Customer = Depends(get_current_admin),
    __: None = Depends(verify_csrf),
    db: Session = Depends(get_db),
):
    update_delivery_staff(db, staff_id, payload)
    db.commit()
    return Response(status_code=204)


@admin_logistics_router.get("/shipments", response_model=list[ShipmentResponse])
def get_shipments(
    status: str | None = None,
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    rows = list_shipments(db, status)
    return [
        ShipmentResponse(
            shipment_id=shipment.shipment_id,
            shipment_code=shipment.shipment_code,
            order_id=shipment.order_id,
            order_number=order_number,
            delivery_staff_id=shipment.delivery_staff_id,
            delivery_staff_name=staff_name,
            delivery_staff_phone=staff_phone,
            status=shipment.status,
            attempt_count=shipment.attempt_count,
            cod_amount_vnd=shipment.cod_amount_vnd,
            cod_collected_vnd=shipment.cod_collected_vnd,
            dispatched_at=shipment.dispatched_at,
            delivered_at=shipment.delivered_at,
            failed_at=shipment.failed_at,
            failure_reason=shipment.failure_reason,
            notes=shipment.notes,
        )
        for shipment, order_number, staff_name, staff_phone in rows
    ]


@admin_logistics_router.get("/shipments/{order_number}", response_model=ShipmentResponse)
def get_shipment_detail(
    order_number: str,
    _: Customer = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    shipment, ord_num, staff_name, staff_phone = get_shipment_by_order_number(db, order_number)
    return ShipmentResponse(
        shipment_id=shipment.shipment_id,
        shipment_code=shipment.shipment_code,
        order_id=shipment.order_id,
        order_number=ord_num,
        delivery_staff_id=shipment.delivery_staff_id,
        delivery_staff_name=staff_name,
        delivery_staff_phone=staff_phone,
        status=shipment.status,
        attempt_count=shipment.attempt_count,
        cod_amount_vnd=shipment.cod_amount_vnd,
        cod_collected_vnd=shipment.cod_collected_vnd,
        dispatched_at=shipment.dispatched_at,
        delivered_at=shipment.delivered_at,
        failed_at=shipment.failed_at,
        failure_reason=shipment.failure_reason,
        notes=shipment.notes,
    )
