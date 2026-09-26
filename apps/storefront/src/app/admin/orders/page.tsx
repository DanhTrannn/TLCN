"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { AdminModal } from "@/components/admin/AdminModal";
import { OrderStatusBadge, orderStatusShortLabel } from "@/components/OrderStatusBadge";
import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  formatMetricVnd,
  formatVnd,
  getAdminOrders,
  type AdminOrder,
} from "@/lib/api";
import {
  cancelAdminOrder,
  completeAdminOrder,
  confirmAdminOrder,
  deliverAdminOrder,
  dispatchAdminOrder,
  failDeliveryAdminOrder,
  getDeliveryStaffList,
  type DeliveryStaff,
} from "@/lib/commerce";
import { exportToCsv } from "@/lib/csv-export";
import { formatVietnamDateTime } from "@/lib/datetime";

const STATUS_TABS = [
  { key: "", label: "Tất cả" },
  { key: "paid", label: "Chờ xác nhận" },
  { key: "confirmed", label: "Chờ xuất kho" },
  { key: "shipping", label: "Đang giao hàng" },
  { key: "delivered", label: "Đã giao hàng" },
  { key: "failed_delivery", label: "Giao thất bại" },
  { key: "completed", label: "Hoàn tất" },
  { key: "cancelled", label: "Đã hủy" },
] as const;

