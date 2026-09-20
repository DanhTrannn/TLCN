"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { AdminModal } from "@/components/admin/AdminModal";
import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  createDeliveryStaff,
  formatVnd,
  getDeliveryStaffList,
  getShipmentsList,
  patchDeliveryStaff,
  type DeliveryStaff,
  type ShipmentDetail,
} from "@/lib/api";
import { formatVietnamDateTime } from "@/lib/datetime";

const FILTER_TABS = [
  { label: "Tất cả", value: "" },
  { label: "Đang giao", value: "in_transit" },
  { label: "Giao thành công", value: "delivered" },
  { label: "Thất bại", value: "failed" },
] as const;

const SHIPMENT_STATUS_MAP: Record<
  string,
  { label: string; classes: string; dotClass: string }
> = {
  in_transit: {
    label: "Đang giao",
    classes: "border-sky-500/25 bg-sky-500/10 text-sky-700 dark:text-sky-300",
    dotClass: "bg-sky-500",
  },
  delivered: {
    label: "Giao thành công",
    classes: "border-emerald-500/25 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300",
    dotClass: "bg-emerald-500",
  },
  failed: {
    label: "Thất bại",
    classes: "border-rose-500/25 bg-rose-500/10 text-rose-700 dark:text-rose-400",
    dotClass: "bg-rose-500",
  },
};

function safeFormatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  try {
    return formatVietnamDateTime(value);
  } catch {
    return value;
  }
}

