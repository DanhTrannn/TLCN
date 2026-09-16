"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function StorePosPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/admin/pos");
  }, [router]);

  return (
    <div className="admin-panel animate-pulse text-muted">Đang chuyển đến POS…</div>
  );
}
