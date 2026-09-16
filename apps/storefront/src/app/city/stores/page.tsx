"use client";

import { useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
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
    apiFetch<Store[]>("/api/v1/admin/city/stores")
      .then(setStores)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div>
        <div className="h-8 w-48 animate-pulse rounded bg-sand/60" />
        <div className="mt-6 h-72 animate-pulse rounded-2xl bg-sand/60" />
      </div>
    );
  }

  return (
    <section>
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Store operations</p>
          <h1 className="admin-heading mt-2">Cửa hàng trong thành phố</h1>
          <p className="mt-2 text-sm leading-6 text-muted">{stores.length} cửa hàng</p>
        </div>
      </header>

      <div className="admin-table-shell mt-6">
        <table>
          <thead>
            <tr>
              <th>Cửa hàng</th>
              <th>Địa chỉ</th>
              <th>Liên hệ</th>
              <th>Trạng thái</th>
            </tr>
          </thead>
          <tbody>
            {stores.map((store) => (
              <tr key={store.store_id}>
                <td>
                  <p className="font-semibold">{store.name}</p>
                  <p className="mt-1 text-xs text-muted">{store.code}</p>
                </td>
                <td>
                  <p className="text-sm">{store.address}</p>
                </td>
                <td>
                  <p className="text-sm">{store.phone}</p>
                </td>
                <td>
                  <span
                    className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-semibold ${
                      store.is_active
                        ? "border-success/20 bg-success/10 text-success"
                        : "border-line bg-paper text-muted"
                    }`}
                  >
                    {store.is_active ? "Hoạt động" : "Tạm ngưng"}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {stores.length === 0 && (
          <div className="p-10 text-center">
            <Icon className="mx-auto text-moss" name="store" size={24} />
            <p className="mt-3 text-muted">Chưa có cửa hàng.</p>
          </div>
        )}
      </div>
    </section>
  );
}
