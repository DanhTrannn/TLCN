"use client";

import { useCallback, useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError } from "@/lib/api";
import { getAdminReviews, moderateAdminReview, type AdminReview } from "@/lib/commerce";

const labels = { pending: "Chờ duyệt", approved: "Đã duyệt", rejected: "Từ chối" };

function Rating({ value }: { value: number }) {
  return <span aria-label={`${value} trên 5 sao`} className="inline-flex gap-0.5 text-warning" role="img">{[1, 2, 3, 4, 5].map((star) => <Icon filled={star <= value} key={star} name="star" size={16} />)}</span>;
}

export default function AdminReviewsPage() {
  const [status, setStatus] = useState("");
  const [reviews, setReviews] = useState<AdminReview[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [rejectingId, setRejectingId] = useState<string | null>(null);
  const [rejectReason, setRejectReason] = useState("");
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setReviews(await getAdminReviews(status || undefined));
      setError(null);
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không tải được đánh giá");
    }
  }, [status]);

  useEffect(() => { void load(); }, [load]);

  async function moderate(review: AdminReview, nextStatus: "approved" | "rejected") {
    const reason = nextStatus === "rejected" ? rejectReason.trim() : null;
    if (nextStatus === "rejected" && !reason) return;
    setBusy(review.public_id);
    setError(null);
    try {
      await moderateAdminReview(review.public_id, { status: nextStatus, reason });
      setRejectingId(null);
      setRejectReason("");
      await load();
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không duyệt được đánh giá");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div><p className="eyebrow">Moderation</p><h1 className="admin-heading mt-2">Đánh giá</h1><p className="mt-2 text-sm text-muted">Duyệt nội dung được tạo từ order item đã hoàn tất.</p></div>
        <label className="field-label min-w-48" htmlFor="review-status">Trạng thái<select className="admin-input" id="review-status" value={status} onChange={(event) => setStatus(event.target.value)}><option value="">Tất cả</option><option value="pending">Chờ duyệt</option><option value="approved">Đã duyệt</option><option value="rejected">Từ chối</option></select></label>
      </header>
      {error ? <div className="feedback-error mt-5">{error}</div> : null}
      <div className="mt-6 grid gap-4">
        {reviews.map((review) => {
          const rejecting = rejectingId === review.public_id;
          return (
            <article className="admin-panel" key={review.public_id}>
              <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                <div><h2 className="text-lg font-semibold">{review.product_name}</h2><p className="mt-1 text-xs text-muted">{review.customer_name} · {review.order_number}</p><div className="mt-3"><Rating value={review.rating} /></div></div>
                <span className={`w-fit rounded-full px-3 py-1 text-xs font-semibold ${review.status === "approved" ? "bg-success/10 text-success" : review.status === "rejected" ? "bg-danger/10 text-danger" : "bg-warning/10 text-warning"}`}>{labels[review.status]}</span>
              </div>
              {review.content ? <blockquote className="mt-4 rounded-2xl border border-line bg-paper p-4 text-sm leading-6">{review.content}</blockquote> : <p className="mt-4 text-sm italic text-muted">Không có nội dung nhận xét.</p>}
              {review.moderation_reason ? <p className="feedback-error mt-4">Lý do: {review.moderation_reason}</p> : null}
              {rejecting ? (
                <div className="mt-4 rounded-2xl border border-danger/20 bg-danger/5 p-4">
                  <label className="field-label" htmlFor={`reject-${review.public_id}`}>Lý do từ chối<input autoFocus className="form-control" id={`reject-${review.public_id}`} maxLength={500} onChange={(event) => setRejectReason(event.target.value)} value={rejectReason} /></label>
                  <div className="mt-3 flex justify-end gap-2"><button className="button-ghost" onClick={() => { setRejectingId(null); setRejectReason(""); }} type="button">Bỏ qua</button><button className="button-accent" disabled={!rejectReason.trim() || busy === review.public_id} onClick={() => void moderate(review, "rejected")} type="button">Xác nhận từ chối</button></div>
                </div>
              ) : (
                <div className="mt-5 flex flex-wrap justify-end gap-2">
                  <button className="button-secondary text-danger" disabled={busy === review.public_id} onClick={() => { setRejectingId(review.public_id); setRejectReason(""); }} type="button">Từ chối</button>
                  <button className="button-primary" disabled={busy === review.public_id} onClick={() => void moderate(review, "approved")} type="button"><Icon name="check" size={17} />Duyệt đánh giá</button>
                </div>
              )}
            </article>
          );
        })}
        {reviews.length === 0 ? <div className="admin-panel py-12 text-center"><Icon className="mx-auto text-moss" name="star" size={25} /><p className="mt-3 text-muted">Không có đánh giá phù hợp.</p></div> : null}
      </div>
    </section>
  );
}
