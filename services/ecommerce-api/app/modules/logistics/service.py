from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import not_found
from app.core.ids import uuid7
from app.models.logistics import DeliveryStaff, Shipment
from app.models.order import Order
from app.modules.logistics.schemas import DeliveryStaffCreateRequest, DeliveryStaffUpdateRequest


def list_delivery_staff(db: Session) -> list[DeliveryStaff]:
    return db.execute(select(DeliveryStaff).order_by(DeliveryStaff.staff_id)).scalars().all()


def create_delivery_staff(db: Session, payload: DeliveryStaffCreateRequest) -> DeliveryStaff:
    staff = DeliveryStaff(
        public_id=uuid7(),
        full_name=payload.full_name,
        phone=payload.phone,
        vehicle_plate=payload.vehicle_plate,
        is_active=True,
    )
    db.add(staff)
    db.flush()
    return staff


def update_delivery_staff(db: Session, staff_id: int, payload: DeliveryStaffUpdateRequest) -> None:
    staff = db.execute(select(DeliveryStaff).where(DeliveryStaff.staff_id == staff_id)).scalar_one_or_none()
    if not staff:
        raise not_found("Không tìm thấy nhân viên giao hàng.")
    if payload.full_name is not None:
        staff.full_name = payload.full_name
    if payload.phone is not None:
        staff.phone = payload.phone
    if payload.vehicle_plate is not None:
        staff.vehicle_plate = payload.vehicle_plate
    if payload.is_active is not None:
        staff.is_active = payload.is_active
    db.flush()


def list_shipments(
    db: Session, status: str | None = None
) -> list[tuple[Shipment, str, str | None, str | None]]:
    stmt = (
        select(
            Shipment,
            Order.order_number,
            DeliveryStaff.full_name,
            DeliveryStaff.phone,
        )
        .join(Order, Order.order_id == Shipment.order_id)
        .outerjoin(DeliveryStaff, DeliveryStaff.staff_id == Shipment.delivery_staff_id)
        .order_by(Shipment.shipment_id.desc())
    )
    if status:
        stmt = stmt.where(Shipment.status == status)
    return db.execute(stmt).all()


def get_shipment_by_order_number(
    db: Session, order_number: str
) -> tuple[Shipment, str, str | None, str | None]:
    stmt = (
        select(
            Shipment,
            Order.order_number,
            DeliveryStaff.full_name,
            DeliveryStaff.phone,
        )
        .join(Order, Order.order_id == Shipment.order_id)
        .outerjoin(DeliveryStaff, DeliveryStaff.staff_id == Shipment.delivery_staff_id)
        .where(Order.order_number == order_number)
    )
    row = db.execute(stmt).first()
    if not row:
        raise not_found("Không tìm thấy thông tin giao hàng cho đơn hàng này.")
    return row
