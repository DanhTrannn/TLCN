"use client";

import { useCallback, useEffect, useState } from "react";

import { AdminModal } from "@/components/admin/AdminModal";
import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  archiveAdminProduct,
  createAdminProduct,
  formatVnd,
  getAdminProducts,
  getCategories,
  updateAdminProduct,
  updateAdminVariant,
  type AdminProduct,
  type AdminVariant,
  type Category,
} from "@/lib/api";
import { formatVietnamDateTime } from "@/lib/datetime";

const DEFAULT_PRODUCT_IMAGE_URL =
  "https://sixdo.vn/modules/uniform/assets/image/aotruoc.webp";

interface DraftVariant {
  sku: string;
  size_code: string;
  color_code: string;
  price_vnd: string;
  opening_on_hand: string;
}

const emptyVariant = (): DraftVariant => ({
  sku: "",
  size_code: "",
  color_code: "",
  price_vnd: "",
  opening_on_hand: "0",
});

function VariantEditor({ variant, onSaved }: { variant: AdminVariant; onSaved: () => Promise<void> }) {
  const [price, setPrice] = useState(String(variant.price_vnd));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function savePrice() {
    const value = Number(price);
    if (!Number.isInteger(value) || value < 0) {
      setError("Giá phải là số nguyên không âm.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await updateAdminVariant(variant.public_id, { price_vnd: value });
      await onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không cập nhật được giá");
    } finally {
      setBusy(false);
    }
  }

  async function toggleActive() {
    setBusy(true);
    setError(null);
    try {
      await updateAdminVariant(variant.public_id, { is_active: !variant.is_active });
      await onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không đổi được trạng thái");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-2xl border border-line bg-paper p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium">{variant.sku}</p>
          <p className="text-xs text-muted">{variant.size_code} / {variant.color_code} · tồn {variant.on_hand}</p>
        </div>
        <button
          className={`min-h-11 rounded-full border px-4 text-xs font-semibold ${
            variant.is_active ? "border-success/20 bg-success/10 text-success" : "border-line bg-paper text-muted"
          }`}
          disabled={busy}
          onClick={toggleActive}
          type="button"
        >
          {variant.is_active ? "Đang bán" : "Ngừng bán"}
        </button>
      </div>
      <div className="mt-3">
        <label className="text-xs text-muted">
          Giá bán
          <div className="mt-1 flex gap-2">
            <input className="min-w-0 flex-1 form-control mt-0 min-h-11" inputMode="numeric" onChange={(event) => setPrice(event.target.value)} value={price} />
            <button className="button-secondary min-h-11 rounded-xl px-3" disabled={busy} onClick={savePrice} type="button">Lưu giá</button>
          </div>
        </label>
      </div>
      {error ? <p className="mt-2 text-xs text-accent">{error}</p> : null}
    </div>
  );
}

function ProductEditor({
  product,
  categories,
  onSaved,
}: {
  product: AdminProduct;
  categories: Category[];
  onSaved: () => Promise<void>;
}) {
  const [name, setName] = useState(product.name);
  const [category, setCategory] = useState(product.category_code);
  const [description, setDescription] = useState(product.description ?? "");
  const [imageUrl, setImageUrl] = useState(product.image_url ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [archiveOpen, setArchiveOpen] = useState(false);
  const [archiveReason, setArchiveReason] = useState("");
  const [archiveError, setArchiveError] = useState<string | null>(null);
  const archivedAt = product.archived_at;
  const archived = archivedAt !== null;

  async function saveProduct() {
    setBusy(true);
    setError(null);
    try {
      await updateAdminProduct(product.public_id, {
        name: name.trim(),
        category_code: category,
        description: description.trim() || null,
        image_url: imageUrl.trim() || null,
      });
      await onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không cập nhật được sản phẩm");
    } finally {
      setBusy(false);
    }
  }

  async function toggleActive() {
    setBusy(true);
    setError(null);
    try {
      await updateAdminProduct(product.public_id, { is_active: !product.is_active });
      await onSaved();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không đổi được trạng thái");
    } finally {
      setBusy(false);
    }
  }

  async function submitArchive(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setArchiveError(null);
    try {
      await archiveAdminProduct(product.public_id, archiveReason.trim());
      setArchiveOpen(false);
      setArchiveReason("");
      await onSaved();
    } catch (err) {
      setArchiveError(err instanceof ApiError ? err.message : "Không xóa được sản phẩm");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="admin-panel">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-muted">{product.slug}</p>
          <h3 className="mt-1 text-xl font-semibold">{product.name}</h3>
          <p className="mt-1 text-sm text-muted">
            {product.variants.length} biến thể · từ {formatVnd(Math.min(...product.variants.map((item) => item.price_vnd)))}
          </p>
        </div>
        {archived ? (
          <span className="inline-flex min-h-11 items-center rounded-full border border-danger/20 bg-danger/5 px-4 text-sm font-semibold text-danger">
            Đã lưu trữ
          </span>
        ) : (
          <div className="flex flex-wrap gap-2">
            <button
              className={`min-h-11 rounded-full border px-4 text-sm font-semibold ${
                product.is_active ? "border-success/20 bg-success/10 text-success" : "border-line bg-paper text-muted"
              }`}
              disabled={busy}
              onClick={toggleActive}
              type="button"
            >
              {product.is_active ? "Đang hiển thị" : "Đã ẩn"}
            </button>
            <button
              className="button-secondary px-4 text-danger"
              disabled={busy}
              onClick={() => {
                setArchiveError(null);
                setArchiveReason("");
                setArchiveOpen(true);
              }}
              type="button"
            >
              <Icon name="trash" size={16} />
              Xóa sản phẩm
            </button>
          </div>
        )}
      </div>

      {archived ? (
        <div className="mt-5 rounded-2xl border border-danger/20 bg-danger/5 p-4 text-sm">
          <p className="font-semibold text-danger">
            Lưu trữ lúc {formatVietnamDateTime(archivedAt)}
          </p>
          <p className="mt-2 text-muted">Lý do: {product.archive_reason}</p>
          <p className="mt-2 text-xs leading-5 text-muted">
            Sản phẩm không còn xuất hiện trên cửa hàng; tồn kho, wishlist và lịch sử đơn hàng vẫn được giữ nguyên.
          </p>
        </div>
      ) : (
        <>
          <details className="mt-5">
            <summary className="flex min-h-11 cursor-pointer items-center gap-2 text-sm font-semibold"><Icon name="chevron-right" size={16} />Sửa thông tin chung</summary>
            <div className="mt-4 grid gap-3 md:grid-cols-2">
              <label className="text-sm">Tên<input className="admin-input" onChange={(e) => setName(e.target.value)} value={name} /></label>
              <label className="text-sm">Danh mục<select className="admin-input" onChange={(e) => setCategory(e.target.value)} value={category}>{categories.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
              <label className="text-sm md:col-span-2">URL ảnh<input className="admin-input" onChange={(e) => setImageUrl(e.target.value)} value={imageUrl} /></label>
              <label className="text-sm md:col-span-2">Mô tả<textarea className="admin-input" onChange={(e) => setDescription(e.target.value)} rows={3} value={description} /></label>
            </div>
            <button className="mt-3 button-primary" disabled={busy} onClick={saveProduct} type="button">Lưu sản phẩm</button>
          </details>

          <details className="mt-5 border-t border-line pt-4">
            <summary className="flex min-h-11 cursor-pointer items-center gap-2 text-sm font-semibold text-muted"><Icon name="chevron-right" size={16} />Quản lý {product.variants.length} biến thể</summary>
            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              {product.variants.map((variant) => <VariantEditor key={variant.public_id} onSaved={onSaved} variant={variant} />)}
            </div>
          </details>
        </>
      )}
      {error ? <p className="mt-3 text-sm font-semibold text-accent">{error}</p> : null}

      <AdminModal
        busy={busy}
        description="Sản phẩm sẽ bị ẩn vĩnh viễn khỏi cửa hàng, nhưng dữ liệu tồn kho, wishlist và đơn hàng cũ vẫn được giữ để đối soát."
        onClose={() => setArchiveOpen(false)}
        open={archiveOpen}
        title={`Xóa sản phẩm ${product.name}?`}
      >
        <form className="space-y-5" onSubmit={submitArchive}>
          <label className="field-label" htmlFor={`archive-product-${product.public_id}`}>
            Lý do xóa
            <textarea
              autoFocus
              className="admin-input"
              id={`archive-product-${product.public_id}`}
              maxLength={500}
              minLength={3}
              onChange={(event) => setArchiveReason(event.target.value)}
              placeholder="Ví dụ: Ngừng kinh doanh sản phẩm"
              required
              rows={3}
              value={archiveReason}
            />
          </label>
          {archiveError ? <div className="feedback-error" role="alert">{archiveError}</div> : null}
          <div className="flex flex-col-reverse gap-2 border-t border-line pt-5 sm:flex-row sm:justify-end">
            <button className="button-secondary" disabled={busy} onClick={() => setArchiveOpen(false)} type="button">Hủy</button>
            <button className="button-accent" disabled={busy || archiveReason.trim().length < 3} type="submit">
              <Icon name="trash" size={16} />
              {busy ? "Đang xóa…" : "Xác nhận xóa"}
            </button>
          </div>
        </form>
      </AdminModal>
    </article>
  );
}

export default function AdminProductsPage() {
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [creating, setCreating] = useState(false);
  const [createOpen, setCreateOpen] = useState(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [category, setCategory] = useState("");
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [imageUrl, setImageUrl] = useState(DEFAULT_PRODUCT_IMAGE_URL);
  const [variants, setVariants] = useState<DraftVariant[]>([emptyVariant()]);

  const loadProducts = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setProducts(await getAdminProducts(debouncedSearch || undefined));
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không tải được sản phẩm");
    } finally {
      setLoading(false);
    }
  }, [debouncedSearch]);

  useEffect(() => {
    getCategories()
      .then((categoryData) => {
        setCategories(categoryData);
        setCategory((current) => current || categoryData[0]?.code || "");
      })
      .catch((requestError) =>
        setError(requestError instanceof ApiError ? requestError.message : "Không tải được danh mục")
      );
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(search.trim()), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  useEffect(() => {
    void loadProducts();
  }, [loadProducts]);

  function updateDraft(index: number, field: keyof DraftVariant, value: string) {
    setVariants((current) =>
      current.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item)
    );
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setCreating(true);
    setCreateError(null);
    try {
      await createAdminProduct({
        category_code: category,
        slug: slug.trim(),
        name: name.trim(),
        description: description.trim() || null,
        image_url: imageUrl.trim() || null,
        variants: variants.map((item) => ({
          sku: item.sku.trim(),
          size_code: item.size_code.trim(),
          color_code: item.color_code.trim(),
          price_vnd: Number(item.price_vnd),
          opening_on_hand: Number(item.opening_on_hand),
        })),
      });
      setSlug("");
      setName("");
      setDescription("");
      setImageUrl(DEFAULT_PRODUCT_IMAGE_URL);
      setVariants([emptyVariant()]);
      await loadProducts();
      setCreateOpen(false);
    } catch (requestError) {
      setCreateError(requestError instanceof ApiError ? requestError.message : "Không tạo được sản phẩm");
    } finally {
      setCreating(false);
    }
  }

  return (
    <section>
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="eyebrow">Catalog operations</p>
          <h1 className="admin-heading mt-2">Quản lý sản phẩm</h1>
          <p className="mt-2 text-sm text-muted">Tìm theo tên, slug hoặc SKU rồi mở đúng sản phẩm cần chỉnh sửa.</p>
        </div>
        <div className="flex shrink-0 flex-col items-start gap-2 sm:items-end">
          <button
            className="button-primary"
            onClick={() => {
              setCreateError(null);
              setCreateOpen(true);
            }}
            type="button"
          >
            <Icon name="plus" size={17} />
            Thêm sản phẩm
          </button>
          <p className="text-xs text-muted">Tối đa 100 kết quả mỗi lần tìm</p>
        </div>
      </div>

      <div className="mt-6 admin-panel">
        <label className="block text-sm font-medium" htmlFor="admin-product-search">Tìm sản phẩm</label>
        <div className="mt-2 flex gap-2">
          <input
            autoComplete="off"
            className="min-w-0 flex-1 form-control mt-0 rounded-2xl px-4 py-3"
            id="admin-product-search"
            onChange={(event) => setSearch(event.target.value)}
            placeholder="Ví dụ: đầm linen, dam-linen hoặc NET-DAM-001"
            type="search"
            value={search}
          />
          {search ? (
            <button
              className="button-secondary rounded-2xl px-4"
              onClick={() => setSearch("")}
              type="button"
            >
              Xóa
            </button>
          ) : null}
        </div>
        <p className="mt-3 text-xs text-muted">
          {loading ? "Đang tìm…" : `${products.length.toLocaleString("vi-VN")} sản phẩm phù hợp`}
        </p>
      </div>

      <AdminModal
        busy={creating}
        description="Nhập thông tin chung và ít nhất một biến thể ban đầu."
        onClose={() => setCreateOpen(false)}
        open={createOpen}
        title="Thêm sản phẩm mới"
      >
        <form className="space-y-5" onSubmit={submit}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="field-label">Tên sản phẩm<input className="admin-input" onChange={(event) => setName(event.target.value)} required value={name} /></label>
            <label className="field-label">Slug<input className="admin-input" onChange={(event) => setSlug(event.target.value.toLowerCase())} pattern="[a-z0-9]+(?:-[a-z0-9]+)*" required value={slug} /></label>
            <label className="field-label">Danh mục<select className="admin-input" onChange={(event) => setCategory(event.target.value)} required value={category}>{categories.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
            <label className="field-label">URL ảnh<input className="admin-input" onChange={(event) => setImageUrl(event.target.value)} type="url" value={imageUrl} /></label>
            <label className="field-label md:col-span-2">Mô tả<textarea className="admin-input" onChange={(event) => setDescription(event.target.value)} rows={3} value={description} /></label>
          </div>
          <div>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h3 className="font-semibold">Biến thể ban đầu</h3>
              <button className="button-ghost px-3 text-accent" onClick={() => setVariants((current) => [...current, emptyVariant()])} type="button"><Icon name="plus" size={16} />Thêm biến thể</button>
            </div>
            <div className="mt-3 space-y-3">
              {variants.map((item, index) => (
                <div className="grid gap-2 rounded-2xl border border-line bg-paper p-3 lg:grid-cols-5" key={index}>
                  <input aria-label="SKU" className="admin-input mt-0" onChange={(event) => updateDraft(index, "sku", event.target.value)} placeholder="SKU" required value={item.sku} />
                  <input aria-label="Size" className="admin-input mt-0" onChange={(event) => updateDraft(index, "size_code", event.target.value)} placeholder="Size" required value={item.size_code} />
                  <input aria-label="Màu" className="admin-input mt-0" onChange={(event) => updateDraft(index, "color_code", event.target.value)} placeholder="Màu" required value={item.color_code} />
                  <input aria-label="Giá" className="admin-input mt-0" min={0} onChange={(event) => updateDraft(index, "price_vnd", event.target.value)} placeholder="Giá VND" required type="number" value={item.price_vnd} />
                  <div className="flex gap-2">
                    <input aria-label="Tồn đầu" className="admin-input mt-0 min-w-0" min={0} onChange={(event) => updateDraft(index, "opening_on_hand", event.target.value)} placeholder="Tồn" required type="number" value={item.opening_on_hand} />
                    {variants.length > 1 ? <button aria-label="Xóa biến thể" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-danger hover:bg-danger/5" onClick={() => setVariants((current) => current.filter((_, itemIndex) => itemIndex !== index))} type="button"><Icon name="close" size={17} /></button> : null}
                  </div>
                </div>
              ))}
            </div>
          </div>
          {createError ? <div className="feedback-error">{createError}</div> : null}
          <div className="flex flex-col-reverse gap-2 border-t border-line pt-5 sm:flex-row sm:justify-end">
            <button className="button-secondary" disabled={creating} onClick={() => setCreateOpen(false)} type="button">Hủy</button>
            <button className="button-accent" disabled={creating} type="submit">
              {creating ? "Đang tạo…" : "Tạo sản phẩm"}
            </button>
          </div>
        </form>
      </AdminModal>

      {error ? <p className="mt-5 text-sm font-semibold text-accent">{error}</p> : null}
      {loading ? (
        <div className="mt-8 space-y-3">
          {[0, 1, 2].map((item) => <div className="h-28 animate-pulse rounded-2xl bg-sand/60" key={item} />)}
        </div>
      ) : products.length > 0 ? (
        <div className="mt-8 space-y-4">
          {products.map((product) => (
            <ProductEditor categories={categories} key={product.public_id} onSaved={loadProducts} product={product} />
          ))}
        </div>
      ) : (
        <div className="mt-8 rounded-2xl border border-dashed border-line bg-surface px-6 py-12 text-center">
          <p className="font-medium">Không tìm thấy sản phẩm</p>
          <p className="mt-2 text-sm text-muted">Thử tên, slug hoặc SKU khác.</p>
        </div>
      )}
    </section>
  );
}
