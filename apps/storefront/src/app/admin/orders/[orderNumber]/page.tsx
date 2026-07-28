"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError, formatVnd, getAdminOrder, type OrderDetail } from "@/lib/api";

const labels: Record<string, string> = { paid: "Đã thanh toán", payment_failed: "Thanh toán lỗi", completed: "Hoàn tất" };

export default function AdminOrderDetailPage() {
  const { orderNumber } = useParams<{ orderNumber: string }>();
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderNumber) return;
    getAdminOrder(orderNumber).then(setOrder).catch((err) => setError(err instanceof ApiError ? err.message : "Không tải được đơn hàng"));
  }, [orderNumber]);

  if (error) return <p className="text-accent">{error}</p>;
  if (!order) return <p className="text-ink/60">Đang tải…</p>;

  return (
    <section className="max-w-4xl">
      <Link className="text-sm text-ink/55 hover:text-accent" href="/admin/orders">← Danh sách đơn</Link>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-3"><div><h2 className="text-2xl font-semibold">{order.order_number}</h2><p className="mt-1 text-sm text-ink/55">{new Date(order.created_at).toLocaleString("vi-VN")}</p></div><span className="rounded-full bg-ink/10 px-4 py-2 text-sm">{labels[order.status] ?? order.status}</span></div>
      <div className="mt-6 grid gap-5 md:grid-cols-[1fr_18rem]">
        <div className="rounded-3xl border border-ink/10 bg-white/70 p-5"><h3 className="font-semibold">Sản phẩm</h3><ul className="mt-3 divide-y divide-ink/10">{order.items.map((item) => <li className="flex justify-between gap-4 py-3 text-sm" key={item.sku}><span>{item.product_name}<span className="block text-xs text-ink/50">{item.sku} · {item.size_code}/{item.color_code} × {item.quantity}</span></span><span>{formatVnd(item.line_total_vnd)}</span></li>)}</ul><div className="mt-3 border-t border-ink/10 pt-3 text-right text-sm"><p>Tạm tính: {formatVnd(order.subtotal_vnd)}</p><p>Vận chuyển: {formatVnd(order.shipping_fee_vnd)}</p><p className="mt-1 text-lg font-semibold">Tổng: {formatVnd(order.total_vnd)}</p></div></div>
        <aside className="space-y-5"><div className="rounded-3xl border border-ink/10 bg-white/70 p-5"><h3 className="font-semibold">Giao hàng</h3><p className="mt-3 text-sm">{order.receiver_name}</p><p className="text-sm text-ink/60">{order.receiver_phone}</p><p className="mt-2 text-sm text-ink/60">{order.shipping_address_text}</p></div>{order.payment ? <div className="rounded-3xl border border-ink/10 bg-white/70 p-5"><h3 className="font-semibold">Thanh toán</h3><p className="mt-3 text-sm">{order.payment.payment_reference}</p><p className="text-sm text-ink/60">{order.payment.status} · {formatVnd(order.payment.amount_vnd)}</p></div> : null}</aside>
      </div>
    </section>
  );
}