export default function AdminOrdersPage() {
  const searchParams = useSearchParams();
  const initialStatus = searchParams.get("status") ?? "";
  const initialChannel = searchParams.get("channel") ?? "all";

  const [status, setStatus] = useState<string>(initialStatus);
  const [channelFilter, setChannelFilter] = useState<string>(initialChannel);
  const [search, setSearch] = useState("");
  const [orders, setOrders] = useState<AdminOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [busyOrder, setBusyOrder] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Pagination state
  const [page, setPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(15);

  // Cancel modal state
  const [cancellingOrder, setCancellingOrder] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("Cửa hàng không thể xử lý đơn");

  // Dispatch modal state
  const [dispatchingOrder, setDispatchingOrder] = useState<string | null>(null);
  const [staffList, setStaffList] = useState<DeliveryStaff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(false);
  const [staffError, setStaffError] = useState<string | null>(null);
  const [selectedStaffId, setSelectedStaffId] = useState<number | null>(null);
  const [dispatchNotes, setDispatchNotes] = useState("");

  // Boom modal state
  const [boomingOrder, setBoomingOrder] = useState<string | null>(null);
  const [boomReason, setBoomReason] = useState("Khách không nghe máy / từ chối nhận hàng");

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }
    setError(null);
    try {
      // Fetch all orders to power fast client-side tab switching and KPI metrics
      const data = await getAdminOrders();
      setOrders(data);
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không tải được danh sách đơn hàng"
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  // Keep status tab in sync if URL parameter changes
  useEffect(() => {
    const urlStatus = searchParams.get("status");
    if (urlStatus !== null) {
      setStatus(urlStatus);
      setPage(1);
    }
  }, [searchParams]);

  async function mutate(
    orderNumber: string,
    action: () => Promise<unknown>,
    fallbackMessage: string
  ) {
    setBusyOrder(orderNumber);
    setError(null);
    try {
      await action();
      await load(true);
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : fallbackMessage
      );
    } finally {
      setBusyOrder(null);
    }
  }

  function handleOpenCancel(orderNumber: string) {
    setCancellingOrder(orderNumber);
    setCancelReason("Cửa hàng không thể xử lý đơn");
  }

  function submitCancel() {
    if (!cancellingOrder || cancelReason.trim().length < 3) return;
    const target = cancellingOrder;
    void mutate(
      target,
      async () => {
        await cancelAdminOrder(target, cancelReason.trim());
        setCancellingOrder(null);
      },
      "Không hủy được đơn hàng"
    );
  }

  async function handleOpenDispatch(orderNumber: string) {
    setDispatchingOrder(orderNumber);
    setDispatchNotes("");
    if (staffList.length === 0) {
      setLoadingStaff(true);
      setStaffError(null);
      try {
        const staff = await getDeliveryStaffList();
        setStaffList(staff);
        const active = staff.filter((s) => s.is_active);
        if (active.length > 0) {
          setSelectedStaffId(active[0].staff_id);
        } else {
          setSelectedStaffId(null);
        }
      } catch (staffErr) {
        setStaffError(
          staffErr instanceof ApiError
            ? staffErr.message
            : "Không tải được danh sách nhân viên giao hàng"
        );
      } finally {
        setLoadingStaff(false);
      }
    } else {
      const active = staffList.filter((s) => s.is_active);
      if (
        active.length > 0 &&
        (!selectedStaffId || !active.some((s) => s.staff_id === selectedStaffId))
      ) {
        setSelectedStaffId(active[0].staff_id);
      }
    }
  }

  function submitDispatch() {
    if (!dispatchingOrder || !selectedStaffId) return;
    const target = dispatchingOrder;
    void mutate(
      target,
      async () => {
        await dispatchAdminOrder(
          target,
          selectedStaffId,
          dispatchNotes.trim() || undefined
        );
        setDispatchingOrder(null);
      },
      "Không xuất kho được đơn hàng"
    );
  }

  function handleOpenBoom(orderNumber: string) {
    setBoomingOrder(orderNumber);
    setBoomReason("Khách không nghe máy / từ chối nhận hàng");
  }

  function submitBoom() {
    if (!boomingOrder || boomReason.trim().length === 0) return;
    const target = boomingOrder;
    void mutate(
      target,
      async () => {
        await failDeliveryAdminOrder(target, boomReason.trim());
        setBoomingOrder(null);
      },
      "Không cập nhật được trạng thái giao thất bại"
    );
  }

  function handleConfirm(orderNumber: string) {
    void mutate(
      orderNumber,
      () => confirmAdminOrder(orderNumber),
      "Không xác nhận được đơn hàng"
    );
  }

  function handleDeliver(orderNumber: string) {
    void mutate(
      orderNumber,
      () => deliverAdminOrder(orderNumber),
      "Không cập nhật được trạng thái giao thành công"
    );
  }

  function handleComplete(orderNumber: string) {
    void mutate(
      orderNumber,
      () => completeAdminOrder(orderNumber),
      "Không hoàn tất được đơn hàng"
    );
  }

  const activeStaff = staffList.filter((s) => s.is_active);

  // Compute status counts for badges & KPI cards
  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = { "": orders.length };
    for (const o of orders) {
      counts[o.status] = (counts[o.status] || 0) + 1;
    }
    return counts;
  }, [orders]);

  // Summary KPIs
  const kpiData = useMemo(() => {
    const totalRevenue = orders.reduce((sum, o) => sum + (o.total_vnd || 0), 0);
    const needAction = (statusCounts["paid"] || 0) + (statusCounts["confirmed"] || 0);
    const shipping = statusCounts["shipping"] || 0;
    const boom = statusCounts["failed_delivery"] || 0;
    const online = orders.filter((o) => (o.channel || "online") === "online").length;
    const pos = orders.filter((o) => o.channel === "pos").length;

    return {
      totalOrders: orders.length,
      totalRevenue,
      needAction,
      shipping,
      boom,
      online,
      pos,
    };
  }, [orders, statusCounts]);

  // Filtered orders based on Status, Channel, and Search Query
  const filteredOrders = useMemo(() => {
    return orders.filter((o) => {
      // 1. Channel filter
      if (channelFilter === "online" && o.channel === "pos") return false;
      if (channelFilter === "pos" && o.channel !== "pos") return false;

      // 2. Status filter
      if (status && o.status !== status) return false;

      // 3. Search text
      if (search.trim()) {
        const q = search.trim().toLowerCase();
        const matchesNumber = o.order_number.toLowerCase().includes(q);
        const matchesName = o.customer_name.toLowerCase().includes(q);
        const matchesEmail = o.customer_email.toLowerCase().includes(q);
        if (!matchesNumber && !matchesName && !matchesEmail) return false;
      }

      return true;
    });
  }, [orders, channelFilter, status, search]);

  // Paginated list
  const totalPages = Math.max(1, Math.ceil(filteredOrders.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const paginatedOrders = useMemo(() => {
    const start = (currentPage - 1) * pageSize;
    return filteredOrders.slice(start, start + pageSize);
  }, [filteredOrders, currentPage, pageSize]);

  function handleExportCsv() {
    exportToCsv(
      `don_hang_admin_${new Date().toISOString().slice(0, 10)}`,
      [
        "Mã đơn hàng",
        "Khách hàng",
        "Email",
        "Kênh",
        "Phương thức thanh toán",
        "Trạng thái",
        "Số món",
        "Tổng tiền (VNĐ)",
        "Ngày tạo",
      ],
      filteredOrders.map((o) => [
        o.order_number,
        o.customer_name,
        o.customer_email,
        o.channel === "pos" ? "Tại quầy (POS)" : "Online",
        o.payment_method === "cod" ? "COD" : "VietQR",
        orderStatusShortLabel(o.status),
        o.item_count,
        o.total_vnd,
        formatVietnamDateTime(o.created_at),
      ])
    );
  }

  return (
    <section className="space-y-6">
      {/* Top Header */}
      <header className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">Order operations</p>
          <h1 className="admin-heading mt-2">Quản lý Đơn hàng</h1>
          <p className="mt-2 text-sm leading-6 text-muted">
            Theo dõi vòng đời đơn hàng: xác nhận thanh toán, điều phối shipper, xử lý boom và đối soát xuất kho.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <button
            className="button-secondary inline-flex items-center gap-1.5 h-10 px-3.5 text-xs font-semibold"
            disabled={loading || refreshing}
            onClick={() => void load(true)}
            title="Làm mới dữ liệu"
            type="button"
          >
            <Icon className={refreshing ? "animate-spin text-accent" : ""} name="rotate-ccw" size={15} />
            <span>Làm mới</span>
          </button>
          <button
            className="button-secondary inline-flex items-center gap-1.5 h-10 px-3.5 text-xs font-semibold"
            disabled={filteredOrders.length === 0}
            onClick={handleExportCsv}
            title="Xuất file CSV"
            type="button"
          >
            <Icon name="receipt" size={15} />
            <span>Xuất CSV ({filteredOrders.length})</span>
          </button>
        </div>
      </header>

      {error ? (
        <div className="feedback-error">
          <div className="flex items-center justify-between">
            <span>{error}</span>
            <button className="text-xs underline font-semibold ml-3" onClick={() => void load(true)} type="button">
              Thử lại
            </button>
          </div>
        </div>
      ) : null}

      {/* 4 Operations KPI Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {/* Card 1: Tổng đơn hàng */}
        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Tổng đơn hàng</p>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sand text-muted">
              <Icon name="receipt" size={18} />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold tracking-tight text-ink font-mono">
            {loading ? "..." : kpiData.totalOrders.toLocaleString("vi-VN")}
          </p>
          <p className="mt-2 text-xs text-muted truncate">
            Giá trị: <span className="font-semibold text-accent font-mono">{loading ? "..." : formatMetricVnd(kpiData.totalRevenue)}</span>
          </p>
        </article>

        {/* Card 2: Cần xử lý gấp */}
        <article
          className={`admin-panel min-w-0 overflow-hidden transition ${
            kpiData.needAction > 0 ? "border-amber-500/40 bg-amber-500/[0.02]" : ""
          }`}
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Cần xử lý gấp</p>
            <div
              className={`flex h-9 w-9 items-center justify-center rounded-xl ${
                kpiData.needAction > 0 ? "bg-amber-500/15 text-amber-600 dark:text-amber-400" : "bg-sand text-muted"
              }`}
            >
              <Icon name="alert" size={18} />
            </div>
          </div>
          <div className="mt-3 flex items-baseline gap-2">
            <span
              className={`text-2xl font-bold tracking-tight font-mono ${
                kpiData.needAction > 0 ? "text-amber-600 dark:text-amber-400" : "text-ink"
              }`}
            >
              {loading ? "..." : kpiData.needAction.toLocaleString("vi-VN")}
            </span>
            <span className="text-xs text-muted">đơn chờ duyệt/xuất kho</span>
          </div>
          <p className="mt-2 text-xs text-muted">
            {statusCounts["paid"] || 0} chờ xác nhận · {statusCounts["confirmed"] || 0} chờ xuất kho
          </p>
        </article>

        {/* Card 3: Đang giao hàng */}
        <article className="admin-panel min-w-0 overflow-hidden">
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Đang giao hàng</p>
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-sky-500/15 text-sky-600 dark:text-sky-400">
              <Icon name="truck" size={18} />
            </div>
          </div>
          <p className="mt-3 text-2xl font-bold tracking-tight text-sky-600 dark:text-sky-400 font-mono">
            {loading ? "..." : kpiData.shipping.toLocaleString("vi-VN")}
          </p>
          <p className="mt-2 text-xs text-muted">Shipper đang trên đường vận chuyển</p>
        </article>

        {/* Card 4: Giao thất bại / Boom */}
        <article
          className={`admin-panel min-w-0 overflow-hidden transition ${
            kpiData.boom > 0 ? "border-rose-500/40 bg-rose-500/[0.02]" : ""
          }`}
        >
          <div className="flex items-center justify-between">
            <p className="text-sm font-medium text-muted">Giao thất bại / Boom</p>
            <div
              className={`flex h-9 w-9 items-center justify-center rounded-xl ${
                kpiData.boom > 0 ? "bg-rose-500/15 text-rose-600 dark:text-rose-400" : "bg-sand text-muted"
              }`}
            >
              <Icon name="alert" size={18} />
            </div>
          </div>
          <p
            className={`mt-3 text-2xl font-bold tracking-tight font-mono ${
              kpiData.boom > 0 ? "text-rose-600 dark:text-rose-400" : "text-ink"
            }`}
          >
            {loading ? "..." : kpiData.boom.toLocaleString("vi-VN")}
          </p>
          <p className="mt-2 text-xs text-muted">Cần thu hồi hàng về kho trung tâm</p>
        </article>
      </div>

      {/* Main Operations Shell (Toolbar & Tabs) */}
      <div className="flex flex-col gap-4 rounded-2xl border border-line bg-surface p-4 shadow-sm">
        {/* Search & Channel Toolbar */}
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Icon
              className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-muted"
              name="search"
              size={16}
            />
            <input
              className="admin-input w-full pl-10 pr-9 text-sm"
              onChange={(e) => {
                setSearch(e.target.value);
                setPage(1);
              }}
              placeholder="Tìm theo mã đơn (OD...), tên khách, email..."
              value={search}
            />
            {search ? (
              <button
                aria-label="Xóa tìm kiếm"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-ink"
                onClick={() => {
                  setSearch("");
                  setPage(1);
                }}
                type="button"
              >
                <Icon name="close" size={14} />
              </button>
            ) : null}
          </div>

          {/* Channel Selector Pills */}
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-muted mr-1">Kênh bán:</span>
            <div className="inline-flex rounded-xl border border-line bg-sand/40 p-1">
              <button
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                  channelFilter === "all"
                    ? "bg-ink text-paper shadow-xs"
                    : "text-muted hover:text-ink"
                }`}
                onClick={() => {
                  setChannelFilter("all");
                  setPage(1);
                }}
                type="button"
              >
                Tất cả ({kpiData.totalOrders})
              </button>
              <button
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                  channelFilter === "online"
                    ? "bg-ink text-paper shadow-xs"
                    : "text-muted hover:text-ink"
                }`}
                onClick={() => {
                  setChannelFilter("online");
                  setPage(1);
                }}
                type="button"
              >
                Online 🌐 ({kpiData.online})
              </button>
              <button
                className={`rounded-lg px-3 py-1.5 text-xs font-semibold transition ${
                  channelFilter === "pos"
                    ? "bg-ink text-paper shadow-xs"
                    : "text-muted hover:text-ink"
                }`}
                onClick={() => {
                  setChannelFilter("pos");
                  setPage(1);
                }}
                type="button"
              >
                POS Quầy 🏬 ({kpiData.pos})
              </button>
            </div>
          </div>
        </div>

        {/* Status Tabs Navigation */}
        <div className="flex flex-wrap items-center gap-1.5 border-t border-line/60 pt-3">
          {STATUS_TABS.map((tab) => {
            const count = statusCounts[tab.key] || 0;
            const isActive = status === tab.key;
            const isBoom = tab.key === "failed_delivery";
            const isAction = tab.key === "paid" || tab.key === "confirmed";

            return (
              <button
                key={tab.key}
                className={`inline-flex items-center gap-2 rounded-xl px-3 py-1.5 text-xs font-semibold transition ${
                  isActive
                    ? "bg-accent text-white shadow-xs"
                    : "bg-surface-elevated text-muted hover:bg-sand/60 hover:text-ink"
                }`}
                onClick={() => {
                  setStatus(tab.key);
                  setPage(1);
                }}
                type="button"
              >
                <span>{tab.label}</span>
                <span
                  className={`rounded-full px-1.5 py-0.2 text-[10px] font-bold ${
                    isActive
                      ? "bg-white/20 text-white"
                      : isBoom && count > 0
                        ? "bg-rose-500/15 text-rose-600 dark:text-rose-400"
                        : isAction && count > 0
                          ? "bg-amber-500/15 text-amber-600 dark:text-amber-400"
                          : "bg-sand text-muted"
                  }`}
                >
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Orders Table Container */}
      {loading ? (
        <div className="space-y-3">
          <div className="h-14 animate-pulse rounded-2xl bg-sand/60" />
          <div className="h-72 animate-pulse rounded-2xl bg-sand/40" />
        </div>
      ) : filteredOrders.length === 0 ? (
        <div className="admin-panel text-center py-12 text-muted">
          <Icon className="mx-auto text-muted mb-3 opacity-60" name="receipt" size={32} />
          <h2 className="text-base font-semibold text-ink">Không tìm thấy đơn hàng nào</h2>
          <p className="mt-1 text-sm">
            {search
              ? "Không có đơn hàng nào khớp với từ khóa tìm kiếm của bạn."
              : "Hiện tại không có đơn hàng nào trong bộ lọc này."}
          </p>
          {(search || status || channelFilter !== "all") && (
            <button
              className="button-secondary mt-4 text-xs font-semibold"
              onClick={() => {
                setSearch("");
                setStatus("");
                setChannelFilter("all");
                setPage(1);
              }}
              type="button"
            >
              Đặt lại tất cả bộ lọc
            </button>
          )}
        </div>
      ) : (
        <div className="space-y-4">
          <div className="admin-table-shell overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-line bg-sand/30 text-xs font-medium text-muted uppercase tracking-wider">
                  <th className="py-3 px-4">Đơn hàng</th>
                  <th className="py-3 px-4">Khách hàng</th>
                  <th className="py-3 px-4">Kênh & Thanh toán</th>
                  <th className="py-3 px-4">Tổng tiền</th>
                  <th className="py-3 px-4">Trạng thái</th>
                  <th className="py-3 px-4 text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line">
                {paginatedOrders.map((order) => {
                  const isBusy = busyOrder === order.order_number;

                  return (
                    <tr key={order.order_number} className="hover:bg-sand/20 transition-colors">
                      {/* Mã đơn hàng & Ngày tạo */}
                      <td className="py-3.5 px-4 align-top">
                        <Link
                          className="font-mono font-bold text-accent hover:underline inline-flex items-center gap-1"
                          href={`/admin/orders/${order.order_number}`}
                        >
                          {order.order_number}
                        </Link>
                        <p className="mt-1 text-xs text-muted">
                          {formatVietnamDateTime(order.created_at)}
                        </p>
                        <p className="mt-0.5 text-xs text-muted font-medium">
                          {order.item_count} món hàng
                        </p>
                      </td>

                      {/* Khách hàng */}
                      <td className="py-3.5 px-4 align-top">
                        <p className="font-semibold text-ink">{order.customer_name}</p>
                        <p className="text-xs text-muted truncate max-w-44" title={order.customer_email}>
                          {order.customer_email}
                        </p>
                      </td>

                      {/* Kênh & Phương thức thanh toán */}
                      <td className="py-3.5 px-4 align-top">
                        <div className="flex flex-col gap-1.5 items-start">
                          {/* Channel Badge */}
                          {order.channel === "pos" ? (
                            <span className="inline-flex items-center gap-1 rounded-md border border-purple-500/25 bg-purple-500/10 px-2 py-0.5 text-[11px] font-semibold text-purple-700 dark:text-purple-300">
                              <Icon name="store" size={12} />
                              POS Tại quầy
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-md border border-sky-500/25 bg-sky-500/10 px-2 py-0.5 text-[11px] font-semibold text-sky-700 dark:text-sky-300">
                              Online 🌐
                            </span>
                          )}

                          {/* Payment Method Badge */}
                          {order.payment_method === "cod" ? (
                            <span className="inline-flex items-center gap-1 rounded-md border border-amber-500/25 bg-amber-500/10 px-2 py-0.5 text-[11px] font-semibold text-amber-700 dark:text-amber-400">
                              <Icon name="cash" size={12} />
                              COD Thu hộ
                            </span>
                          ) : (
                            <span className="inline-flex items-center gap-1 rounded-md border border-emerald-500/25 bg-emerald-500/10 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                              <Icon name="check" size={12} />
                              VietQR
                            </span>
                          )}
                        </div>
                      </td>

                      {/* Tổng tiền */}
                      <td className="py-3.5 px-4 align-top">
                        <p className="font-mono font-bold text-ink text-base">
                          {formatVnd(order.total_vnd)}
                        </p>
                      </td>

                      {/* Trạng thái */}
                      <td className="py-3.5 px-4 align-top">
                        <OrderStatusBadge status={order.status} />
                      </td>

                      {/* Thao tác */}
                      <td className="py-3.5 px-4 align-top text-right">
                        <div className="flex flex-col items-end gap-2">
                          <div className="flex flex-wrap items-center justify-end gap-1.5">
                            {order.status === "paid" ? (
                              <>
                                <button
                                  className="button-secondary px-2.5 py-1 text-xs text-danger hover:bg-danger/10"
                                  disabled={isBusy}
                                  onClick={() => handleOpenCancel(order.order_number)}
                                  type="button"
                                >
                                  Hủy
                                </button>
                                <button
                                  className="button-primary px-3 py-1 text-xs inline-flex items-center gap-1"
                                  disabled={isBusy}
                                  onClick={() => handleConfirm(order.order_number)}
                                  type="button"
                                >
                                  <Icon name="check" size={13} />
                                  {isBusy ? "Đang xử lý…" : "Xác nhận"}
                                </button>
                              </>
                            ) : null}

                            {order.status === "confirmed" ? (
                              <>
                                <button
                                  className="button-secondary px-2.5 py-1 text-xs text-danger hover:bg-danger/10"
                                  disabled={isBusy}
                                  onClick={() => handleOpenCancel(order.order_number)}
                                  type="button"
                                >
                                  Hủy
                                </button>
                                <button
                                  className="button-primary px-3 py-1 text-xs inline-flex items-center gap-1"
                                  disabled={isBusy}
                                  onClick={() => void handleOpenDispatch(order.order_number)}
                                  type="button"
                                >
                                  <Icon name="truck" size={13} />
                                  Xuất kho
                                </button>
                              </>
                            ) : null}

                            {order.status === "shipping" ? (
                              <>
                                <button
                                  className="button-secondary px-2.5 py-1 text-xs text-danger hover:bg-danger/10"
                                  disabled={isBusy}
                                  onClick={() => handleOpenBoom(order.order_number)}
                                  type="button"
                                >
                                  <Icon name="alert" size={13} />
                                  Báo Boom
                                </button>
                                <button
                                  className="button-primary px-3 py-1 text-xs inline-flex items-center gap-1"
                                  disabled={isBusy}
                                  onClick={() => handleDeliver(order.order_number)}
                                  type="button"
                                >
                                  <Icon name="check" size={13} />
                                  {isBusy ? "Đang lưu…" : "Giao thành công"}
                                </button>
                              </>
                            ) : null}

                            {order.status === "delivered" ? (
                              <button
                                className="button-primary px-3 py-1 text-xs inline-flex items-center gap-1"
                                disabled={isBusy}
                                onClick={() => handleComplete(order.order_number)}
                                type="button"
                              >
                                <Icon name="check" size={13} />
                                {isBusy ? "Đang lưu…" : "Hoàn tất đơn"}
                              </button>
                            ) : null}
                          </div>

                          <Link
                            className="text-xs text-muted hover:text-accent font-medium hover:underline inline-flex items-center gap-1"
                            href={`/admin/orders/${order.order_number}`}
                          >
                            Chi tiết đơn hàng →
                          </Link>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          {/* Pagination & Footer Controls */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between px-2 text-xs text-muted">
            <div className="flex items-center gap-2">
              <span>
                Hiển thị{" "}
                <span className="font-semibold text-ink">
                  {(currentPage - 1) * pageSize + 1}
                </span>{" "}
                -{" "}
                <span className="font-semibold text-ink">
                  {Math.min(currentPage * pageSize, filteredOrders.length)}
                </span>{" "}
                trong tổng số{" "}
                <span className="font-semibold text-ink font-mono">{filteredOrders.length}</span> đơn hàng
              </span>
              <span className="text-line">|</span>
              <label className="flex items-center gap-1.5" htmlFor="admin-order-page-size">
                <span>Số hàng:</span>
                <select
                  className="rounded-lg border border-line bg-surface px-2 py-1 text-xs text-ink"
                  id="admin-order-page-size"
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setPage(1);
                  }}
                  value={pageSize}
                >
                  <option value={10}>10</option>
                  <option value={15}>15</option>
                  <option value={25}>25</option>
                  <option value={50}>50</option>
                </select>
              </label>
            </div>

            {/* Navigation buttons */}
            {totalPages > 1 && (
              <div className="flex items-center gap-1.5">
                <button
                  className="button-secondary px-2.5 py-1 text-xs"
                  disabled={currentPage <= 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  type="button"
                >
                  ← Trước
                </button>
                <span className="px-2 font-mono font-medium text-ink">
                  {currentPage} / {totalPages}
                </span>
                <button
                  className="button-secondary px-2.5 py-1 text-xs"
                  disabled={currentPage >= totalPages}
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  type="button"
                >
                  Sau →
                </button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Cancel Order Modal */}
      <AdminModal
        busy={busyOrder === cancellingOrder}
        description={`Hủy đơn hàng ${cancellingOrder}. Thao tác này sẽ cập nhật trạng thái đơn sang "Đã hủy" và không thể khôi phục.`}
        onClose={() => setCancellingOrder(null)}
        open={Boolean(cancellingOrder)}
        title={`Hủy đơn hàng: ${cancellingOrder}`}
      >
        <label className="field-label" htmlFor="cancel-reason">
          Lý do hủy đơn <span className="text-danger">*</span>
          <textarea
            autoFocus
            className="form-control"
            id="cancel-reason"
            maxLength={500}
            onChange={(e) => setCancelReason(e.target.value)}
            placeholder="Ví dụ: Khách yêu cầu hủy, hết hàng tồn kho..."
            rows={3}
            value={cancelReason}
          />
        </label>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="button-ghost"
            disabled={busyOrder === cancellingOrder}
            onClick={() => setCancellingOrder(null)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-danger"
            disabled={cancelReason.trim().length < 3 || busyOrder === cancellingOrder}
            onClick={submitCancel}
            type="button"
          >
            {busyOrder === cancellingOrder ? "Đang hủy…" : "Xác nhận hủy đơn"}
          </button>
        </div>
      </AdminModal>

      {/* Dispatch Modal */}
      <AdminModal
        busy={busyOrder === dispatchingOrder}
        description={`Xuất kho và bàn giao đơn ${dispatchingOrder} cho nhân viên vận chuyển.`}
        onClose={() => setDispatchingOrder(null)}
        open={Boolean(dispatchingOrder)}
        title={`Xuất kho & Giao hàng: ${dispatchingOrder}`}
      >
        {loadingStaff ? (
          <div className="py-6 text-center text-sm text-muted">
            <Icon className="animate-spin mx-auto text-accent mb-2" name="rotate-ccw" size={20} />
            Đang tải danh sách nhân viên giao hàng…
          </div>
        ) : staffError ? (
          <div className="feedback-error">{staffError}</div>
        ) : activeStaff.length === 0 ? (
          <div className="admin-panel text-center text-muted">
            <Icon className="mx-auto text-muted mb-2" name="alert" size={20} />
            <p>Hiện không có nhân viên giao hàng nào đang hoạt động.</p>
            <p className="mt-1 text-xs">
              Vui lòng tạo hoặc kích hoạt nhân viên giao hàng tại trang{" "}
              <Link className="font-medium text-ink underline" href="/admin/logistics">
                Quản lý Vận chuyển
              </Link>
              .
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <label className="field-label" htmlFor="dispatch-staff">
              Nhân viên giao hàng <span className="text-danger">*</span>
              <select
                className="admin-input"
                id="dispatch-staff"
                onChange={(e) => setSelectedStaffId(Number(e.target.value))}
                value={selectedStaffId ?? ""}
              >
                {activeStaff.map((staff) => (
                  <option key={staff.staff_id} value={staff.staff_id}>
                    {staff.full_name} ({staff.phone}) {staff.vehicle_plate ? `· ${staff.vehicle_plate}` : ""}
                  </option>
                ))}
              </select>
            </label>
            <label className="field-label" htmlFor="dispatch-notes">
              Ghi chú giao hàng (không bắt buộc)
              <textarea
                className="form-control"
                id="dispatch-notes"
                maxLength={500}
                onChange={(e) => setDispatchNotes(e.target.value)}
                placeholder="Ví dụ: Giao giờ hành chính, gọi trước khi đến..."
                rows={3}
                value={dispatchNotes}
              />
            </label>
          </div>
        )}
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="button-ghost"
            disabled={busyOrder === dispatchingOrder}
            onClick={() => setDispatchingOrder(null)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-primary"
            disabled={!selectedStaffId || busyOrder === dispatchingOrder || activeStaff.length === 0}
            onClick={submitDispatch}
            type="button"
          >
            <Icon name="truck" size={16} />
            {busyOrder === dispatchingOrder ? "Đang xuất kho…" : "Xác nhận giao hàng"}
          </button>
        </div>
      </AdminModal>

      {/* Boom / Failed Delivery Modal */}
      <AdminModal
        busy={busyOrder === boomingOrder}
        description={`Ghi nhận giao thất bại cho đơn ${boomingOrder}. Hệ thống sẽ cập nhật trạng thái đơn sang "Giao thất bại", hoàn tồn kho và tăng bộ đếm boom nếu thanh toán COD.`}
        onClose={() => setBoomingOrder(null)}
        open={Boolean(boomingOrder)}
        title={`Báo Boom hàng: ${boomingOrder}`}
      >
        <label className="field-label" htmlFor="boom-reason">
          Lý do giao hàng thất bại <span className="text-danger">*</span>
          <input
            autoFocus
            className="form-control"
            id="boom-reason"
            maxLength={255}
            onChange={(e) => setBoomReason(e.target.value)}
            placeholder="Ví dụ: Khách không nghe máy, từ chối nhận hàng..."
            value={boomReason}
          />
        </label>
        <div className="mt-6 flex justify-end gap-3">
          <button
            className="button-ghost"
            disabled={busyOrder === boomingOrder}
            onClick={() => setBoomingOrder(null)}
            type="button"
          >
            Bỏ qua
          </button>
          <button
            className="button-accent"
            disabled={boomReason.trim().length === 0 || busyOrder === boomingOrder}
            onClick={submitBoom}
            type="button"
          >
            <Icon name="alert" size={16} />
            {busyOrder === boomingOrder ? "Đang cập nhật…" : "Xác nhận Boom hàng"}
          </button>
        </div>
      </AdminModal>
    </section>
  );
}
