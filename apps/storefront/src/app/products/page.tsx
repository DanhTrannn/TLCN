"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";

import {
  ApiError,
  addWishlistProduct,
  formatVnd,
  getCatalogFacets,
  getCategories,
  getProducts,
  getWishlist,
  removeWishlistProduct,
  type CatalogFacets,
  type Category,
  type ProductListItem,
  type ProductQuery,
  type ProductSort,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";

interface AppliedFilters {
  q: string;
  category: string;
  size: string;
  color: string;
  minPrice?: number;
  maxPrice?: number;
  inStock: boolean;
  sort: ProductSort;
}

const EMPTY_FILTERS: AppliedFilters = {
  q: "",
  category: "",
  size: "",
  color: "",
  inStock: false,
  sort: "newest",
};

function toProductQuery(filters: AppliedFilters, cursor?: string): ProductQuery {
  return {
    q: filters.q || undefined,
    category: filters.category || undefined,
    sizes: filters.size ? [filters.size] : undefined,
    colors: filters.color ? [filters.color] : undefined,
    minPrice: filters.minPrice,
    maxPrice: filters.maxPrice,
    inStock: filters.inStock,
    sort: filters.sort,
    cursor,
  };
}

export default function ProductsPage() {
  const router = useRouter();
  const { customer } = useAuth();
  const [categories, setCategories] = useState<Category[]>([]);
  const [facets, setFacets] = useState<CatalogFacets>({
    sizes: [],
    colors: [],
    min_price_vnd: null,
    max_price_vnd: null,
  });
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [size, setSize] = useState("");
  const [color, setColor] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [inStock, setInStock] = useState(false);
  const [sort, setSort] = useState<ProductSort>("newest");
  const [applied, setApplied] = useState<AppliedFilters>(EMPTY_FILTERS);
  const [items, setItems] = useState<ProductListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [wishlistIds, setWishlistIds] = useState<Set<string>>(new Set());
  const [wishlistBusy, setWishlistBusy] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getCategories(), getCatalogFacets()])
      .then(([categoryRows, facetData]) => {
        setCategories(categoryRows);
        setFacets(facetData);
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!customer) {
      setWishlistIds(new Set());
      return;
    }
    getWishlist()
      .then((wishlist) => {
        setWishlistIds(new Set(wishlist.items.map((item) => item.product_public_id)));
      })
      .catch(() => undefined);
  }, [customer]);

  const load = useCallback(
    async (filters: AppliedFilters, nextCursor?: string) => {
      setLoading(true);
      setError(null);
      try {
        const response = await getProducts(toProductQuery(filters, nextCursor));
        setItems((previous) => (nextCursor ? [...previous, ...response.items] : response.items));
        setCursor(response.next_cursor);
      } catch (requestError) {
        setError(
          requestError instanceof ApiError
            ? requestError.message
            : "Không tải được danh sách sản phẩm"
        );
      } finally {
        setLoading(false);
      }
    },
    []
  );

  useEffect(() => {
    void load(applied);
  }, [applied, load]);

  function applyFilters(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const parsedMin = minPrice === "" ? undefined : Number(minPrice);
    const parsedMax = maxPrice === "" ? undefined : Number(maxPrice);
    if (parsedMin !== undefined && parsedMax !== undefined && parsedMin > parsedMax) {
      setError("Giá tối thiểu không được lớn hơn giá tối đa.");
      return;
    }
    setApplied({
      q: query.trim(),
      category,
      size,
      color,
      minPrice: parsedMin,
      maxPrice: parsedMax,
      inStock,
      sort,
    });
  }

  function resetFilters() {
    setQuery("");
    setCategory("");
    setSize("");
    setColor("");
    setMinPrice("");
    setMaxPrice("");
    setInStock(false);
    setSort("newest");
    setApplied({ ...EMPTY_FILTERS });
  }

  async function toggleWishlist(product: ProductListItem) {
    if (!customer) {
      router.push(`/login?returnTo=${encodeURIComponent("/products")}`);
      return;
    }
    if (wishlistBusy.has(product.public_id)) return;
    const isWishlisted = wishlistIds.has(product.public_id);
    setWishlistBusy((previous) => new Set(previous).add(product.public_id));
    try {
      if (isWishlisted) {
        await removeWishlistProduct(product.public_id);
        setWishlistIds((previous) => {
          const next = new Set(previous);
          next.delete(product.public_id);
          return next;
        });
      } else {
        await addWishlistProduct(product.public_id);
        setWishlistIds((previous) => new Set(previous).add(product.public_id));
      }
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không cập nhật được danh sách yêu thích"
      );
    } finally {
      setWishlistBusy((previous) => {
        const next = new Set(previous);
        next.delete(product.public_id);
        return next;
      });
    }
  }

  return (
    <main className="mx-auto max-w-6xl px-6 py-14">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">Catalog</p>
      <h1 className="mt-3 text-4xl font-semibold">Sản phẩm</h1>

      <form
        className="mt-8 grid gap-4 rounded-3xl border border-ink/10 bg-white/60 p-5 md:grid-cols-4"
        onSubmit={applyFilters}
      >
        <label className="text-sm md:col-span-2">
          Tìm kiếm
          <input
            className="admin-input"
            maxLength={100}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Tên hoặc mô tả sản phẩm"
            value={query}
          />
        </label>
        <label className="text-sm">
          Danh mục
          <select className="admin-input" onChange={(event) => setCategory(event.target.value)} value={category}>
            <option value="">Tất cả</option>
            {categories.map((item) => (
              <option key={item.code} value={item.code}>{item.name}</option>
            ))}
          </select>
        </label>
        <label className="text-sm">
          Sắp xếp
          <select className="admin-input" onChange={(event) => setSort(event.target.value as ProductSort)} value={sort}>
            <option value="newest">Mới nhất</option>
            <option value="price_asc">Giá tăng dần</option>
            <option value="price_desc">Giá giảm dần</option>
          </select>
        </label>
        <label className="text-sm">
          Size
          <select className="admin-input" onChange={(event) => setSize(event.target.value)} value={size}>
            <option value="">Tất cả</option>
            {facets.sizes.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label className="text-sm">
          Màu
          <select className="admin-input" onChange={(event) => setColor(event.target.value)} value={color}>
            <option value="">Tất cả</option>
            {facets.colors.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label className="text-sm">
          Giá từ
          <input className="admin-input" min={0} onChange={(event) => setMinPrice(event.target.value)} placeholder={facets.min_price_vnd?.toString()} type="number" value={minPrice} />
        </label>
        <label className="text-sm">
          Giá đến
          <input className="admin-input" min={0} onChange={(event) => setMaxPrice(event.target.value)} placeholder={facets.max_price_vnd?.toString()} type="number" value={maxPrice} />
        </label>
        <label className="flex items-center gap-2 text-sm md:col-span-2">
          <input checked={inStock} onChange={(event) => setInStock(event.target.checked)} type="checkbox" />
          Chỉ hiển thị sản phẩm còn hàng
        </label>
        <div className="flex gap-3 md:col-span-2 md:justify-end">
          <button className="rounded-full border border-ink/20 px-5 py-2 text-sm" onClick={resetFilters} type="button">Đặt lại</button>
          <button className="rounded-full bg-ink px-5 py-2 text-sm text-paper" type="submit">Áp dụng</button>
        </div>
      </form>

      {error ? <p className="mt-6 text-sm text-accent">{error}</p> : null}

      <div className="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {items.map((product) => {
          const wishlisted = wishlistIds.has(product.public_id);
          return (
            <article key={product.public_id} className="relative rounded-3xl border border-ink/10 bg-white/60 p-5 transition hover:border-ink/30">
              <button
                aria-label={wishlisted ? "Xóa khỏi yêu thích" : "Thêm vào yêu thích"}
                className={`absolute right-8 top-8 z-10 grid h-10 w-10 place-items-center rounded-full border bg-paper/90 text-xl ${wishlisted ? "border-accent text-accent" : "border-ink/20"}`}
                disabled={wishlistBusy.has(product.public_id)}
                onClick={() => void toggleWishlist(product)}
                type="button"
              >
                {wishlisted ? "♥" : "♡"}
              </button>
              <Link href={`/products/${product.slug}`}>
                <div className="aspect-square overflow-hidden rounded-2xl bg-ink/5">
                  {product.image_url ? (
                    // eslint-disable-next-line @next/next/no-img-element
                    <img src={product.image_url} alt={product.name} className="h-full w-full object-cover" />
                  ) : null}
                </div>
                <h2 className="mt-4 font-medium">{product.name}</h2>
                <p className="mt-1 text-sm text-ink/60">{formatVnd(product.min_price_vnd)}</p>
                {product.in_stock ? null : <p className="mt-1 text-xs text-accent">Tạm hết hàng</p>}
              </Link>
            </article>
          );
        })}
      </div>

      {!loading && items.length === 0 ? <p className="mt-10 text-ink/60">Không tìm thấy sản phẩm phù hợp.</p> : null}

      {cursor ? (
        <div className="mt-10 flex justify-center">
          <button className="rounded-full border border-ink/20 px-6 py-2 text-sm disabled:opacity-60" disabled={loading} onClick={() => void load(applied, cursor)} type="button">
            {loading ? "Đang tải…" : "Tải thêm"}
          </button>
        </div>
      ) : null}
    </main>
  );
}
