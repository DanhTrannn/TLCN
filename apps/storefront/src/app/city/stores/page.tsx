"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

interface Store {
  store_id: number;
  code: string;
  name: string;
  address: string;
  phone: string;
  is_active: boolean;
  created_at: string;
}

export default function CityStoresPage() {
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<Store[]>("/admin/city/stores")
      .then(setStores)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="admin-panel animate-pulse text-muted">Đang tải…</div>;
  }

  return (
    <div>
      <h1 className="admin-heading">Cửa hàng trong thành phố</h1>

      {stores.length === 0 ? (
        <div className="admin-panel mt-4 text-muted">Chưa có cửa hàng.</div>
      ) : (
        <div className="mt-4 space-y-3">
          {stores.map((store) => (
            <div key={store.store_id} className="admin-row flex items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-ink">{store.name}</p>
                <p className="text-xs text-muted">{store.address}</p>
                <p className="text-xs text-muted">{store.phone}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                store.is_active ? "bg-moss/10 text-moss" : "bg-surface text-muted"
              }`}>
                {store.is_active ? "Hoạt động" : "Tạm ngưng"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
