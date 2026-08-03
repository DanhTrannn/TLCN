"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { OrderStatusBadge, orderStatusShortLabel } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd } from "@/lib/api";
import { getAdminCommerceOrder, type CommerceOrderDetail } from "@/lib/commerce";
import { formatVietnamDateTime } from "@/lib/datetime";

export default function AdminOrderDetailPage() {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const [order, setOrder] = useState<CommerceOrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderNumber) return;
    getAdminCommerceOrder(orderNumber).then(setOrder).catch((requestError) => setError(requestError instanceof ApiError ? requestError.message : "Không tải được đơn hàng"));
  }, [orderNumber]);

  if (error) return <div className="feedback-error">{error}</div>;
  if (!order) return <div className="h-80 animate-pulse rounded-2xl bg-sand/60" />;

  return (
    <section>
      <Link className="button-ghost -ml-3" href="/admin/orders"><Icon className="rotate-180" name="arrow-right" size={17} />Danh sách đơn</Link>
      <header className="mt-3 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="eyebrow">Order detail</p><h1 className="admin-heading mt-2 break-all">{order.order_number}</h1><p className="mt-2 text-sm text-muted">Tạo lúc {formatVietnamDateTime(order.created_at)}</p></div>
        <OrderStatusBadge status={order.status} />
      </header>

      <div className="mt-6 grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-5">
          <article className="admin-panel">
            <div className="flex items-center justify-between border-b border-line pb-4"><div className="flex items-center gap-3"><Icon className="text-moss" name="package" /><h2 className="font-semibold">Sản phẩm</h2></div><span className="text-sm text-muted">{order.items.length} dòng</span></div>
            <ul className="mt-2 divide-y divide-line">
              {order.items.map((item) => <li className="flex items-center justify-between gap-4 py-4 text-sm" key={item.public_id}><span className="flex min-w-0 items-center gap-3"><span className="relative flex h-14 w-14 shrink-0 items-center justify-center overflow-hidden rounded-xl bg-sand text-muted">{item.image_url ? <Image alt={item.product_name} className="object-cover" fill sizes="56px" src={item.image_url} /> : <Icon name="package" size={18} />}</span><span className="min-w-0"><strong className="font-semibold">{item.product_name}</strong><span className="mt-1 block text-xs text-muted">{item.sku} · {item.size_code}/{item.color_code} · SL {item.quantity}</span></span></span><span className="shrink-0 font-semibold">{formatVnd(item.line_total_vnd)}</span></li>)}
            </ul>
            <dl className="ml-auto mt-3 max-w-sm space-y-2 border-t border-line pt-4 text-sm"><div className="flex justify-between"><dt className="text-muted">Tạm tính</dt><dd>{formatVnd(order.subtotal_vnd)}</dd></div>{order.discount_amount_vnd > 0 ? <div className="flex justify-between text-success"><dt>Giảm giá {order.coupon_code}</dt><dd>−{formatVnd(order.discount_amount_vnd)}</dd></div> : null}<div className="flex justify-between"><dt className="text-muted">Vận chuyển</dt><dd>{formatVnd(order.shipping_fee_vnd)}</dd></div><div className="flex justify-between border-t border-line pt-3 text-lg font-semibold"><dt>Tổng</dt><dd>{formatVnd(order.total_vnd)}</dd></div></dl>
          </article>

          <article className="admin-panel">
            <div className="flex items-center gap-3"><Icon className="text-moss" name="receipt" /><h2 className="font-semibold">Lịch sử trạng thái</h2></div>
            <ol className="mt-5 space-y-4">
              {order.status_history.map((history, index) => <li className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-3" key={`${history.transitioned_at}-${index}`}><span className="mt-1 flex h-6 w-6 items-center justify-center rounded-full bg-moss text-white"><Icon name="check" size={13} /></span><div className="rounded-xl border border-line bg-paper p-3"><div className="flex flex-wrap justify-between gap-2"><strong className="text-sm">{orderStatusShortLabel(history.to_status)}</strong><time className="text-xs text-muted">{formatVietnamDateTime(history.transitioned_at)}</time></div>{history.reason ? <p className="mt-2 text-sm text-muted">{history.reason}</p> : null}</div></li>)}
            </ol>
          </article>
        </div>

        <aside className="space-y-5 xl:sticky xl:top-24">
          <article className="admin-panel"><div className="flex items-center gap-3"><Icon className="text-moss" name="truck" /><h2 className="font-semibold">Giao hàng</h2></div><p className="mt-4 font-semibold">{order.receiver_name}</p><p className="mt-1 text-sm text-muted">{order.receiver_phone}</p><p className="mt-3 text-sm leading-6 text-muted">{order.shipping_address_text}</p></article>
          {order.payment ? <article className="admin-panel"><div className="flex items-center gap-3"><Icon className="text-moss" name="shield" /><h2 className="font-semibold">Thanh toán</h2></div><p className="mt-4 break-all text-sm font-semibold">{order.payment.payment_reference}</p><p className="mt-2 text-sm text-muted">{order.payment.status} · {formatVnd(order.payment.amount_vnd)}</p>{order.refund ? <p className="feedback-error mt-4">Đã hoàn {formatVnd(order.refund.amount_vnd)} · {order.refund.reason}</p> : null}</article> : null}
        </aside>
      </div>
    </section>
  );
}
