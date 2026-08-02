"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { formatVnd, getOrder, type OrderDetail } from "@/lib/api";

export default function CheckoutResultPage() {
  const params = useParams<{ orderNumber: string }>();
  const orderNumber = params.orderNumber;
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderNumber) return;
    getOrder(orderNumber).then(setOrder).catch(() => setError("Không tìm thấy đơn hàng"));
  }, [orderNumber]);

  if (error) return <main className="page-shell"><div className="feedback-error">{error}</div></main>;
  if (!order) return <main className="page-shell"><div className="surface-card h-72 animate-pulse" /></main>;

  const paid = order.status === "paid" || order.status === "confirmed" || order.status === "completed";

  return (
    <main className="mx-auto max-w-3xl px-5 py-12 sm:px-6 sm:py-16">
      <section className="surface-card overflow-hidden text-center">
        <div className={`px-6 py-10 sm:px-10 ${paid ? "bg-success/[0.06]" : "bg-danger/[0.06]"}`}>
          <span className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full ${paid ? "bg-success text-white" : "bg-danger text-white"}`}>
            <Icon name={paid ? "check" : "close"} size={28} />
          </span>
          <p className="eyebrow mt-6">Kết quả checkout</p>
          <h1 className="mt-3 font-serif text-4xl sm:text-5xl">{paid ? "Thanh toán thành công" : "Thanh toán chưa thành công"}</h1>
          <p className="mt-3 text-muted">Mã đơn hàng <strong className="text-ink">{order.order_number}</strong></p>
          {!paid && order.payment?.failure_code ? <p className="feedback-error mx-auto mt-5 max-w-lg">Lý do: {order.payment.failure_code}</p> : null}
        </div>
        <div className="border-t border-line p-6 sm:p-8">
          <p className="text-sm text-muted">Tổng thanh toán</p>
          <p className="mt-1 text-3xl font-semibold">{formatVnd(order.total_vnd)}</p>
          <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
            <Link className="button-secondary" href={`/orders/${order.order_number}`}>Xem chi tiết <Icon name="receipt" size={17} /></Link>
            <Link className="button-primary" href="/products">Tiếp tục mua sắm <Icon name="arrow-right" size={17} /></Link>
          </div>
        </div>
      </section>
    </main>
  );
}
