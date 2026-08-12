"use client";

import { useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { getProductReviews, type ReviewList } from "@/lib/commerce";
import { formatVietnamDate } from "@/lib/datetime";

function Rating({ value }: { value: number }) {
  return (
    <span aria-label={`${value} trên 5 sao`} className="inline-flex gap-0.5 text-warning" role="img">
      {[1, 2, 3, 4, 5].map((star) => <Icon filled={star <= value} key={star} name="star" size={16} />)}
    </span>
  );
}

export function ProductReviews({ slug }: { slug: string }) {
  const [reviews, setReviews] = useState<ReviewList | null>(null);

  useEffect(() => {
    getProductReviews(slug).then(setReviews).catch(() => setReviews(null));
  }, [slug]);

  return (
    <section className="surface-card mt-14 p-6 sm:p-8">
      <div className="flex flex-wrap items-end justify-between gap-4 border-b border-line pb-5">
        <div>
          <p className="eyebrow text-moss">Trải nghiệm thực tế</p>
          <h2 className="mt-2 font-serif text-3xl tracking-[-0.025em]">Đánh giá sản phẩm</h2>
        </div>
        {reviews?.average_rating ? (
          <div className="rounded-2xl bg-paper px-4 py-3 text-right">
            <p className="text-xl font-semibold">{reviews.average_rating}/5</p>
            <p className="text-xs text-muted">{reviews.total} đánh giá</p>
          </div>
        ) : null}
      </div>
      {!reviews ? (
        <p className="mt-6 text-sm text-muted">Đang tải đánh giá…</p>
      ) : reviews.items.length === 0 ? (
        <div className="mt-6 rounded-2xl border border-dashed border-line bg-paper p-8 text-center">
          <Icon className="mx-auto text-moss" name="star" size={24} />
          <p className="mt-3 text-sm text-muted">Chưa có đánh giá cho sản phẩm này.</p>
        </div>
      ) : (
        <ul className="mt-6 grid gap-4 sm:grid-cols-2">
          {reviews.items.map((review) => (
            <li className="rounded-2xl border border-line bg-paper p-5" key={review.public_id}>
              <Rating value={review.rating} />
              {review.content ? <p className="mt-3 text-sm leading-6 text-ink">{review.content}</p> : null}
              <p className="mt-4 text-xs font-medium text-muted">
                {review.customer_name} · {formatVietnamDate(review.created_at)}
              </p>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
