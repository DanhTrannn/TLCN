"use client";

import { Icon } from "@/components/ui/Icon";
import { formatVnd } from "@/lib/api";

interface FreeShippingBarProps {
  subtotalVnd: number;
  thresholdVnd?: number;
}

export function FreeShippingBar({
  subtotalVnd,
  thresholdVnd = 500000,
}: FreeShippingBarProps) {
  const remaining = Math.max(0, thresholdVnd - subtotalVnd);
  const percentage = Math.min(100, Math.max(0, Math.round((subtotalVnd / thresholdVnd) * 100)));
  const isQualified = remaining === 0;

  return (
    <div className="rounded-2xl border border-line bg-paper/80 p-4 shadow-sm">
      <div className="flex items-center justify-between gap-3 text-xs sm:text-sm">
        <div className="flex items-center gap-2">
          <span
            className={`flex h-7 w-7 items-center justify-center rounded-full ${
              isQualified
                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                : "bg-accent/15 text-accent"
            }`}
          >
            <Icon name={isQualified ? "check" : "truck"} size={15} />
          </span>
          {isQualified ? (
            <span className="font-semibold text-emerald-700 dark:text-emerald-400">
              Đơn hàng của bạn đã đủ điều kiện <strong>Miễn phí vận chuyển toàn quốc</strong>!
            </span>
          ) : (
            <span className="text-ink">
              Mua thêm <strong className="text-accent">{formatVnd(remaining)}</strong> để được{" "}
              <strong>Freeship</strong> (từ {formatVnd(thresholdVnd)})
            </span>
          )}
        </div>
        <span className="font-semibold text-xs text-muted">{percentage}%</span>
      </div>

      <div className="mt-3 h-2 w-full overflow-hidden rounded-full bg-line/80">
        <div
          className={`h-full rounded-full transition-all duration-500 ${
            isQualified ? "bg-emerald-500" : "bg-gradient-to-r from-accent to-moss"
          }`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
