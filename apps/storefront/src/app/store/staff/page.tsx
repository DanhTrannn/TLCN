"use client";

import { useEffect, useState } from "react";

import { apiFetch } from "@/lib/api-client";

interface StaffMember {
  public_id: string;
  display_name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

export default function StoreStaffPage() {
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiFetch<StaffMember[]>("/admin/store/staff")
      .then(setStaff)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="admin-panel animate-pulse text-muted">Đang tải…</div>;
  }

  const roleLabels: Record<string, string> = {
    store_manager: "Quản lý cửa hàng",
    city_planner: "Quản lý thành phố",
    admin: "Quản trị viên",
  };

  return (
    <div>
      <h1 className="admin-heading">Nhân viên cửa hàng</h1>

      {staff.length === 0 ? (
        <div className="admin-panel mt-4 text-muted">Chưa có nhân viên.</div>
      ) : (
        <div className="mt-4 space-y-3">
          {staff.map((member) => (
            <div key={member.public_id} className="admin-row flex items-center justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-semibold text-ink">{member.display_name}</p>
                <p className="text-xs text-muted">{member.email}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${
                member.role === "store_manager" ? "bg-accent/10 text-accent" : "bg-surface text-muted"
              }`}>
                {roleLabels[member.role] || member.role}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
