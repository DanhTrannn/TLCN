"use client";

import { useEffect, useMemo, useState } from "react";

import { AdminModal } from "@/components/admin/AdminModal";
import { Icon } from "@/components/ui/Icon";
import { ApiError, formatVnd, getAdminProducts, type AdminProduct, type AdminVariant } from "@/lib/api";
import { createAdminInboundReceipt } from "@/lib/commerce";

export interface CreateInboundModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

interface StagedInboundItem {
  variant_id: number;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  on_hand: number;
  current_cost_price_vnd: number;
  quantity: number;
  unit_cost_vnd: number;
  new_cost_price_vnd: number;
}

interface FlatVariantOption {
  variant_id: number;
  product_name: string;
  sku: string;
  size_code: string;
  color_code: string;
  on_hand: number;
  cost_price_vnd: number;
}

function calculateNewCostPrice(
  currentQty: number,
  currentCost: number,
  inboundQty: number,
  inboundCost: number
): number {
  const safeCurrentQty = Math.max(0, currentQty);
  if (inboundQty <= 0) return currentCost;
  if (safeCurrentQty > 0) {
    return Math.round(
      (safeCurrentQty * currentCost + inboundQty * inboundCost) /
        (safeCurrentQty + inboundQty)
    );
  }
  return inboundCost;
}

