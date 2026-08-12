"use client";

import { useCallback, useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError } from "@/lib/api";
import {
  getAdminReviews,
  moderateAdminReview,
  type AdminReview,
} from "@/lib/commerce";

const labels: Record<AdminReview["status"], string> = {
  approved: "Đang hiển thị",
  rejected: "Đã ẩn",
};

function Rating({ value }: { value: number }) {
  return (
    <span
      aria-label={`${value} trên 5 sao`}
      className="inline-flex gap-0.5 text-warning"
      role="img"
    >
      {[1, 2, 3, 4, 5].map((star) => (
        <Icon filled={star <= value} key={star} name="star" size={16} />
      ))}
    </span>
  );
}

export default function AdminReviewsPage() {
  const [status, setStatus] = useState("");
  const [reviews, setReviews] = useState<AdminReview[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [hidingId, setHidingId] = useState<string | null>(null);
  const [hideReason, setHideReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setReviews(await getAdminReviews(status || undefined));
      setError(null);
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tải được đánh giá"
      );
    }
  }, [status]);

  useEffect(() => {
    void load();
  }, [load]);

  async function updateVisibility(
    review: AdminReview,
    nextStatus: "approved" | "rejected"
  ) {
    const reason = nextStatus === "rejected" ? hideReason.trim() : null;
    if (nextStatus === "rejected" && !reason) return;
    setBusy(review.public_id);
    setError(null);
    try {
      await moderateAdminReview(review.public_id, {
        status: nextStatus,
        reason,
      });
      setHidingId(null);
      setHideReason("");
      await load();
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không cập nhật được trạng thái đánh giá"
      );
    } finally {
      setBusy(null);
    }
  }

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Hậu kiểm nội dung</p>
          <h1 className="admin-heading mt-2">Đánh giá</h1>
          <p className="mt-2 text-sm text-muted">
            Đánh giá được hiển thị ngay sau khi khách gửi. Admin chỉ ẩn nội dung vi phạm.
          </p>
        </div>
        <label className="field-label min-w-48" htmlFor="review-status">
          Trạng thái
          <select
            className="admin-input"
            id="review-status"
            onChange={(event) => setStatus(event.target.value)}
            value={status}
          >
            <option value="">Tất cả</option>
            <option value="approved">Đang hiển thị</option>
            <option value="rejected">Đã ẩn</option>
          </select>
        </label>
      </header>

      {error ? <div className="feedback-error mt-5">{error}</div> : null}

      <div className="mt-6 grid gap-4">
        {reviews.map((review) => {
          const hiding = hidingId === review.public_id;
          return (
            <article className="admin-panel" key={review.public_id}>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold">{review.product_name}</h2>
                  <p className="mt-1 text-xs text-muted">
                    {review.customer_name} · {review.order_number}
                  </p>
                  <div className="mt-3">
                    <Rating value={review.rating} />
                  </div>
                </div>
                <span
                  className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ${
                    review.status === "approved"
                      ? "bg-success/10 text-success"
                      : "bg-danger/10 text-danger"
                  }`}
                >
                  {labels[review.status]}
                </span>
              </div>

              {review.content ? (
                <blockquote className="mt-4 rounded-2xl border border-line bg-paper p-4 text-sm leading-6">
                  {review.content}
                </blockquote>
              ) : (
                <p className="mt-4 text-sm italic text-muted">
                  Không có nội dung nhận xét.
                </p>
              )}

              {review.moderation_reason ? (
                <p className="feedback-error mt-4">
                  Lý do ẩn: {review.moderation_reason}
                </p>
              ) : null}

              {review.status === "approved" ? (
                hiding ? (
                  <div className="mt-4 rounded-2xl border border-danger/20 bg-danger/5 p-4">
                    <label
                      className="field-label"
                      htmlFor={`hide-${review.public_id}`}
                    >
                      Lý do ẩn
                      <input
                        autoFocus
                        className="form-control"
                        id={`hide-${review.public_id}`}
                        maxLength={500}
                        onChange={(event) => setHideReason(event.target.value)}
                        value={hideReason}
                      />
                    </label>
                    <div className="mt-3 flex justify-end gap-2">
                      <button
                        className="button-ghost"
                        onClick={() => {
                          setHidingId(null);
                          setHideReason("");
                        }}
                        type="button"
                      >
                        Bỏ qua
                      </button>
                      <button
                        className="button-accent"
                        disabled={!hideReason.trim() || busy === review.public_id}
                        onClick={() => void updateVisibility(review, "rejected")}
                        type="button"
                      >
                        Xác nhận ẩn
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-5 flex justify-end">
                    <button
                      className="button-secondary text-danger"
                      disabled={busy === review.public_id}
                      onClick={() => {
                        setHidingId(review.public_id);
                        setHideReason("");
                      }}
                      type="button"
                    >
                      Ẩn đánh giá
                    </button>
                  </div>
                )
              ) : (
                <div className="mt-5 flex justify-end">
                  <button
                    className="button-primary"
                    disabled={busy === review.public_id}
                    onClick={() => void updateVisibility(review, "approved")}
                    type="button"
                  >
                    <Icon name="check" size={17} />
                    Hiển thị lại
                  </button>
                </div>
              )}
            </article>
          );
        })}

        {reviews.length === 0 ? (
          <div className="admin-panel py-12 text-center">
            <Icon className="mx-auto text-moss" name="star" size={25} />
            <p className="mt-3 text-muted">Không có đánh giá phù hợp.</p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
