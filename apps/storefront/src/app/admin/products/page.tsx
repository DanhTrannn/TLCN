"use client";

import { useCallback, useEffect, useState } from "react";

import {
  ApiError,
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
    <div className="rounded-2xl border border-ink/10 bg-paper/60 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <p className="font-medium">{variant.sku}</p>
          <p className="text-xs text-ink/55">{variant.size_code} / {variant.color_code} · tồn {variant.on_hand}</p>
        </div>
        <button
          className={`rounded-full px-3 py-1 text-xs ${
            variant.is_active ? "bg-moss/15 text-moss" : "bg-ink/10 text-ink/55"
          }`}
          disabled={busy}
          onClick={toggleActive}
          type="button"
        >
          {variant.is_active ? "Đang bán" : "Ngừng bán"}
        </button>
      </div>
      <div className="mt-3">
        <label className="text-xs text-ink/60">
          Giá bán
          <div className="mt-1 flex gap-2">
            <input className="min-w-0 flex-1 rounded-lg border border-ink/15 bg-white px-3 py-2 text-sm text-ink" inputMode="numeric" onChange={(event) => setPrice(event.target.value)} value={price} />
            <button className="rounded-lg border border-ink/20 px-3 text-sm" disabled={busy} onClick={savePrice} type="button">Lưu giá</button>
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

  return (
    <article className="rounded-3xl border border-ink/10 bg-white/70 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <p className="text-xs uppercase tracking-wider text-ink/50">{product.slug}</p>
          <h3 className="mt-1 text-xl font-semibold">{product.name}</h3>
          <p className="mt-1 text-sm text-ink/60">
            {product.variants.length} biến thể · từ {formatVnd(Math.min(...product.variants.map((item) => item.price_vnd)))}
          </p>
        </div>
        <button
          className={`rounded-full px-4 py-2 text-sm ${
            product.is_active ? "bg-moss/15 text-moss" : "bg-ink/10 text-ink/55"
          }`}
          disabled={busy}
          onClick={toggleActive}
          type="button"
        >
          {product.is_active ? "Đang hiển thị" : "Đã ẩn"}
        </button>
      </div>

      <details className="mt-5">
        <summary className="cursor-pointer text-sm font-medium">Sửa thông tin chung</summary>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <label className="text-sm">Tên<input className="admin-input" onChange={(e) => setName(e.target.value)} value={name} /></label>
          <label className="text-sm">Danh mục<select className="admin-input" onChange={(e) => setCategory(e.target.value)} value={category}>{categories.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
          <label className="text-sm md:col-span-2">URL ảnh<input className="admin-input" onChange={(e) => setImageUrl(e.target.value)} value={imageUrl} /></label>
          <label className="text-sm md:col-span-2">Mô tả<textarea className="admin-input" onChange={(e) => setDescription(e.target.value)} rows={3} value={description} /></label>
        </div>
        <button className="mt-3 rounded-full bg-ink px-5 py-2 text-sm text-paper" disabled={busy} onClick={saveProduct} type="button">Lưu sản phẩm</button>
      </details>

      <div className="mt-5 grid gap-3 lg:grid-cols-2">
        {product.variants.map((variant) => <VariantEditor key={variant.public_id} onSaved={onSaved} variant={variant} />)}
      </div>
      {error ? <p className="mt-3 text-sm text-accent">{error}</p> : null}
    </article>
  );
}

export default function AdminProductsPage() {
  const [products, setProducts] = useState<AdminProduct[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [category, setCategory] = useState("");
  const [slug, setSlug] = useState("");
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [imageUrl, setImageUrl] = useState("");
  const [variants, setVariants] = useState<DraftVariant[]>([emptyVariant()]);

  const load = useCallback(async () => {
    setError(null);
    try {
      const [productData, categoryData] = await Promise.all([getAdminProducts(), getCategories()]);
      setProducts(productData);
      setCategories(categoryData);
      setCategory((current) => current || categoryData[0]?.code || "");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không tải được sản phẩm");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void load(); }, [load]);

  function updateDraft(index: number, field: keyof DraftVariant, value: string) {
    setVariants((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item));
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setCreating(true);
    setError(null);
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
      setSlug(""); setName(""); setDescription(""); setImageUrl(""); setVariants([emptyVariant()]);
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Không tạo được sản phẩm");
    } finally {
      setCreating(false);
    }
  }

  return (
    <section>
      <details className="rounded-3xl border border-ink/10 bg-white/70 p-5">
        <summary className="cursor-pointer text-lg font-semibold">Thêm sản phẩm mới</summary>
        <form className="mt-5 space-y-4" onSubmit={submit}>
          <div className="grid gap-4 md:grid-cols-2">
            <label className="text-sm">Tên sản phẩm<input className="admin-input" onChange={(e) => setName(e.target.value)} required value={name} /></label>
            <label className="text-sm">Slug<input className="admin-input" onChange={(e) => setSlug(e.target.value.toLowerCase())} pattern="[a-z0-9]+(?:-[a-z0-9]+)*" required value={slug} /></label>
            <label className="text-sm">Danh mục<select className="admin-input" onChange={(e) => setCategory(e.target.value)} required value={category}>{categories.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}</select></label>
            <label className="text-sm">URL ảnh<input className="admin-input" onChange={(e) => setImageUrl(e.target.value)} type="url" value={imageUrl} /></label>
            <label className="text-sm md:col-span-2">Mô tả<textarea className="admin-input" onChange={(e) => setDescription(e.target.value)} rows={3} value={description} /></label>
          </div>
          <div>
            <div className="flex items-center justify-between"><h3 className="font-medium">Biến thể ban đầu</h3><button className="text-sm text-accent" onClick={() => setVariants((current) => [...current, emptyVariant()])} type="button">+ Thêm biến thể</button></div>
            <div className="mt-3 space-y-3">
              {variants.map((item, index) => (
                <div className="grid gap-2 rounded-2xl border border-ink/10 p-3 sm:grid-cols-5" key={index}>
                  <input aria-label="SKU" className="admin-input mt-0" onChange={(e) => updateDraft(index, "sku", e.target.value)} placeholder="SKU" required value={item.sku} />
                  <input aria-label="Size" className="admin-input mt-0" onChange={(e) => updateDraft(index, "size_code", e.target.value)} placeholder="Size" required value={item.size_code} />
                  <input aria-label="Màu" className="admin-input mt-0" onChange={(e) => updateDraft(index, "color_code", e.target.value)} placeholder="Màu" required value={item.color_code} />
                  <input aria-label="Giá" className="admin-input mt-0" min={0} onChange={(e) => updateDraft(index, "price_vnd", e.target.value)} placeholder="Giá VND" required type="number" value={item.price_vnd} />
                  <div className="flex gap-2"><input aria-label="Tồn đầu" className="admin-input mt-0 min-w-0" min={0} onChange={(e) => updateDraft(index, "opening_on_hand", e.target.value)} placeholder="Tồn" required type="number" value={item.opening_on_hand} />{variants.length > 1 ? <button className="text-accent" onClick={() => setVariants((current) => current.filter((_, i) => i !== index))} type="button">×</button> : null}</div>
                </div>
              ))}
            </div>
          </div>
          <button className="rounded-full bg-accent px-6 py-3 text-paper disabled:opacity-50" disabled={creating} type="submit">{creating ? "Đang tạo…" : "Tạo sản phẩm"}</button>
        </form>
      </details>

      {error ? <p className="mt-5 text-sm text-accent">{error}</p> : null}
      {loading ? <p className="mt-8 text-ink/60">Đang tải…</p> : (
        <div className="mt-8 space-y-5">{products.map((product) => <ProductEditor categories={categories} key={product.public_id} onSaved={load} product={product} />)}</div>
      )}
    </section>
  );
}
