"use client";

import { useEffect, useState } from "react";

import { Icon } from "@/components/ui/Icon";
import { apiFetch } from "@/lib/api-client";
import { formatVietnamDateTime } from "@/lib/datetime";

interface StaffMember {
  public_id: string;
  display_name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

const ROLE_LABELS: Record<string, string> = {
  store_manager: "Quản lý cửa hàng",
  admin: "Quản trị viên",
};

export default function StoreStaffPage() {
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<StaffMember[]>("/api/v1/admin/store/staff")
      .then(setStaff)
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
          <p className="eyebrow">Staff management</p>
          <h1 className="admin-heading mt-2">Nhân viên cửa hàng</h1>
          <p className="mt-2 text-sm leading-6 text-muted">{staff.length} nhân viên</p>
        </div>
      </header>

      <div className="admin-table-shell mt-6">
        <table>
          <thead>
            <tr>
              <th>Nhân viên</th>
              <th>Vai trò</th>
              <th>Trạng thái</th>
              <th>Ngày tạo</th>
            </tr>
          </thead>
          <tbody>
            {staff.map((member) => (
              <tr key={member.public_id}>
                <td>
                  <p className="font-semibold">{member.display_name}</p>
                  <p className="mt-1 text-xs text-muted">{member.email}</p>
                </td>
                <td>
                  <span
                    className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-semibold ${
                      member.role === "store_manager"
                        ? "border-accent/25 bg-accent/10 text-accent"
                        : "border-line bg-paper text-muted"
                    }`}
                  >
                    {ROLE_LABELS[member.role] || member.role}
                  </span>
                </td>
                <td>
                  <span
                    className={`inline-flex w-fit items-center rounded-full border px-3 py-1 text-xs font-semibold ${
                      member.status === "active"
                        ? "border-success/20 bg-success/10 text-success"
                        : "border-line bg-paper text-muted"
                    }`}
                  >
                    {member.status === "active" ? "Đang hoạt động" : "Ngừng hoạt động"}
                  </span>
                </td>
                <td className="text-sm text-muted">{formatVietnamDateTime(member.created_at)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {staff.length === 0 && (
          <div className="p-10 text-center">
            <Icon className="mx-auto text-moss" name="users" size={24} />
            <p className="mt-3 text-muted">Chưa có nhân viên.</p>
          </div>
        )}
      </div>
    </section>
  );
}
