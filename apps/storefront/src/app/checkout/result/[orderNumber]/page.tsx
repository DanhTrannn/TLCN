"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import { formatVnd, getOrder, type OrderDetail } from "@/lib/api";

export default function CheckoutResultPage() {
  const params = useParams<{ orderNumber: string }>();
  const orderNumber = params.orderNumber;
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!orderNumber) return;
    getOrder(orderNumber)
      .then(setOrder)
      .catch(() => setError("Không tìm thấy đơn hàng"));
  }, [orderNumber]);

  if (error) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-14">
        <p className="text-accent">{error}</p>
      </main>
    );
  }

  if (!order) {
    return (
      <main className="mx-auto max-w-2xl px-6 py-14">
        <p className="text-ink/60">Đang tải…</p>
      </main>
    );
  }

  const paid = order.status === "paid" || order.status === "completed";

  return (
    <main className="mx-auto max-w-2xl px-6 py-14 text-center">
      <div
        className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full text-2xl ${
          paid ? "bg-moss/15 text-moss" : "bg-accent/15 text-accent"
        }`}
      >
        {paid ? "✓" : "✕"}
      </div>
      <h1 className="mt-6 text-3xl font-semibold">
        {paid ? "Thanh toán thành công" : "Thanh toán thất bại"}
      </h1>
      <p className="mt-2 text-ink/65">Mã đơn hàng: {order.order_number}</p>
      {!paid && order.payment?.failure_code ? (
        <p className="mt-1 text-sm text-accent">Lý do: {order.payment.failure_code}</p>
      ) : null}
      <p className="mt-4 text-xl font-medium">{formatVnd(order.total_vnd)}</p>

      <div className="mt-8 flex justify-center gap-4">
        <Link className="rounded-full border border-ink/20 px-6 py-2" href={`/orders/${order.order_number}`}>
          Xem chi tiết
        </Link>
        <Link className="rounded-full bg-ink px-6 py-2 text-paper" href="/products">
          Tiếp tục mua sắm
        </Link>
      </div>
    </main>
  );
}