export function CreateInboundModal({
  isOpen,
  onClose,
  onCreated,
}: CreateInboundModalProps) {
  const [batchName, setBatchName] = useState("");
  const [notes, setNotes] = useState("");
  const [items, setItems] = useState<StagedInboundItem[]>([]);

  // Products loading & selection
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [loadingProducts, setLoadingProducts] = useState(false);
  const [productSearch, setProductSearch] = useState("");
  const [selectedVariantId, setSelectedVariantId] = useState<number | "">("");
  const [quantity, setQuantity] = useState<string>("10");
  const [unitCost, setUnitCost] = useState<string>("0");

  // Status & errors
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stagingError, setStagingError] = useState<string | null>(null);

  // Fetch products when modal opens
  useEffect(() => {
    if (!isOpen) return;
    let isCancelled = false;

    async function loadProducts() {
      setLoadingProducts(true);
      try {
        const data = await getAdminProducts();
        if (!isCancelled) {
          setProducts(data);
        }
      } catch (err) {
        if (!isCancelled) {
          setError(
            err instanceof ApiError
              ? err.message
              : "Không tải được danh sách sản phẩm"
          );
        }
      } finally {
        if (!isCancelled) {
          setLoadingProducts(false);
        }
      }
    }

    void loadProducts();

    return () => {
      isCancelled = true;
    };
  }, [isOpen]);

  // Flatten active variants from products
  const flatVariants = useMemo<FlatVariantOption[]>(() => {
    const list: FlatVariantOption[] = [];
    for (const p of products) {
      if (!p.variants) continue;
      for (const v of p.variants) {
        if (v.variant_id !== undefined && v.variant_id !== null) {
          list.push({
            variant_id: v.variant_id,
            product_name: p.name,
            sku: v.sku,
            size_code: v.size_code,
            color_code: v.color_code,
            on_hand: v.on_hand ?? 0,
            cost_price_vnd: v.cost_price_vnd ?? 0,
          });
        }
      }
    }
    return list;
  }, [products]);

  // Filter variants by user search
  const filteredVariants = useMemo(() => {
    const q = productSearch.trim().toLowerCase();
    if (!q) return flatVariants;
    return flatVariants.filter(
      (v) =>
        v.product_name.toLowerCase().includes(q) ||
        v.sku.toLowerCase().includes(q) ||
        v.size_code.toLowerCase().includes(q) ||
        v.color_code.toLowerCase().includes(q)
    );
  }, [flatVariants, productSearch]);

  // Find currently selected variant
  const selectedVariant = useMemo(() => {
    if (selectedVariantId === "") return null;
    return flatVariants.find((v) => v.variant_id === selectedVariantId) || null;
  }, [flatVariants, selectedVariantId]);

  // Live costing calculations
  const parsedQty = Math.max(0, parseInt(quantity, 10) || 0);
  const parsedUnitCost = Math.max(0, parseInt(unitCost, 10) || 0);

  const previewNewCost = useMemo(() => {
    if (!selectedVariant || parsedQty <= 0) return null;
    return calculateNewCostPrice(
      selectedVariant.on_hand,
      selectedVariant.cost_price_vnd,
      parsedQty,
      parsedUnitCost
    );
  }, [selectedVariant, parsedQty, parsedUnitCost]);

  const costDelta = useMemo(() => {
    if (!selectedVariant || previewNewCost === null) return null;
    const delta = previewNewCost - selectedVariant.cost_price_vnd;
    const percent =
      selectedVariant.cost_price_vnd > 0
        ? ((delta / selectedVariant.cost_price_vnd) * 100).toFixed(1)
        : null;
    return { delta, percent };
  }, [selectedVariant, previewNewCost]);

  // Add item to staging list
  function handleAddStagedItem() {
    setStagingError(null);
    if (!selectedVariant) {
      setStagingError("Vui lòng chọn một biến thể sản phẩm.");
      return;
    }
    if (parsedQty <= 0) {
      setStagingError("Số lượng nhập kho phải lớn hơn 0.");
      return;
    }
    if (parsedUnitCost < 0) {
      setStagingError("Đơn giá xưởng không thể âm.");
      return;
    }

    if (items.some((i) => i.variant_id === selectedVariant.variant_id)) {
      setStagingError(
        "Sản phẩm này đã có trong danh sách nhập kho. Hãy xóa mục hiện có nếu muốn điều chỉnh."
      );
      return;
    }

    const newCost = calculateNewCostPrice(
      selectedVariant.on_hand,
      selectedVariant.cost_price_vnd,
      parsedQty,
      parsedUnitCost
    );

    setItems((prev) => [
      ...prev,
      {
        variant_id: selectedVariant.variant_id,
        product_name: selectedVariant.product_name,
        sku: selectedVariant.sku,
        size_code: selectedVariant.size_code,
        color_code: selectedVariant.color_code,
        on_hand: selectedVariant.on_hand,
        current_cost_price_vnd: selectedVariant.cost_price_vnd,
        quantity: parsedQty,
        unit_cost_vnd: parsedUnitCost,
        new_cost_price_vnd: newCost,
      },
    ]);

    // Reset picker
    setSelectedVariantId("");
    setQuantity("10");
    setUnitCost("0");
  }

  function handleRemoveStagedItem(variantId: number) {
    setItems((prev) => prev.filter((i) => i.variant_id !== variantId));
  }

  function handleResetForm() {
    setBatchName("");
    setNotes("");
    setItems([]);
    setSelectedVariantId("");
    setProductSearch("");
    setQuantity("10");
    setUnitCost("0");
    setError(null);
    setStagingError(null);
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);

    const trimmedBatchName = batchName.trim();
    if (!trimmedBatchName) {
      setError("Vui lòng nhập tên đợt sản xuất.");
      return;
    }

    if (items.length === 0) {
      setError("Vui lòng thêm ít nhất một sản phẩm vào danh sách nhập kho.");
      return;
    }

    setSubmitting(true);
    try {
      const idempotencyKey =
        typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
          ? crypto.randomUUID()
          : `inbound-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;

      await createAdminInboundReceipt(
        {
          batch_name: trimmedBatchName,
          notes: notes.trim() || undefined,
          items: items.map((i) => ({
            variant_id: i.variant_id,
            quantity: i.quantity,
            unit_cost_vnd: i.unit_cost_vnd,
          })),
        },
        idempotencyKey
      );

      handleResetForm();
      onCreated();
      onClose();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Tạo phiếu nhập kho thất bại. Vui lòng thử lại."
      );
    } finally {
      setSubmitting(false);
    }
  }

  const totalQuantity = items.reduce((sum, i) => sum + i.quantity, 0);
  const totalProductionCost = items.reduce(
    (sum, i) => sum + i.quantity * i.unit_cost_vnd,
    0
  );

  return (
    <AdminModal
      busy={submitting}
      description="Nhập thành phẩm may mặc từ xưởng sản xuất nội bộ và tự động tính toán lại giá vốn bình quân gia quyền."
      maxWidthClass="w-[min(56rem,calc(100vw-2rem))]"
      onClose={() => {
        if (!submitting) {
          handleResetForm();
          onClose();
        }
      }}
      open={isOpen}
      title="Tạo phiếu nhập kho sản xuất"
    >
      <form className="space-y-6" onSubmit={handleSubmit}>
        {error ? (
          <div className="feedback-error" role="alert">
            <Icon name="alert" size={18} />
            <span>{error}</span>
          </div>
        ) : null}

        {/* Section 1: Batch Info */}
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className="field-label" htmlFor="inbound-batch-name">
              Tên đợt sản xuất <span className="text-danger">*</span>
            </label>
            <input
              autoFocus
              className="admin-input mt-1 w-full"
              id="inbound-batch-name"
              maxLength={150}
              minLength={3}
              onChange={(e) => setBatchName(e.target.value)}
              placeholder="Ví dụ: Lô may áo thun Cotton đợt 3"
              required
              type="text"
              value={batchName}
            />
          </div>

          <div>
            <label className="field-label" htmlFor="inbound-notes">
              Ghi chú xưởng sản xuất (tùy chọn)
            </label>
            <input
              className="admin-input mt-1 w-full"
              id="inbound-notes"
              maxLength={500}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Ghi chú quy cách may, xưởng gia công, mã hợp đồng..."
              type="text"
              value={notes}
            />
          </div>
        </div>

        {/* Section 2: Product Variant Picker & Live Costing */}
        <div className="rounded-2xl border border-line bg-paper/50 p-4 sm:p-5">
          <div className="flex items-center gap-2">
            <Icon className="text-moss" name="package" size={18} />
            <h3 className="text-sm font-semibold uppercase tracking-wider text-ink">
              Thêm sản phẩm xuất xưởng
            </h3>
          </div>

          {stagingError ? (
            <div className="feedback-error mt-3" role="alert">
              <span>{stagingError}</span>
            </div>
          ) : null}

          <div className="mt-4 grid gap-4 lg:grid-cols-12">
            {/* Search & Select Variant */}
            <div className="space-y-2 lg:col-span-6">
              <label className="field-label" htmlFor="inbound-variant-select">
                Chọn biến thể sản phẩm
              </label>

              {/* Variant search filter */}
              <div className="relative">
                <Icon
                  className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted"
                  name="search"
                  size={15}
                />
                <input
                  className="admin-input w-full pl-9 pr-8 text-xs"
                  onChange={(e) => setProductSearch(e.target.value)}
                  placeholder="Lọc theo tên, SKU, size..."
                  type="text"
                  value={productSearch}
                />
                {productSearch ? (
                  <button
                    aria-label="Xóa bộ lọc"
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted hover:text-ink"
                    onClick={() => setProductSearch("")}
                    type="button"
                  >
                    <Icon name="close" size={12} />
                  </button>
                ) : null}
              </div>

              {/* Variant dropdown */}
              <select
                className="admin-input w-full text-xs"
                disabled={loadingProducts}
                id="inbound-variant-select"
                onChange={(e) => {
                  const val = e.target.value;
                  setSelectedVariantId(val ? Number(val) : "");
                  setStagingError(null);
                }}
                value={selectedVariantId}
              >
                <option value="">
                  {loadingProducts
                    ? "-- Đang tải danh sách sản phẩm... --"
                    : filteredVariants.length === 0
                    ? "-- Không tìm thấy biến thể phù hợp --"
                    : "-- Chọn một biến thể sản phẩm --"}
                </option>
                {filteredVariants.map((v) => (
                  <option key={v.variant_id} value={v.variant_id}>
                    {v.product_name} | {v.sku} ({v.size_code}/{v.color_code}) - Tồn: {v.on_hand} - Giá vốn: {formatVnd(v.cost_price_vnd)}
                  </option>
                ))}
              </select>
            </div>

            {/* Quantity input */}
            <div className="lg:col-span-3">
              <label className="field-label" htmlFor="inbound-item-qty">
                Số lượng xuất xưởng
              </label>
              <input
                className="admin-input mt-1 w-full text-sm"
                id="inbound-item-qty"
                min={1}
                onChange={(e) => setQuantity(e.target.value)}
                placeholder="Ví dụ: 50"
                step={1}
                type="number"
                value={quantity}
              />
            </div>

            {/* Unit Cost input */}
            <div className="lg:col-span-3">
              <label className="field-label" htmlFor="inbound-item-cost">
                Đơn giá xưởng (VNĐ)
              </label>
              <input
                className="admin-input mt-1 w-full text-sm font-mono"
                id="inbound-item-cost"
                min={0}
                onChange={(e) => setUnitCost(e.target.value)}
                placeholder="Ví dụ: 120000"
                step={1000}
                type="number"
                value={unitCost}
              />
            </div>
          </div>

          {/* Live Costing Preview Box */}
          {selectedVariant && parsedQty > 0 ? (
            <div className="mt-4 rounded-xl border border-moss/20 bg-moss/5 p-3.5 transition">
              <div className="flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
                <div>
                  <span className="font-semibold text-ink">
                    {selectedVariant.product_name}
                  </span>{" "}
                  <span className="font-mono text-muted">
                    ({selectedVariant.sku} · Size {selectedVariant.size_code} · {selectedVariant.color_code})
                  </span>
                  <div className="mt-1 flex flex-wrap items-center gap-3 text-xs text-muted">
                    <span>
                      Tồn hiện tại: <b className="text-ink">{selectedVariant.on_hand}</b> cái
                    </span>
                    <span>·</span>
                    <span>
                      Đơn giá nhập mới: <b className="text-ink">{formatVnd(parsedUnitCost)}</b>
                    </span>
                    <span>·</span>
                    <span>
                      Thành tiền:{" "}
                      <b className="font-semibold text-accent">
                        {formatVnd(parsedQty * parsedUnitCost)}
                      </b>
                    </span>
                  </div>
                </div>

                {/* Live Weighted Costing Badge */}
                {previewNewCost !== null && costDelta !== null ? (
                  <div className="flex flex-col items-end gap-1">
                    <div className="inline-flex items-center gap-2 rounded-lg border border-moss/30 bg-surface px-3 py-1.5 shadow-sm">
                      <span className="text-xs text-muted">
                        Giá vốn:{" "}
                        <span className="font-mono font-medium text-ink">
                          {formatVnd(selectedVariant.cost_price_vnd)}
                        </span>
                      </span>
                      <Icon className="text-muted" name="arrow-right" size={14} />
                      <span className="text-xs font-bold text-moss">
                        Mới dự kiến:{" "}
                        <span className="font-mono">
                          {formatVnd(previewNewCost)}
                        </span>
                      </span>
                    </div>

                    <div className="text-right">
                      {selectedVariant.cost_price_vnd === 0 ? (
                        <span className="rounded bg-sky-100 px-2 py-0.5 text-[11px] font-semibold text-sky-800">
                          Khởi tạo giá vốn ban đầu
                        </span>
                      ) : costDelta.delta > 0 ? (
                        <span className="rounded bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
                          +{formatVnd(costDelta.delta)} (+{costDelta.percent}%)
                        </span>
                      ) : costDelta.delta < 0 ? (
                        <span className="rounded bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                          -{formatVnd(Math.abs(costDelta.delta))} ({costDelta.percent}%)
                        </span>
                      ) : (
                        <span className="rounded bg-gray-100 px-2 py-0.5 text-[11px] font-medium text-gray-700">
                          Không đổi (0%)
                        </span>
                      )}
                    </div>
                  </div>
                ) : null}
              </div>
            </div>
          ) : null}

          {/* Add button */}
          <div className="mt-3 flex justify-end">
            <button
              className="button-secondary text-xs sm:text-sm"
              disabled={!selectedVariant || parsedQty <= 0 || parsedUnitCost < 0}
              onClick={handleAddStagedItem}
              type="button"
            >
              <Icon name="plus" size={16} />
              Thêm vào danh sách nhập kho
            </button>
          </div>
        </div>

        {/* Section 3: Staged Items Table */}
        <div>
          <div className="flex items-center justify-between pb-2">
            <h3 className="text-sm font-semibold text-ink">
              Danh sách sản phẩm trong đợt nhập ({items.length})
            </h3>
            {items.length > 0 ? (
              <button
                className="text-xs text-muted hover:text-accent hover:underline"
                onClick={() => setItems([])}
                type="button"
              >
                Xóa tất cả
              </button>
            ) : null}
          </div>

          {items.length === 0 ? (
            <div className="rounded-2xl border border-dashed border-line bg-paper/30 py-8 text-center text-sm text-muted">
              Chưa có sản phẩm nào trong đợt nhập. Hãy chọn biến thể ở trên và nhấn &ldquo;Thêm vào danh sách&rdquo;.
            </div>
          ) : (
            <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
              <table className="w-full text-left text-xs sm:text-sm">
                <thead className="border-b border-line bg-paper/60 text-xs uppercase tracking-wider text-muted">
                  <tr>
                    <th className="px-4 py-3">Sản phẩm &amp; Biến thể</th>
                    <th className="px-3 py-3 text-right">SL nhập</th>
                    <th className="px-3 py-3 text-right">Đơn giá xưởng</th>
                    <th className="px-3 py-3 text-right">Thành tiền</th>
                    <th className="px-3 py-3 text-right">Giá vốn mới dự kiến</th>
                    <th className="px-3 py-3 text-center">Xóa</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line">
                  {items.map((item) => (
                    <tr className="hover:bg-paper/30" key={item.variant_id}>
                      <td className="px-4 py-3">
                        <p className="font-semibold text-ink">{item.product_name}</p>
                        <p className="font-mono text-xs text-muted">
                          {item.sku} · Size {item.size_code} · {item.color_code}
                        </p>
                      </td>
                      <td className="px-3 py-3 text-right font-medium text-ink">
                        {item.quantity.toLocaleString("vi-VN")}
                      </td>
                      <td className="px-3 py-3 text-right font-mono text-ink">
                        {formatVnd(item.unit_cost_vnd)}
                      </td>
                      <td className="px-3 py-3 text-right font-mono font-semibold text-accent">
                        {formatVnd(item.quantity * item.unit_cost_vnd)}
                      </td>
                      <td className="px-3 py-3 text-right">
                        <div className="font-mono font-semibold text-moss">
                          {formatVnd(item.new_cost_price_vnd)}
                        </div>
                        <div className="text-[11px] text-muted">
                          (từ {formatVnd(item.current_cost_price_vnd)})
                        </div>
                      </td>
                      <td className="px-3 py-3 text-center">
                        <button
                          aria-label={`Xóa biến thể ${item.sku}`}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-lg text-muted hover:bg-rose-50 hover:text-rose-600"
                          onClick={() => handleRemoveStagedItem(item.variant_id)}
                          type="button"
                        >
                          <Icon name="trash" size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Section 4: Summary Totals */}
        <div className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-line bg-paper/70 px-5 py-4">
          <div>
            <p className="text-xs text-muted uppercase tracking-wider font-semibold">
              Tổng số lượng sản phẩm
            </p>
            <p className="text-lg font-bold text-ink">
              {totalQuantity.toLocaleString("vi-VN")}{" "}
              <span className="text-sm font-normal text-muted">sản phẩm</span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-muted uppercase tracking-wider font-semibold">
              Tổng chi phí sản xuất
            </p>
            <p className="text-xl font-bold font-mono text-accent">
              {formatVnd(totalProductionCost)}
            </p>
          </div>
        </div>

        {/* Section 5: Modal Actions */}
        <div className="flex flex-col-reverse gap-2 border-t border-line pt-4 sm:flex-row sm:justify-end">
          <button
            className="button-secondary"
            disabled={submitting}
            onClick={() => {
              handleResetForm();
              onClose();
            }}
            type="button"
          >
            Hủy
          </button>
          <button
            className="button-primary"
            disabled={submitting || items.length === 0 || !batchName.trim()}
            type="submit"
          >
            {submitting ? (
              <>
                <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-paper border-t-transparent" />
                <span>Đang tạo phiếu nhập...</span>
              </>
            ) : (
              <>
                <Icon name="check" size={16} />
                <span>Xác nhận nhập kho</span>
              </>
            )}
          </button>
        </div>
      </form>
    </AdminModal>
  );
}
