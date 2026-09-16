"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AdminPosPage() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/store/pos");
  }, [router]);

  return (
    <div className="admin-panel animate-pulse text-muted">Đang chuyển đến POS…</div>
  );
}
