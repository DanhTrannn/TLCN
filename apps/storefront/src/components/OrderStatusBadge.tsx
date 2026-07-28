const STATUS_PRESENTATION: Record<string, { label: string; classes: string }> = {
  paid: {
    label: "Đã thanh toán",
    classes: "border-moss/20 bg-moss/10 text-moss",
  },
  payment_failed: {
    label: "Thanh toán thất bại",
    classes: "border-accent/25 bg-accent/10 text-accent",
  },
  completed: {
    label: "Hoàn tất",
    classes: "border-ink bg-ink text-paper",
  },
};

export function orderStatusLabel(status: string): string {
  return STATUS_PRESENTATION[status]?.label ?? status;
}

export function OrderStatusBadge({ status }: { status: string }) {
  const presentation = STATUS_PRESENTATION[status] ?? {
    label: status,
    classes: "border-ink/15 bg-ink/5 text-ink/70",
  };

  return (
    <span
      className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-semibold ${presentation.classes}`}
    >
      {presentation.label}
    </span>
  );
}
