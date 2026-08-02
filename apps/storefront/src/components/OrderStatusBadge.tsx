const STATUS_PRESENTATION: Record<string, { label: string; classes: string }> = {
  paid: {
    label: "Đã thanh toán · chờ xác nhận",
    classes: "border-warning/25 bg-warning/10 text-warning",
  },
  payment_failed: {
    label: "Thanh toán thất bại",
    classes: "border-danger/25 bg-danger/10 text-danger",
  },
  confirmed: {
    label: "Đã xác nhận",
    classes: "border-success/20 bg-success/10 text-success",
  },
  completed: {
    label: "Hoàn tất",
    classes: "border-ink bg-ink text-paper",
  },
  cancelled: {
    label: "Đã hủy",
    classes: "border-line bg-paper text-muted",
  },
};

const STATUS_SHORT_LABELS: Record<string, string> = {
  paid: "Đã thanh toán",
  payment_failed: "Thanh toán thất bại",
  confirmed: "Đã xác nhận",
  completed: "Hoàn tất",
  cancelled: "Đã hủy",
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
