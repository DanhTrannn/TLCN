"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useRef, useState } from "react";

import { DetailTable, EmptyState } from "@/components/analytics/AnalyticsUI";
import { RoleDashboards } from "@/components/analytics/RoleDashboards";
import { SalesTrendPanel } from "@/components/analytics/SalesTrendPanel";
import { Icon } from "@/components/ui/Icon";
import { getAdminAnalyticsStores, getAdminRoleMetrics, type RoleMetricsResponse, type StoreItemResponse } from "@/lib/api";
import { ANALYTICS_ROLES, CANONICAL_ROLES, isAnalyticsRole, metricDefinitions, sourceName } from "@/lib/analytics-dashboard";
import { useAuth } from "@/lib/auth";
import { AUTO_REFRESH_INTERVAL_MS, shouldAutoRefreshRole } from "@/lib/dashboard-refresh";

function LoadingDashboard() {
  return <div aria-label="Đang tải báo cáo" className="space-y-5" role="status">
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">{[0, 1, 2, 3].map(index => <div className="h-40 animate-pulse rounded-2xl bg-sand/60" key={index} />)}</div>
    <div className="h-72 animate-pulse rounded-2xl bg-sand/40" />
  </div>;
}

function AnalyticsHubContent() {
  const { customer, loading: authLoading } = useAuth();
  const searchParams = useSearchParams();
  const canonicalRole = CANONICAL_ROLES[customer?.role ?? ""];
  const requestedRole = searchParams.get("role");
  const activeRole = isAnalyticsRole(requestedRole) ? requestedRole : canonicalRole ?? "executive";
  const role = ANALYTICS_ROLES.find(item => item.id === activeRole)!;
  const isAdmin = customer?.role === "admin";
  const unauthorized = !isAdmin && activeRole !== canonicalRole;
  const [selectedStoreId, setSelectedStoreId] = useState<number | undefined>();
  const [stores, setStores] = useState<{ customerId: string; items: StoreItemResponse[] } | null>(null);
  const [storeError, setStoreError] = useState<string | null>(null);
  const [refreshVersion, setRefreshVersion] = useState(0);
  const [snapshot, setSnapshot] = useState<{ key: string; metrics: RoleMetricsResponse; receivedAt: Date } | null>(null);
  const [failure, setFailure] = useState<{ key: string; message: string } | null>(null);
  const [pending, setPending] = useState(false);
  const inFlight = useRef(false);
  const customerId = customer?.public_id;
  const storeParam = activeRole === "store" && isAdmin ? selectedStoreId : undefined;
  const requestKey = `${customerId}:${activeRole}:${storeParam ?? "default"}`;
  const metrics = snapshot?.key === requestKey ? snapshot.metrics : null;
  const error = failure?.key === requestKey ? failure.message : null;
  const loading = !metrics && !error;
  const autoRefresh = shouldAutoRefreshRole(activeRole);
  const availableStores = stores && stores.customerId === customerId ? stores.items : [];

  useEffect(() => {
    if (!customerId || activeRole !== "store" || unauthorized) return;
    let current = true;
    setStoreError(null);
    getAdminAnalyticsStores().then(items => {
      if (current) setStores({ customerId, items });
    }).catch((cause: unknown) => {
      if (current) setStoreError(cause instanceof Error ? cause.message : "Không tải được danh sách cửa hàng.");
    });
    return () => { current = false; };
  }, [customerId, activeRole, unauthorized, refreshVersion]);

  useEffect(() => {
    if (authLoading || !customerId || unauthorized) return;
    let current = true;
    inFlight.current = true;
    setPending(true);
    setFailure(null);
    getAdminRoleMetrics(activeRole, storeParam).then(response => {
      if (!current) return;
      if (response.role !== activeRole) throw new Error("Phản hồi không khớp vai trò được yêu cầu. Vui lòng tải lại.");
      setSnapshot({ key: requestKey, metrics: response, receivedAt: new Date() });
    }).catch((cause: unknown) => {
      if (current) setFailure({ key: requestKey, message: cause instanceof Error ? cause.message : "Không thể tải báo cáo." });
    }).finally(() => {
      if (current) { inFlight.current = false; setPending(false); }
    });
    return () => { current = false; inFlight.current = false; };
  }, [authLoading, customerId, activeRole, unauthorized, storeParam, requestKey, refreshVersion]);

  useEffect(() => {
    if (!customerId || unauthorized || !autoRefresh) return;
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible" && !inFlight.current) setRefreshVersion(value => value + 1);
    }, AUTO_REFRESH_INTERVAL_MS);
    return () => window.clearInterval(timer);
  }, [customerId, unauthorized, autoRefresh, activeRole]);

  if (authLoading || !customer) return <LoadingDashboard />;

  const visibleRoles = isAdmin ? ANALYTICS_ROLES : ANALYTICS_ROLES.filter(item => item.id === canonicalRole);
  const effectiveStoreId = selectedStoreId ?? (metrics?.role === "store" ? metrics.store_id ?? undefined : undefined);
  const displayedStoreMissing = effectiveStoreId != null && !availableStores.some(store => store.store_id === effectiveStoreId);
  const receivedAt = metrics && snapshot ? new Intl.DateTimeFormat("vi-VN", { timeZone: "Asia/Ho_Chi_Minh", dateStyle: "short", timeStyle: "medium", hour12: false }).format(snapshot.receivedAt) : null;

  return <section className="space-y-5">
    <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">D&K / Không gian phân tích</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-ink sm:text-4xl">Báo cáo & quyết định</h1>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-muted">Theo dõi kết quả, tìm điểm cần kiểm tra và mở công việc liên quan.</p>
      </div>
      {!unauthorized && <button className="button-secondary shrink-0 rounded-xl" disabled={pending} onClick={() => setRefreshVersion(value => value + 1)} type="button"><Icon className={pending ? "animate-spin" : ""} name="rotate-ccw" size={16} />{pending ? "Đang tải lại…" : "Làm mới báo cáo"}</button>}
    </header>

    <nav aria-label="Góc nhìn báo cáo" className="flex flex-wrap gap-1.5 rounded-2xl border border-line bg-surface p-2">
      {visibleRoles.map(item => <Link aria-current={activeRole === item.id ? "page" : undefined} className={`inline-flex min-h-10 flex-1 items-center justify-center gap-2 whitespace-nowrap rounded-xl px-3 py-2 text-xs font-semibold transition sm:flex-none ${activeRole === item.id ? "bg-ink text-paper" : "text-muted hover:bg-paper hover:text-ink"}`} href={`/admin/analytics?role=${item.id}`} key={item.id}><Icon name={item.icon} size={16} />{item.label}</Link>)}
    </nav>

    {unauthorized ? <div className="feedback-error" role="alert"><p className="font-semibold">Bạn không có quyền xem góc nhìn này.</p><p className="mt-1 text-sm">Tài khoản chỉ được truy cập báo cáo theo vai trò được cấp.</p><Link className="mt-3 inline-flex min-h-10 items-center gap-2 font-semibold underline" href={`/admin/analytics?role=${canonicalRole}`}>Mở báo cáo của bạn<Icon name="arrow-right" size={16} /></Link></div> : <>
      <section className="rounded-2xl border border-line bg-surface p-4 sm:p-5">
        <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
          <div><h2 className="text-lg font-semibold text-ink">{role.label}</h2><p className="mt-1 text-sm leading-6 text-muted">{role.purpose}</p></div>
          {activeRole === "store" && <div className="w-full lg:max-w-xs">
            <label className="field-label" htmlFor="analytics-store">Phạm vi cửa hàng</label>
            {isAdmin ? <select className="admin-input" disabled={pending} id="analytics-store" onChange={event => setSelectedStoreId(event.target.value ? Number(event.target.value) : undefined)} value={effectiveStoreId ?? ""}>
              <option value="">Cửa hàng mặc định theo API</option>
              {displayedStoreMissing && <option value={effectiveStoreId}>{metrics?.role === "store" ? metrics.store_name ?? `Cửa hàng #${effectiveStoreId}` : `Cửa hàng #${effectiveStoreId}`}</option>}
              {availableStores.map(store => <option key={store.store_id} value={store.store_id}>{store.name}</option>)}
            </select> : <p className="mt-2 text-sm font-semibold" id="analytics-store">{metrics?.role === "store" ? metrics.store_name ?? "Cửa hàng được phân quyền" : "Cửa hàng được phân quyền"}</p>}
            {selectedStoreId != null && isAdmin && <button className="mt-2 min-h-8 text-xs font-semibold text-accent underline" onClick={() => setSelectedStoreId(undefined)} type="button">Về cửa hàng mặc định</button>}
            {storeError && <p className="mt-2 text-xs leading-5 text-danger" role="status">{storeError} Dùng nút làm mới để thử lại.</p>}
          </div>}
        </div>
        <div className="mt-4 grid gap-3 border-t border-line pt-4 text-xs leading-5 text-muted sm:grid-cols-2 xl:grid-cols-3">
          <div><p className="font-semibold text-ink">Nguồn phản hồi</p><p>{sourceName(metrics?.data_source)}</p></div>
          <div><p className="font-semibold text-ink">Phạm vi đo</p><p>{role.scope}</p></div>
          <div><p className="font-semibold text-ink">Lần tải thành công</p><p>{receivedAt ? `${receivedAt} · UTC+7` : "Chưa có phản hồi thành công"}</p><p>{autoRefresh ? "Tải lại mỗi 60 giây khi trang đang hiển thị." : "Tải lại thủ công."} Đây không phải thời điểm Gold được cập nhật.</p></div>
        </div>
        <details className="mt-4 border-t border-line pt-3"><summary className="cursor-pointer text-xs font-semibold text-muted">Báo cáo này giúp trả lời điều gì?</summary><ul className="mt-2 list-inside list-disc space-y-1 text-sm leading-6 text-muted">{role.questions.map(question => <li key={question}>{question}</li>)}</ul></details>
      </section>

      {metrics?.is_degraded && <div className="flex items-start gap-3 rounded-xl border border-warning/30 bg-warning/5 p-4 text-sm leading-6 text-warning" role="status"><Icon className="mt-1 shrink-0" name="alert" size={18} /><div><p className="font-semibold">Nguồn thay thế hoặc dữ liệu chưa đầy đủ</p><p>{metrics.degraded_reason ?? "Phản hồi đang được đánh dấu degraded. Xem nguồn và định nghĩa trước khi diễn giải."}</p><p>Không coi công thức nguồn thay thế là bản sao của Gold.</p></div></div>}
      {error && <div className="feedback-error" role="alert"><p className="font-semibold">Không tải được báo cáo mới</p><p className="mt-1">{error}</p>{metrics && <p className="mt-1">Các số bên dưới vẫn là lần tải thành công lúc {receivedAt}; chưa được cập nhật.</p>}<button className="mt-2 min-h-8 font-semibold underline" onClick={() => setRefreshVersion(value => value + 1)} type="button">Thử lại</button></div>}
      {loading && <LoadingDashboard />}
      {metrics && <div aria-busy={pending} className="space-y-5" key={requestKey}>
        <RoleDashboards metrics={metrics} trend={activeRole === "executive" || activeRole === "sales" ? <SalesTrendPanel refreshVersion={refreshVersion} /> : undefined} userRole={customer.role} />
        <details className="rounded-2xl border border-line bg-surface p-4 sm:p-5">
          <summary className="cursor-pointer text-sm font-semibold text-ink">Định nghĩa chỉ số & lưu ý khi đọc</summary>
          <p className="mb-4 mt-3 text-xs leading-5 text-muted">Nguồn hiện tại: {sourceName(metrics.data_source)}. API chưa cung cấp kỳ trước/target đồng nhất cho mọi KPI, nên không dựng delta hoặc chỉ tiêu. Các tỷ lệ cần có mẫu số dương; dấu — nghĩa là chưa đủ dữ liệu để tính hoặc chưa có giá trị.</p>
          <DetailTable caption="Từ điển chỉ số của góc nhìn hiện tại" filename={`dinh-nghia-${activeRole}-${metrics.data_source}`} rows={metricDefinitions(metrics)} rowKey={row => row.name} columns={[
            { key: "name", label: "Chỉ số", value: row => row.name }, { key: "formula", label: "Cách tính / ý nghĩa", value: row => row.calculation }, { key: "unit", label: "Đơn vị", value: row => row.unit },
            { key: "grain", label: "Mức dữ liệu", value: row => row.grain }, { key: "scope", label: "Kỳ / bộ lọc", value: row => row.scope }, { key: "caveat", label: "Giới hạn", value: row => row.caveat },
          ]} />
        </details>
        <p className="px-1 text-xs leading-5 text-muted">Dữ liệu do generator tạo là dữ liệu tổng hợp. Số liệu trên dashboard không tự chứng minh hiệu quả kinh doanh hay hiệu năng production.</p>
      </div>}
      {!loading && !metrics && !error && <EmptyState detail="Chưa nhận được phản hồi cho góc nhìn này. Thử tải lại báo cáo." />}
    </>}
  </section>;
}

export default function AnalyticsHubPage() {
  return <Suspense fallback={<LoadingDashboard />}><AnalyticsHubContent /></Suspense>;
}
