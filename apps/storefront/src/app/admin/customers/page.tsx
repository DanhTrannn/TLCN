"use client";

import { useCallback, useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { ApiError, getAdminCustomers, updateAdminCustomer, type AdminCustomer } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { formatVietnamDate } from "@/lib/datetime";

export default function AdminCustomersPage() {
  const { customer: currentCustomer } = useAuth();
  const [customers, setCustomers] = useState<AdminCustomer[]>([]);
  const [loading, setLoading] = useState(true);
  const [busyCustomer, setBusyCustomer] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    try {
      setCustomers(await getAdminCustomers());
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không tải được khách hàng");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function toggle(customer: AdminCustomer) {
    setBusyCustomer(customer.public_id);
    setError(null);
    try {
      await updateAdminCustomer(customer.public_id, customer.status === "active" ? "inactive" : "active");
      await load();
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không đổi được trạng thái tài khoản");
    } finally {
      setBusyCustomer(null);
    }
  }

  return (
    <section>
      <header>
        <p className="eyebrow">Customer accounts</p>
        <h1 className="admin-heading mt-2">Khách hàng</h1>
        <p className="mt-2 text-sm leading-6 text-muted">Vô hiệu hóa quyền đăng nhập mà không xóa lịch sử giao dịch.</p>
      </header>
      {error ? <div className="feedback-error mt-5">{error}</div> : null}
      {loading ? (
        <div className="mt-6 h-64 animate-pulse rounded-2xl bg-sand/60" />
      ) : (
        <div className="admin-table-shell mt-6">
          <table>
            <thead><tr><th>Tài khoản</th><th>Vai trò</th><th>Ngày tạo</th><th>Trạng thái</th><th><span className="sr-only">Thao tác</span></th></tr></thead>
            <tbody>
              {customers.map((customer) => {
                const isSelf = customer.public_id === currentCustomer?.public_id;
                const protectedAdmin = customer.role === "admin";
                const active = customer.status === "active";
                return (
                  <tr key={customer.public_id}>
                    <td><div className="flex items-center gap-3"><span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-moss/10 text-moss"><Icon name="user" size={18} /></span><div><p className="font-semibold">{customer.display_name}{isSelf ? " (bạn)" : ""}</p><p className="text-xs text-muted">{customer.email}</p></div></div></td>
                    <td>{customer.role === "admin" ? "Quản trị" : "Khách hàng"}</td>
                    <td className="text-muted">{formatVietnamDate(customer.created_at)}</td>
                    <td><span className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold ${active ? "bg-success/10 text-success" : "bg-muted/10 text-muted"}`}>{active ? "Hoạt động" : "Đã khóa"}</span></td>
                    <td className="text-right"><button className={active ? "button-secondary px-4 text-danger" : "button-secondary px-4 text-success"} disabled={isSelf || protectedAdmin || busyCustomer === customer.public_id} onClick={() => void toggle(customer)} type="button">{busyCustomer === customer.public_id ? "Đang lưu…" : active ? "Vô hiệu hóa" : "Kích hoạt"}</button></td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
