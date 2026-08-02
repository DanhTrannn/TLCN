"use client";

import { useCallback, useEffect, useState } from "react";

import { AdminModal } from "@/components/admin/AdminModal";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import {
  createAdminCoupon,
  getAdminCoupons,
  setAdminCouponActive,
  type AdminCoupon,
} from "@/lib/commerce";
import {
  formatVietnamDateTime,
  toVietnamLocalInputValue,
  vietnamLocalInputToUtcIso,
} from "@/lib/datetime";

export default function AdminCouponsPage() {
  const now = new Date();
  const [coupons, setCoupons] = useState<AdminCoupon[]>([]);
  const [code, setCode] = useState("");
  const [discountType, setDiscountType] = useState<"percentage" | "fixed_amount">("percentage");
  const [discountValue, setDiscountValue] = useState("10");
  const [minimumSubtotal, setMinimumSubtotal] = useState("0");
  const [startsAt, setStartsAt] = useState(toVietnamLocalInputValue(now));
  const [endsAt, setEndsAt] = useState(toVietnamLocalInputValue(new Date(now.getTime() + 30 * 86_400_000)));
  const [totalLimit, setTotalLimit] = useState("");
  const [customerLimit, setCustomerLimit] = useState("1");
  const [busy, setBusy] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setCoupons(await getAdminCoupons());
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không tải được coupon");
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function createCoupon(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setCreateError(null);
    try {
      await createAdminCoupon({
        code: code.trim().toUpperCase(),
        discount_type: discountType,
        discount_value: Number(discountValue),
        minimum_subtotal_vnd: Number(minimumSubtotal),
        starts_at: vietnamLocalInputToUtcIso(startsAt),
        ends_at: vietnamLocalInputToUtcIso(endsAt),
        total_usage_limit: totalLimit ? Number(totalLimit) : null,
        per_customer_usage_limit: customerLimit ? Number(customerLimit) : null,
      });
      setCode("");
      await load();
      setCreateOpen(false);
    } catch (requestError) {
      setCreateError(requestError instanceof ApiError ? requestError.message : "Không tạo được coupon");
    } finally {
      setBusy(false);
    }
  }

  async function toggle(coupon: AdminCoupon) {
    setBusy(true);
    try {
      await setAdminCouponActive(coupon.public_id, !coupon.is_active);
      await load();
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không cập nhật được coupon");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="eyebrow">Promotions</p>
          <h1 className="admin-heading mt-2">Quản lý mã giảm giá</h1>
          <p className="mt-2 text-sm leading-6 text-muted">Mỗi đơn tối đa một coupon; giá trị giảm được snapshot tại checkout.</p>
        </div>
        <button
          className="button-primary shrink-0"
          onClick={() => {
            setCreateError(null);
            setCreateOpen(true);
          }}
          type="button"
        >
          <Icon name="plus" size={17} />
          Thêm mã giảm giá
        </button>
      </header>

      <AdminModal
        busy={busy}
        description="Thiết lập mức giảm, thời gian hiệu lực và giới hạn sử dụng."
        onClose={() => setCreateOpen(false)}
        open={createOpen}
        title="Thêm mã giảm giá"
      >
        <form className="grid gap-4 md:grid-cols-2" onSubmit={createCoupon}>
          <label className="field-label" htmlFor="coupon-code-admin">Mã<input className="admin-input uppercase" id="coupon-code-admin" required value={code} onChange={(event) => setCode(event.target.value)} /></label>
          <label className="field-label" htmlFor="coupon-type">Loại<select className="admin-input" id="coupon-type" value={discountType} onChange={(event) => setDiscountType(event.target.value as "percentage" | "fixed_amount")}><option value="percentage">Phần trăm</option><option value="fixed_amount">Số tiền cố định</option></select></label>
          <label className="field-label" htmlFor="coupon-value">Giá trị<input className="admin-input" id="coupon-value" min={1} required type="number" value={discountValue} onChange={(event) => setDiscountValue(event.target.value)} /></label>
          <label className="field-label" htmlFor="coupon-minimum">Đơn tối thiểu<input className="admin-input" id="coupon-minimum" min={0} required type="number" value={minimumSubtotal} onChange={(event) => setMinimumSubtotal(event.target.value)} /></label>
          <label className="field-label" htmlFor="coupon-start">Bắt đầu<input className="admin-input" id="coupon-start" required type="datetime-local" value={startsAt} onChange={(event) => setStartsAt(event.target.value)} /></label>
          <label className="field-label" htmlFor="coupon-end">Kết thúc<input className="admin-input" id="coupon-end" required type="datetime-local" value={endsAt} onChange={(event) => setEndsAt(event.target.value)} /></label>
          <label className="field-label" htmlFor="coupon-total-limit">Tổng lượt sử dụng<input className="admin-input" id="coupon-total-limit" min={1} placeholder="Không giới hạn" type="number" value={totalLimit} onChange={(event) => setTotalLimit(event.target.value)} /></label>
          <label className="field-label" htmlFor="coupon-customer-limit">Lượt mỗi khách<input className="admin-input" id="coupon-customer-limit" min={1} type="number" value={customerLimit} onChange={(event) => setCustomerLimit(event.target.value)} /></label>
          {createError ? <div className="feedback-error md:col-span-2">{createError}</div> : null}
          <div className="flex flex-col-reverse gap-2 border-t border-line pt-5 md:col-span-2 sm:flex-row sm:justify-end">
            <button className="button-secondary" disabled={busy} onClick={() => setCreateOpen(false)} type="button">Hủy</button>
            <button className="button-primary" disabled={busy} type="submit"><Icon name="ticket" size={17} />{busy ? "Đang lưu…" : "Tạo mã giảm giá"}</button>
          </div>
        </form>
      </AdminModal>

      {error ? <div className="feedback-error mt-5">{error}</div> : null}
      <div className="admin-table-shell mt-6">
        <table>
          <thead><tr><th>Mã</th><th>Mức giảm</th><th>Hiệu lực</th><th>Sử dụng</th><th><span className="sr-only">Thao tác</span></th></tr></thead>
          <tbody>
            {coupons.map((coupon) => (
              <tr key={coupon.public_id}>
                <td><p className="font-semibold tracking-wide">{coupon.code}</p><span className={`mt-1 inline-flex rounded-full px-2.5 py-1 text-xs font-semibold ${coupon.is_active ? "bg-success/10 text-success" : "bg-muted/10 text-muted"}`}>{coupon.is_active ? "Đang bật" : "Đã tắt"}</span></td>
                <td><p className="font-semibold">{coupon.discount_type === "percentage" ? `${coupon.discount_value}%` : formatVnd(coupon.discount_value)}</p><p className="mt-1 text-xs text-muted">Đơn từ {formatVnd(coupon.minimum_subtotal_vnd)}</p></td>
                <td className="text-xs leading-5 text-muted">{formatVietnamDateTime(coupon.starts_at)}<br />đến {formatVietnamDateTime(coupon.ends_at)}</td>
                <td><p className="font-semibold">{coupon.used_count}{coupon.total_usage_limit ? ` / ${coupon.total_usage_limit}` : ""}</p><p className="mt-1 text-xs text-muted">Mỗi khách: {coupon.per_customer_usage_limit ?? "Không giới hạn"}</p></td>
                <td className="text-right"><button className={coupon.is_active ? "button-secondary px-4 text-danger" : "button-secondary px-4 text-success"} disabled={busy} onClick={() => void toggle(coupon)} type="button">{coupon.is_active ? "Tắt coupon" : "Bật coupon"}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
        {coupons.length === 0 ? <div className="p-10 text-center"><Icon className="mx-auto text-moss" name="ticket" size={24} /><p className="mt-3 text-muted">Chưa có coupon.</p></div> : null}
      </div>
    </section>
  );
}
