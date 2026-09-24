"use client";

import { Icon, type IconName } from "@/components/ui/Icon";
import { formatVnd } from "@/lib/api";

export interface RewardTier {
  id: "freeship" | "voucher" | "gift";
  thresholdVnd: number;
  label: string;
  shortLabel: string;
  icon: IconName;
  couponCode?: string;
  rewardText: string;
}

export const REWARD_TIERS: RewardTier[] = [
  {
    id: "freeship",
    thresholdVnd: 500000,
    label: "Miễn phí vận chuyển",
    shortLabel: "Freeship",
    icon: "truck",
    rewardText: "Đã miễn phí giao hàng",
  },
  {
    id: "voucher",
    thresholdVnd: 800000,
    label: "Voucher giảm 50.000₫",
    shortLabel: "Voucher 50K",
    icon: "ticket",
    couponCode: "DKVIP50",
    rewardText: "Mở khóa Voucher 50K",
  },
  {
    id: "gift",
    thresholdVnd: 1200000,
    label: "Tặng Túi Tote Canvas D&K",
    shortLabel: "Túi Tote Signature",
    icon: "sparkles",
    rewardText: "Tặng Túi Tote Signature",
  },
];

interface TieredRewardsBarProps {
  subtotalVnd: number;
  appliedCouponCode?: string | null;
  onApplyCoupon?: (code: string) => void;
}

export function TieredRewardsBar({
  subtotalVnd,
  appliedCouponCode,
  onApplyCoupon,
}: TieredRewardsBarProps) {
  const maxThreshold = REWARD_TIERS[REWARD_TIERS.length - 1].thresholdVnd;
  const percentage = Math.min(100, Math.max(0, Math.round((subtotalVnd / maxThreshold) * 100)));

  const nextTier = REWARD_TIERS.find((t) => subtotalVnd < t.thresholdVnd);
  const allUnlocked = !nextTier;

  return (
    <section
      aria-label="Thanh tiến độ ưu đãi giỏ hàng"
      className="rounded-2xl border border-line bg-paper/90 p-4 sm:p-5 shadow-sm transition-all"
    >
      {/* Top Banner Status */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5">
        <div className="flex items-center gap-2.5">
          <span
            className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-colors ${
              allUnlocked
                ? "bg-emerald-500 text-white shadow-sm"
                : subtotalVnd >= REWARD_TIERS[0].thresholdVnd
                ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400"
                : "bg-accent/15 text-accent"
            }`}
          >
            <Icon
              name={allUnlocked ? "check" : subtotalVnd >= REWARD_TIERS[0].thresholdVnd ? "truck" : "sparkles"}
              size={16}
            />
          </span>

          <div className="text-xs sm:text-sm">
            {allUnlocked ? (
              <p className="font-semibold text-emerald-700 dark:text-emerald-400">
                🎉 Tuyệt vời! Bạn đã mở khóa toàn bộ đặc quyền (Freeship + Voucher 50K + Quà tặng Túi Tote)!
              </p>
            ) : nextTier ? (
              <p className="text-ink">
                Mua thêm{" "}
                <strong className="text-accent font-semibold">
                  {formatVnd(nextTier.thresholdVnd - subtotalVnd)}
                </strong>{" "}
                để nhận <strong>{nextTier.label}</strong> (từ {formatVnd(nextTier.thresholdVnd)})
              </p>
            ) : null}
          </div>
        </div>

        <div className="flex items-center justify-between sm:justify-end gap-2 text-xs">
          <span className="font-medium text-muted">
            Đã đạt <strong className="text-ink font-semibold">{formatVnd(subtotalVnd)}</strong>
          </span>
          <span className="rounded-full bg-surface px-2.5 py-0.5 font-semibold tabular-nums text-ink">
            {percentage}%
          </span>
        </div>
      </div>

      {/* Progress Bar with Checkpoints */}
      <div className="relative mt-6 mb-8 px-2 sm:px-4">
        {/* Track background */}
        <div className="h-2 w-full overflow-hidden rounded-full bg-line/80">
          <div
            className="h-full rounded-full bg-gradient-to-r from-accent via-moss to-emerald-500 transition-all duration-500"
            style={{ width: `${percentage}%` }}
          />
        </div>

        {/* Checkpoint Nodes */}
        {REWARD_TIERS.map((tier) => {
          const reached = subtotalVnd >= tier.thresholdVnd;
          const nodePosition = (tier.thresholdVnd / maxThreshold) * 100;

          return (
            <div
              key={tier.id}
              className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 flex flex-col items-center"
              style={{ left: `${nodePosition}%` }}
            >
              {/* Checkpoint Circle */}
              <div
                className={`flex h-6 w-6 sm:h-7 sm:w-7 items-center justify-center rounded-full border-2 transition-all ${
                  reached
                    ? "border-emerald-500 bg-emerald-500 text-white shadow-sm ring-4 ring-emerald-500/20"
                    : "border-line bg-paper text-muted hover:border-accent"
                }`}
                title={`${tier.label} - ${formatVnd(tier.thresholdVnd)}`}
              >
                <Icon name={reached ? "check" : tier.icon} size={13} />
              </div>

              {/* Label underneath */}
              <div className="absolute top-8 flex flex-col items-center whitespace-nowrap text-center">
                <span
                  className={`text-[10px] sm:text-xs font-semibold ${
                    reached ? "text-emerald-700 dark:text-emerald-400" : "text-ink/80"
                  }`}
                >
                  {tier.shortLabel}
                </span>
                <span className="text-[9px] sm:text-[10px] text-muted">
                  {formatVnd(tier.thresholdVnd)}
                </span>

                {/* Quick Apply Voucher Button if reached and not applied */}
                {tier.couponCode && reached && appliedCouponCode !== tier.couponCode && onApplyCoupon ? (
                  <button
                    className="mt-1 inline-flex items-center gap-1 rounded bg-accent/10 hover:bg-accent/20 px-1.5 py-0.5 text-[9px] font-semibold text-accent transition"
                    onClick={() => onApplyCoupon(tier.couponCode!)}
                    type="button"
                  >
                    Dùng mã
                  </button>
                ) : null}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