function ShipmentStatusBadge({ status }: { status: string }) {
  const config = SHIPMENT_STATUS_MAP[status] ?? {
    label: status,
    classes: "border-line bg-paper text-muted",
    dotClass: "bg-muted",
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-semibold ${config.classes}`}
    >
      <span className={`h-1.5 w-1.5 rounded-full ${config.dotClass}`} />
      {config.label}
    </span>
  );
}

export default function AdminLogisticsPage() {
  // Staff state
  const [staffList, setStaffList] = useState<DeliveryStaff[]>([]);
  const [loadingStaff, setLoadingStaff] = useState(true);
  const [staffError, setStaffError] = useState<string | null>(null);
  const [busyStaffId, setBusyStaffId] = useState<number | null>(null);

  // Add staff modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalBusy, setModalBusy] = useState(false);
  const [modalError, setModalError] = useState<string | null>(null);
  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [vehiclePlate, setVehiclePlate] = useState("");

  // Shipments state
  const [shipments, setShipments] = useState<ShipmentDetail[]>([]);
  const [shipmentFilter, setShipmentFilter] = useState<string>("");
  const [loadingShipments, setLoadingShipments] = useState(true);
  const [shipmentsError, setShipmentsError] = useState<string | null>(null);

  const loadStaff = useCallback(async () => {
    setLoadingStaff(true);
    setStaffError(null);
    try {
      const data = await getDeliveryStaffList();
      setStaffList(data);
    } catch (err) {
      setStaffError(
        err instanceof ApiError ? err.message : "Không tải được danh sách đội ngũ giao hàng."
      );
    } finally {
      setLoadingStaff(false);
    }
  }, []);

  const loadShipments = useCallback(async (statusFilter: string) => {
    setLoadingShipments(true);
    setShipmentsError(null);
    try {
      const data = await getShipmentsList(statusFilter || undefined);
      setShipments(data);
    } catch (err) {
      setShipmentsError(
        err instanceof ApiError ? err.message : "Không tải được danh sách vận đơn."
      );
    } finally {
      setLoadingShipments(false);
    }
  }, []);

  useEffect(() => {
    void loadStaff();
  }, [loadStaff]);

  useEffect(() => {
    void loadShipments(shipmentFilter);
  }, [loadShipments, shipmentFilter]);

  async function handleCreateStaff(event: React.FormEvent) {
    event.preventDefault();
    const trimmedName = fullName.trim();
    const trimmedPhone = phone.trim();
    const trimmedPlate = vehiclePlate.trim();

    if (trimmedName.length < 2) {
      setModalError("Họ và tên phải có ít nhất 2 ký tự.");
      return;
    }
    if (trimmedPhone.length < 8) {
      setModalError("Số điện thoại phải có ít nhất 8 chữ số.");
      return;
    }

    setModalBusy(true);
    setModalError(null);
    try {
      await createDeliveryStaff({
        full_name: trimmedName,
        phone: trimmedPhone,
        vehicle_plate: trimmedPlate || null,
      });
      setIsModalOpen(false);
      setFullName("");
      setPhone("");
      setVehiclePlate("");
      setModalError(null);
      await loadStaff();
    } catch (err) {
      setModalError(
        err instanceof ApiError ? err.message : "Không thể tạo nhân viên giao hàng mới."
      );
    } finally {
      setModalBusy(false);
    }
  }

  function handleCloseModal() {
    if (modalBusy) return;
    setIsModalOpen(false);
    setModalError(null);
    setFullName("");
    setPhone("");
    setVehiclePlate("");
  }

  async function handleToggleStaff(staff: DeliveryStaff) {
    setBusyStaffId(staff.staff_id);
    setStaffError(null);
    try {
      await patchDeliveryStaff(staff.staff_id, { is_active: !staff.is_active });
      await loadStaff();
    } catch (err) {
      setStaffError(
        err instanceof ApiError
          ? err.message
          : "Không cập nhật được trạng thái hoạt động của shipper."
      );
    } finally {
      setBusyStaffId(null);
    }
  }

  return (
    <div className="space-y-10">
      {/* Page Header */}
      <header className="flex flex-col gap-3">
        <p className="eyebrow">Logistics & Đội ngũ vận chuyển</p>
        <h1 className="admin-heading">Quản lý Vận chuyển & Giao hàng</h1>
        <p className="max-w-3xl text-sm leading-6 text-muted">
          Quản lý danh sách nhân viên giao hàng nội bộ D&K và giám sát toàn bộ hành trình
          vận đơn, đối soát tiền thu hộ COD.
        </p>
      </header>

      {/* Phần 1: Quản lý Đội ngũ Shipper D&K */}
      <section className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-ink">Đội ngũ giao hàng</h2>
            <p className="text-sm text-muted">
              Quản lý danh sách nhân viên giao hàng và trạng thái sẵn sàng nhận đơn.
            </p>
          </div>
          <button
            type="button"
            onClick={() => {
              setModalError(null);
              setIsModalOpen(true);
            }}
            className="button-primary self-start sm:self-auto"
          >
            <Icon name="plus" size={17} />
            Thêm Shipper mới
          </button>
        </div>

        {staffError ? <div className="feedback-error">{staffError}</div> : null}

        {loadingStaff ? (
          <div className="h-44 animate-pulse rounded-2xl bg-sand/60" />
        ) : (
          <div className="admin-table-shell">
            <table>
              <thead>
                <tr>
                  <th>Mã shipper</th>
                  <th>Họ tên</th>
                  <th>SĐT</th>
                  <th>Biển số xe</th>
                  <th>Trạng thái hoạt động</th>
                  <th className="text-right">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {staffList.map((staff) => (
                  <tr key={staff.staff_id}>
                    <td>
                      <span className="font-mono text-xs font-semibold text-muted">
                        #{staff.staff_id}
                      </span>
                    </td>
                    <td>
                      <span className="font-semibold text-ink">{staff.full_name}</span>
                    </td>
                    <td>
                      <span className="text-sm text-ink">{staff.phone}</span>
                    </td>
                    <td>
                      <span className="text-sm text-muted">
                        {staff.vehicle_plate || "—"}
                      </span>
                    </td>
                    <td>
                      {staff.is_active ? (
                        <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-1 text-xs font-semibold text-emerald-700 dark:text-emerald-400">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          Đang hoạt động
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-paper px-2.5 py-1 text-xs font-semibold text-muted">
                          <span className="h-1.5 w-1.5 rounded-full bg-muted" />
                          Ngừng hoạt động
                        </span>
                      )}
                    </td>
                    <td className="text-right">
                      <div className="flex items-center justify-end gap-2.5">
                        <button
                          type="button"
                          role="switch"
                          aria-checked={staff.is_active}
                          aria-label={`Bật hoặc tắt trạng thái hoạt động của shipper ${staff.full_name}`}
                          title={
                            staff.is_active ? "Tạm ngưng hoạt động" : "Kích hoạt shipper"
                          }
                          disabled={busyStaffId === staff.staff_id}
                          onClick={() => void handleToggleStaff(staff)}
                          className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus:outline-none focus:ring-2 focus:ring-accent/30 disabled:cursor-not-allowed disabled:opacity-50 ${
                            staff.is_active
                              ? "bg-emerald-600"
                              : "bg-neutral-300 dark:bg-neutral-700"
                          }`}
                        >
                          <span
                            className={`pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
                              staff.is_active ? "translate-x-5" : "translate-x-0"
                            }`}
                          />
                        </button>
                        <button
                          type="button"
                          disabled={busyStaffId === staff.staff_id}
                          onClick={() => void handleToggleStaff(staff)}
                          className={`button-secondary min-h-8 px-3 py-1 text-xs ${
                            staff.is_active
                              ? "text-danger hover:border-danger/40"
                              : "text-emerald-600 hover:border-emerald-500/40"
                          }`}
                        >
                          {busyStaffId === staff.staff_id
                            ? "Đang lưu…"
                            : staff.is_active
                            ? "Tắt"
                            : "Bật"}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {staffList.length === 0 ? (
              <div className="p-10 text-center">
                <Icon className="mx-auto text-muted" name="users" size={32} />
                <p className="mt-3 text-sm font-medium text-ink">
                  Chưa có nhân viên giao hàng nào.
                </p>
                <p className="mt-1 text-xs text-muted">
                  Nhấn &quot;Thêm Shipper mới&quot; để thiết lập đội ngũ giao hàng D&K.
                </p>
              </div>
            ) : null}
          </div>
        )}
      </section>

      {/* Phần 2: Giám sát Vận đơn (Shipments) */}
      <section className="space-y-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <h2 className="text-xl font-bold tracking-tight text-ink">Giám sát vận đơn</h2>
            <p className="text-sm text-muted">
              Theo dõi chi tiết các chuyến giao hàng, tiền thu hộ COD và thời gian xuất kho.
            </p>
          </div>

          {/* Filter Tabs */}
          <div className="flex flex-wrap gap-2">
            {FILTER_TABS.map((tab) => {
              const active = shipmentFilter === tab.value;
              return (
                <button
                  key={tab.value}
                  type="button"
                  onClick={() => setShipmentFilter(tab.value)}
                  className={`rounded-full px-4 py-1.5 text-xs font-semibold transition ${
                    active
                      ? "bg-ink text-paper shadow-sm"
                      : "border border-line bg-surface text-muted hover:border-ink/30 hover:text-ink"
                  }`}
                >
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        {shipmentsError ? <div className="feedback-error">{shipmentsError}</div> : null}

        {loadingShipments ? (
          <div className="h-60 animate-pulse rounded-2xl bg-sand/60" />
        ) : (
          <div className="admin-table-shell">
            <table>
              <thead>
                <tr>
                  <th>Mã vận đơn</th>
                  <th>Mã đơn hàng</th>
                  <th>Shipper phụ trách</th>
                  <th>Trạng thái</th>
                  <th>Tiền COD</th>
                  <th>Thời gian xuất kho</th>
                </tr>
              </thead>
              <tbody>
                {shipments.map((shipment) => (
                  <tr key={shipment.shipment_id}>
                    <td>
                      <span className="font-semibold text-ink">
                        {shipment.shipment_code}
                      </span>
                    </td>
                    <td>
                      <Link
                        className="font-semibold text-accent hover:underline"
                        href={`/admin/orders/${shipment.order_number}`}
                      >
                        {shipment.order_number}
                      </Link>
                    </td>
                    <td>
                      {shipment.delivery_staff_name ? (
                        <div>
                          <p className="font-medium text-ink">
                            {shipment.delivery_staff_name}
                          </p>
                          {shipment.delivery_staff_phone ? (
                            <p className="text-xs text-muted">
                              {shipment.delivery_staff_phone}
                            </p>
                          ) : null}
                        </div>
                      ) : (
                        <span className="text-xs italic text-muted">Chưa phân công</span>
                      )}
                    </td>
                    <td>
                      <ShipmentStatusBadge status={shipment.status} />
                    </td>
                    <td>
                      <span className="font-semibold text-ink">
                        {formatVnd(shipment.cod_amount_vnd)}
                      </span>
                    </td>
                    <td>
                      <span className="text-xs text-muted">
                        {shipment.dispatched_at
                          ? safeFormatDateTime(shipment.dispatched_at)
                          : "Chưa xuất kho"}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {shipments.length === 0 ? (
              <div className="p-10 text-center">
                <Icon className="mx-auto text-muted" name="truck" size={32} />
                <p className="mt-3 text-sm font-medium text-ink">
                  Không có vận đơn nào phù hợp.
                </p>
                <p className="mt-1 text-xs text-muted">
                  Vận đơn sẽ xuất hiện khi đơn hàng được điều phối và xuất kho.
                </p>
              </div>
            ) : null}
          </div>
        )}
      </section>

      {/* Modal Thêm Shipper mới */}
      <AdminModal
        busy={modalBusy}
        description="Nhập thông tin nhân viên giao hàng nội bộ vào hệ thống D&K Logistics."
        onClose={handleCloseModal}
        open={isModalOpen}
        title="Thêm Shipper mới"
      >
        <form className="space-y-4" onSubmit={handleCreateStaff}>
          <label className="field-label" htmlFor="staff-fullname">
            Họ và tên <span className="text-danger">*</span>
            <input
              className="admin-input"
              id="staff-name"
              minLength={2}
              maxLength={100}
              placeholder="Ví dụ: Nguyễn Văn Shipper"
              required
              type="text"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
            />
          </label>

          <label className="field-label" htmlFor="staff-phone">
            Số điện thoại <span className="text-danger">*</span>
            <input
              className="admin-input"
              id="staff-phone"
              minLength={8}
              maxLength={20}
              placeholder="Ví dụ: 0912345678"
              required
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
            />
          </label>

          <label className="field-label" htmlFor="staff-vehicle-plate">
            Biển số xe{" "}
            <span className="text-xs font-normal text-muted">(Không bắt buộc)</span>
            <input
              className="admin-input"
              id="staff-vehicle-plate"
              maxLength={30}
              placeholder="Ví dụ: 29-A1 12345"
              type="text"
              value={vehiclePlate}
              onChange={(e) => setVehiclePlate(e.target.value)}
            />
          </label>

          {modalError ? (
            <div className="feedback-error" role="alert">
              {modalError}
            </div>
          ) : null}

          <div className="flex flex-col-reverse gap-2 border-t border-line pt-5 sm:flex-row sm:justify-end">
            <button
              type="button"
              className="button-secondary"
              disabled={modalBusy}
              onClick={handleCloseModal}
            >
              Hủy
            </button>
            <button
              type="submit"
              className="button-primary"
              disabled={
                modalBusy || fullName.trim().length < 2 || phone.trim().length < 8
              }
            >
              <Icon name="plus" size={17} />
              {modalBusy ? "Đang lưu…" : "Lưu thông tin"}
            </button>
          </div>
        </form>
      </AdminModal>
    </div>
  );
}
