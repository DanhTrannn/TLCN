"use client";

import { useEffect, useState } from "react";

import { useLocation } from "@/components/LocationContext";
import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  formatVnd,
  getProductAvailability,
  type ProductAvailability,
  type VariantAvailability,
} from "@/lib/api";

interface StoreAvailabilityBoxProps {
  slug: string;
  variantPublicId: string | null;
}

export function StoreAvailabilityBox({ slug, variantPublicId }: StoreAvailabilityBoxProps) {
  const { selectedCity } = useLocation();
  const [availability, setAvailability] = useState<ProductAvailability | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!selectedCity) return;
    setLoading(true);
    setError(null);
    getProductAvailability(slug, selectedCity.code)
      .then(setAvailability)
      .catch((err) => {
        if (err instanceof ApiError) {
          setError(err.message);
        } else {
          setError("Không thể tải thông tin tồn kho");
        }
      })
      .finally(() => setLoading(false));
  }, [slug, selectedCity]);

  if (!selectedCity) return null;

  const variant: VariantAvailability | undefined = availability?.variants.find(
    (v) => v.variant_public_id === variantPublicId
  );

  const totalOnHand = variant?.total_on_hand ?? 0;

  return (
    <div className="rounded-2xl border border-line bg-surface p-5 shadow-sm">
      <div className="flex items-center gap-2 text-sm font-semibold text-ink">
        <Icon className="text-moss" name="store" size={18} />
        <span>Xem cửa hàng còn hàng</span>
      </div>

      {loading ? (
        <div className="mt-4 space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 animate-pulse rounded-xl bg-sand/50" />
          ))}
        </div>
      ) : error ? (
        <p className="feedback-error mt-3">{error}</p>
      ) : variant ? (
        <>
          <p className="mt-3 text-sm font-medium text-muted">
            Tổng tồn tại <span className="font-semibold text-ink">{selectedCity.name}</span>:
            <span className={`ml-1 font-semibold ${totalOnHand > 0 ? "text-success" : "text-danger"}`}>
              {totalOnHand > 0 ? `Còn ${totalOnHand} sản phẩm` : "Tạm hết hàng"}
            </span>
          </p>

          {variant.stores.length > 0 ? (
            <ul className="mt-3 space-y-2">
              {variant.stores.map((store) => (
                <li
                  key={store.store_code}
                  className="flex items-center justify-between rounded-xl border border-line bg-paper px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-semibold text-ink">{store.store_name}</p>
                    <p className="text-xs text-muted">SKU: {store.sku}</p>
                  </div>
                  <span
                    className={`text-xs font-semibold ${store.on_hand > 0 ? "text-success" : "text-danger"}`}
                  >
                    {store.on_hand > 0 ? `Còn ${store.on_hand}` : "Hết"}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-3 text-xs text-muted">Không có thông tin cửa hàng cụ thể</p>
          )}

          <p className="mt-3 text-xs text-muted">
            {formatVnd(variant.price_vnd)}
          </p>
        </>
      ) : null}
    </div>
  );
}
