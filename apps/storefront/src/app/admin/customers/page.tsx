"use client";

import { useCallback, useEffect, useState } from "react";

import { ApiError, getAdminCustomers, updateAdminCustomer, type AdminCustomer } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function AdminCustomersPage() {
  const { customer: currentCustomer } = useAuth();
  const [customers, setCustomers] = useState<AdminCustomer[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyCustomer, setBusyCustomer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try { setCustomers(await getAdminCustomers()); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Không tải được khách hàng"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function toggle(customer: AdminCustomer) {
    setBusyCustomer(customer.public_id); setError(null);
    try { await updateAdminCustomer(customer.public_id, customer.status === "active" ? "inactive" : "active"); await load(); }
    catch (err) { setError(err instanceof ApiError ? err.message : "Không đổi được trạng thái tài khoản"); }
    finally { setBusyCustomer(null); }
  }

  return (
    <section>
      <h2 className="text-xl font-semibold">Khách hàng</h2>
      <p className="mt-1 text-sm text-ink/60">Chỉ vô hiệu hóa tài khoản; không xóa lịch sử giao dịch.</p>
      {error ? <p className="mt-5 text-sm text-accent">{error}</p> : null}
      {loading ? <p className="mt-8 text-ink/60">Đang tải…</p> : (
        <div className="mt-6 overflow-x-auto rounded-3xl border border-ink/10 bg-white/70">
          <table className="min-w-full text-left text-sm"><thead className="border-b border-ink/10 text-ink/55"><tr><th className="p-4">Tài khoản</th><th className="p-4">Vai trò</th><th className="p-4">Ngày tạo</th><th className="p-4">Trạng thái</th><th className="p-4"></th></tr></thead><tbody className="divide-y divide-ink/10">{customers.map((customer) => { const isSelf = customer.public_id === currentCustomer?.public_id; const protectedAdmin = customer.role === "admin"; return <tr key={customer.public_id}><td className="p-4"><p className="font-medium">{customer.display_name}{isSelf ? " (bạn)" : ""}</p><p className="text-xs text-ink/50">{customer.email}</p></td><td className="p-4">{customer.role === "admin" ? "Quản trị" : "Khách hàng"}</td><td className="p-4 text-ink/65">{new Date(customer.created_at).toLocaleDateString("vi-VN")}</td><td className="p-4"><span className={customer.status === "active" ? "text-moss" : "text-ink/45"}>{customer.status === "active" ? "Hoạt động" : "Đã khóa"}</span></td><td className="p-4 text-right"><button className="rounded-full border border-ink/20 px-4 py-2 text-xs disabled:opacity-40" disabled={isSelf || protectedAdmin || busyCustomer === customer.public_id} onClick={() => toggle(customer)} type="button">{customer.status === "active" ? "Vô hiệu hóa" : "Kích hoạt"}</button></td></tr>; })}</tbody></table>
        </div>
      )}
    </section>
  );
}
