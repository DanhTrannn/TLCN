from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import (
    COUPON_INVALID,
    COUPON_USAGE_LIMIT,
    VALIDATION_ERROR,
    AppError,
    not_found,
)
from app.core.ids import uuid7
from app.db.uow import run_in_transaction
from app.models.promotion import Coupon, CouponRedemption
from app.modules.coupons.schemas import (
    AvailableCouponListResponse,
    AvailableCouponResponse,
    CouponResponse,
    CreateCouponRequest,
)


@dataclass(frozen=True)
class CouponUse:
    coupon: Coupon
    discount_amount_vnd: int


def _utc_naive(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value
    return value.astimezone(UTC).replace(tzinfo=None)


def normalize_coupon_code(code: str) -> str:
    return code.strip().upper()


def calculate_coupon_discount(
    discount_type: str, discount_value: int, subtotal_vnd: int
) -> int:
    if discount_type == "percentage":
        return subtotal_vnd * discount_value // 100
    return min(discount_value, subtotal_vnd)


def resolve_coupon(
    db: Session,
    code: str,
    customer_id: int,
    subtotal_vnd: int,
    now: datetime,
    *,
    for_update: bool,
) -> CouponUse:
    stmt = select(Coupon).where(Coupon.code_normalized == normalize_coupon_code(code))
    if for_update:
        stmt = stmt.with_for_update()
    coupon = db.execute(stmt).scalar_one_or_none()
    if coupon is None or not coupon.is_active:
        raise AppError(COUPON_INVALID, "Mã giảm giá không hợp lệ.", status_code=409)
    if not (coupon.starts_at <= now < coupon.ends_at):
        raise AppError(COUPON_INVALID, "Mã giảm giá chưa có hiệu lực hoặc đã hết hạn.", status_code=409)
    if subtotal_vnd < coupon.minimum_subtotal_vnd:
        raise AppError(
            COUPON_INVALID,
            f"Đơn hàng phải đạt tối thiểu {coupon.minimum_subtotal_vnd}₫.",
            status_code=409,
        )
    if coupon.total_usage_limit is not None and coupon.used_count >= coupon.total_usage_limit:
        raise AppError(COUPON_USAGE_LIMIT, "Mã giảm giá đã hết lượt sử dụng.", status_code=409)
    if coupon.per_customer_usage_limit is not None:
        customer_uses = db.scalar(
            select(func.count())
            .select_from(CouponRedemption)
            .where(
                CouponRedemption.coupon_id == coupon.coupon_id,
                CouponRedemption.customer_id == customer_id,
                CouponRedemption.status == "redeemed",
            )
        )
        if int(customer_uses or 0) >= coupon.per_customer_usage_limit:
            raise AppError(
                COUPON_USAGE_LIMIT,
                "Bạn đã dùng hết lượt của mã giảm giá này.",
                status_code=409,
            )
    discount = calculate_coupon_discount(
        coupon.discount_type, coupon.discount_value, subtotal_vnd
    )
    if discount <= 0:
        raise AppError(COUPON_INVALID, "Mã giảm giá không tạo ra giá trị giảm.", status_code=409)
    return CouponUse(coupon=coupon, discount_amount_vnd=discount)


def list_available_coupons(
    db: Session,
    customer_id: int,
    subtotal_vnd: int,
    now: datetime | None = None,
) -> AvailableCouponListResponse:
    if subtotal_vnd <= 0:
        return AvailableCouponListResponse(subtotal_vnd=subtotal_vnd, items=[])

    effective_now = _utc_naive(now or datetime.now(UTC))
    customer_usage_rows = db.execute(
        select(CouponRedemption.coupon_id, func.count())
        .where(
            CouponRedemption.customer_id == customer_id,
            CouponRedemption.status == "redeemed",
        )
        .group_by(CouponRedemption.coupon_id)
    ).all()
    customer_uses_by_coupon = {
        int(coupon_id): int(uses) for coupon_id, uses in customer_usage_rows
    }
    coupons = (
        db.execute(
            select(Coupon)
            .where(
                Coupon.is_active.is_(True),
                Coupon.starts_at <= effective_now,
                Coupon.ends_at > effective_now,
                Coupon.minimum_subtotal_vnd <= subtotal_vnd,
                or_(
                    Coupon.total_usage_limit.is_(None),
                    Coupon.used_count < Coupon.total_usage_limit,
                ),
            )
            .order_by(Coupon.ends_at, Coupon.coupon_id)
        )
        .scalars()
        .all()
    )

    items: list[AvailableCouponResponse] = []
    for coupon in coupons:
        customer_uses = customer_uses_by_coupon.get(coupon.coupon_id, 0)
        if (
            coupon.per_customer_usage_limit is not None
            and customer_uses >= coupon.per_customer_usage_limit
        ):
            continue
        discount_amount_vnd = calculate_coupon_discount(
            coupon.discount_type,
            coupon.discount_value,
            subtotal_vnd,
        )
        if discount_amount_vnd <= 0:
            continue
        remaining_uses = (
            max(0, coupon.total_usage_limit - coupon.used_count)
            if coupon.total_usage_limit is not None
            else None
        )
        items.append(
            AvailableCouponResponse(
                code=coupon.code_normalized,
                discount_type=coupon.discount_type,
                discount_value=coupon.discount_value,
                minimum_subtotal_vnd=coupon.minimum_subtotal_vnd,
                discount_amount_vnd=discount_amount_vnd,
                ends_at=coupon.ends_at.replace(tzinfo=UTC),
                remaining_uses=remaining_uses,
            )
        )

    items.sort(key=lambda item: (-item.discount_amount_vnd, item.ends_at, item.code))
    return AvailableCouponListResponse(subtotal_vnd=subtotal_vnd, items=items)


def _coupon_response(coupon: Coupon) -> CouponResponse:
    return CouponResponse(
        public_id=str(coupon.public_id),
        code=coupon.code_normalized,
        discount_type=coupon.discount_type,
        discount_value=coupon.discount_value,
        minimum_subtotal_vnd=coupon.minimum_subtotal_vnd,
        starts_at=coupon.starts_at,
        ends_at=coupon.ends_at,
        is_active=coupon.is_active,
        total_usage_limit=coupon.total_usage_limit,
        per_customer_usage_limit=coupon.per_customer_usage_limit,
        used_count=coupon.used_count,
        created_at=coupon.created_at,
        updated_at=coupon.updated_at,
    )


def list_coupons(db: Session) -> list[CouponResponse]:
    rows = db.execute(
        select(Coupon).order_by(Coupon.created_at.desc(), Coupon.coupon_id.desc())
    ).scalars().all()
    return [_coupon_response(coupon) for coupon in rows]


def create_coupon(payload: CreateCouponRequest) -> CouponResponse:
    def _work(db: Session) -> CouponResponse:
        code = normalize_coupon_code(payload.code)
        existing = db.execute(
            select(Coupon).where(Coupon.code_normalized == code).with_for_update()
        ).scalar_one_or_none()
        if existing is not None:
            raise AppError(VALIDATION_ERROR, "Mã coupon đã tồn tại.", status_code=409)
        coupon = Coupon(
            public_id=uuid7(),
            code_normalized=code,
            discount_type=payload.discount_type,
            discount_value=payload.discount_value,
            minimum_subtotal_vnd=payload.minimum_subtotal_vnd,
            starts_at=_utc_naive(payload.starts_at),
            ends_at=_utc_naive(payload.ends_at),
            is_active=True,
            total_usage_limit=payload.total_usage_limit,
            per_customer_usage_limit=payload.per_customer_usage_limit,
            used_count=0,
        )
        db.add(coupon)
        db.flush()
        db.refresh(coupon)
        return _coupon_response(coupon)

    try:
        return run_in_transaction(_work)
    except IntegrityError as error:
        raise AppError(
            VALIDATION_ERROR,
            "Mã coupon đã tồn tại.",
            status_code=409,
        ) from error


def set_coupon_active(public_id, is_active: bool) -> None:
    def _work(db: Session) -> None:
        coupon = db.execute(
            select(Coupon).where(Coupon.public_id == public_id).with_for_update()
        ).scalar_one_or_none()
        if coupon is None:
            raise not_found("Không tìm thấy coupon.")
        coupon.is_active = is_active
        coupon.updated_at = datetime.now(UTC).replace(tzinfo=None)
        db.flush()

    run_in_transaction(_work)
