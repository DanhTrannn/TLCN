const STATUS_PRESENTATION: Record<string, { label: string; classes: string }> = {
  paid: {
    label: "Đã thanh toán · Chờ xuất kho",
    classes: "border-amber-500/25 bg-amber-500/10 text-amber-600 dark:text-amber-400",
  },
  confirmed: {
    label: "Đã xác nhận · Chờ giao hàng",
    classes: "border-sky-500/25 bg-sky-500/10 text-sky-600 dark:text-sky-400",
  },
  shipping: {
    label: "Đang giao hàng",
    classes: "border-indigo-500/25 bg-indigo-500/10 text-indigo-600 dark:text-indigo-400",
  },
  delivered: {
    label: "Đã giao hàng · Chờ hoàn tất",
    classes: "border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  },
  failed_delivery: {
    label: "Giao thất bại (Boom COD)",
    classes: "border-rose-500/25 bg-rose-500/10 text-rose-600 dark:text-rose-400",
  },
  returned: {
    label: "Đã đổi / trả hàng",
    classes: "border-amber-600/25 bg-amber-600/10 text-amber-700 dark:text-amber-400",
  },
  completed: {
    label: "Hoàn tất",
    classes: "border-slate-500/25 bg-slate-500/10 text-slate-700 dark:text-slate-300",
  },
  cancelled: {
    label: "Đã hủy",
    classes: "border-line bg-paper text-muted",
  },
  payment_failed: {
    label: "Thanh toán thất bại",
    classes: "border-danger/25 bg-danger/10 text-danger",
  },
  pending_payment: {
    label: "Chờ thanh toán",
    classes: "border-warning/25 bg-warning/10 text-warning",
  },
};

const STATUS_SHORT_LABELS: Record<string, string> = {
  paid: "Đã thanh toán",
  confirmed: "Đã xác nhận",
  shipping: "Đang giao hàng",
  delivered: "Đã giao hàng",
  failed_delivery: "Giao thất bại",
  returned: "Đã đổi / trả",
  completed: "Hoàn tất",
  cancelled: "Đã hủy",
  payment_failed: "Thanh toán thất bại",
  pending_payment: "Chờ thanh toán",
};

export function orderStatusLabel(status: string): string {
  return STATUS_PRESENTATION[status]?.label ?? status;
}

export function orderStatusShortLabel(status: string): string {
  return STATUS_SHORT_LABELS[status] ?? orderStatusLabel(status);
}

export function OrderStatusBadge({ status }: { status: string }) {
  const presentation = STATUS_PRESENTATION[status] ?? {
    label: status,
    classes: "border-line bg-paper text-muted",
  };

  return (
    <span className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-semibold ${presentation.classes}`}>
      {presentation.label}
    </span>
  );
}

const SHIPMENT_STATUS_MAP: Record<
  string,
  { label: string; classes: string; dotClass: string }
> = {
  in_transit: {
    label: "Đang giao",
    classes: "border-sky-500/25 bg-sky-500/10 text-sky-700 dark:text-sky-300",
    dotClass: "bg-sky-500",
  },
  delivered: {
    label: "Giao thành công",
    classes: "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
    dotClass: "bg-emerald-500",
  },
  failed: {
    label: "Thất bại",
    classes: "border-rose-500/25 bg-rose-500/10 text-rose-700 dark:text-rose-400",
    dotClass: "bg-rose-500",
  },
};

export function shipmentStatusLabel(status: string): string {
  return SHIPMENT_STATUS_MAP[status]?.label ?? status;
}

export function ShipmentStatusBadge({ status }: { status: string }) {
  const config = SHIPMENT_STATUS_MAP[status] ?? {
    label: status,
    classes: "border-line bg-paper text-muted",
    dotClass: "bg-muted",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${config.classes}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dotClass}`} />
      {config.label}
    </span>
  );
}

