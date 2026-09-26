"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useCallback, useEffect, useMemo, useState } from "react";

import { QuickViewModal } from "@/components/QuickViewModal";
import { Icon } from "@/components/ui/Icon";
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
import { getColorHex, getColorLabel, getColorMeta } from "@/lib/colors";

interface AppliedFilters {
  q: string;
  category: string;
  sizes: string[];
  colors: string[];
  minPrice?: number;
  maxPrice?: number;
  inStock: boolean;
  sort: ProductSort;
}

function filtersFromSearchParams(searchParams: Pick<URLSearchParams, "get" | "getAll">): AppliedFilters {
  const parsePrice = (value: string | null) => {
    if (!value) return undefined;
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined;
  };
  const requestedSort = searchParams.get("sort");
  const sort: ProductSort =
    requestedSort === "price_asc" || requestedSort === "price_desc"
      ? requestedSort
      : "newest";

  const rawSizes = searchParams.getAll("size");
  const sizes = rawSizes.flatMap((s) => s.split(",")).map((s) => s.trim()).filter(Boolean);

  const rawColors = searchParams.getAll("color");
  const colors = rawColors.flatMap((c) => c.split(",")).map((c) => c.trim()).filter(Boolean);

  return {
    q: searchParams.get("q")?.trim() ?? "",
    category: searchParams.get("category") ?? "",
    sizes,
    colors,
    minPrice: parsePrice(searchParams.get("min_price")),
    maxPrice: parsePrice(searchParams.get("max_price")),
    inStock: searchParams.get("in_stock") === "true",
    sort,
  };
}

function filtersToSearchParams(filters: AppliedFilters): URLSearchParams {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.category) params.set("category", filters.category);
  filters.sizes.forEach((s) => params.append("size", s));
  filters.colors.forEach((c) => params.append("color", c));
  if (filters.minPrice !== undefined) params.set("min_price", String(filters.minPrice));
  if (filters.maxPrice !== undefined) params.set("max_price", String(filters.maxPrice));
  if (filters.inStock) params.set("in_stock", "true");
  if (filters.sort !== "newest") params.set("sort", filters.sort);
  return params;
}

function toProductQuery(filters: AppliedFilters, cursor?: string): ProductQuery {
  return {
    q: filters.q || undefined,
    category: filters.category || undefined,
    sizes: filters.sizes.length > 0 ? filters.sizes : undefined,
    colors: filters.colors.length > 0 ? filters.colors : undefined,
    minPrice: filters.minPrice,
    maxPrice: filters.maxPrice,
    inStock: filters.inStock,
    sort: filters.sort,
    cursor,
  };
}

function ProductsContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const applied = useMemo(() => filtersFromSearchParams(searchParams), [searchParams]);
  const { customer } = useAuth();

  const [categories, setCategories] = useState<Category[]>([]);
  const [facets, setFacets] = useState<CatalogFacets>({
    sizes: [],
    colors: [],
    min_price_vnd: null,
    max_price_vnd: null,
  });

  const [query, setQuery] = useState(applied.q);
  const [category, setCategory] = useState(applied.category);
  const [selectedSizes, setSelectedSizes] = useState<string[]>(applied.sizes);
  const [selectedColors, setSelectedColors] = useState<string[]>(applied.colors);
  const [minPrice, setMinPrice] = useState(applied.minPrice?.toString() ?? "");
  const [maxPrice, setMaxPrice] = useState(applied.maxPrice?.toString() ?? "");
  const [inStock, setInStock] = useState(applied.inStock);
  const [sort, setSort] = useState<ProductSort>(applied.sort);

  const [items, setItems] = useState<ProductListItem[]>([]);
  const [cursor, setCursor] = useState<string | null>(null);
  const [wishlistIds, setWishlistIds] = useState<Set<string>>(new Set());
  const [wishlistBusy, setWishlistBusy] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [facetsError, setFacetsError] = useState<string | null>(null);

  // Quick view state
  const [quickViewSlug, setQuickViewSlug] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([getCategories(), getCatalogFacets()])
      .then(([categoryRows, facetData]) => {
        setCategories(categoryRows);
        setFacets(facetData);
        setFacetsError(null);
      })
      .catch((requestError) => {
        setFacetsError(
          requestError instanceof ApiError
            ? requestError.message
            : "Không tải được danh mục và bộ lọc sản phẩm"
        );
      });
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
      .catch((requestError) => {
        setError(
          requestError instanceof ApiError
            ? requestError.message
            : "Không tải được danh sách yêu thích"
        );
      });
  }, [customer]);

  useEffect(() => {
    setQuery(applied.q);
    setCategory(applied.category);
    setSelectedSizes(applied.sizes);
    setSelectedColors(applied.colors);
    setMinPrice(applied.minPrice?.toString() ?? "");
    setMaxPrice(applied.maxPrice?.toString() ?? "");
    setInStock(applied.inStock);
    setSort(applied.sort);
  }, [applied]);

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

  function toggleSize(sizeValue: string) {
    setSelectedSizes((prev) =>
      prev.includes(sizeValue) ? prev.filter((s) => s !== sizeValue) : [...prev, sizeValue]
    );
  }

  function toggleColor(colorValue: string) {
    setSelectedColors((prev) =>
      prev.includes(colorValue) ? prev.filter((c) => c !== colorValue) : [...prev, colorValue]
    );
  }

  function applyFilters(event?: FormEvent<HTMLFormElement>) {
    if (event) event.preventDefault();
    const parsedMin = minPrice === "" ? undefined : Number(minPrice);
    const parsedMax = maxPrice === "" ? undefined : Number(maxPrice);
    if (parsedMin !== undefined && parsedMax !== undefined && parsedMin > parsedMax) {
      setError("Giá tối thiểu không được lớn hơn giá tối đa.");
      return;
    }
    const nextFilters: AppliedFilters = {
      q: query.trim(),
      category,
      sizes: selectedSizes,
      colors: selectedColors,
      minPrice: parsedMin,
      maxPrice: parsedMax,
      inStock,
      sort,
    };
    const params = filtersToSearchParams(nextFilters);
    router.replace(params.size > 0 ? `/products?${params.toString()}` : "/products", { scroll: false });
    setFiltersOpen(false);
  }

  function resetFilters() {
    setQuery("");
    setCategory("");
    setSelectedSizes([]);
    setSelectedColors([]);
    setMinPrice("");
    setMaxPrice("");
    setInStock(false);
    setSort("newest");
    router.replace("/products", { scroll: false });
  }

  function removeSingleFilter(type: keyof AppliedFilters, value?: string) {
    const updated: AppliedFilters = { ...applied };
    if (type === "q") updated.q = "";
    else if (type === "category") updated.category = "";
    else if (type === "sizes" && value) updated.sizes = updated.sizes.filter((s) => s !== value);
    else if (type === "colors" && value) updated.colors = updated.colors.filter((c) => c !== value);
    else if (type === "minPrice") updated.minPrice = undefined;
    else if (type === "maxPrice") updated.maxPrice = undefined;
    else if (type === "inStock") updated.inStock = false;

    const params = filtersToSearchParams(updated);
    router.replace(params.size > 0 ? `/products?${params.toString()}` : "/products", { scroll: false });
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

  const categoryNameMap = useMemo(() => {
    const map = new Map<string, string>();
    categories.forEach((c) => map.set(c.code, c.name));
    return map;
  }, [categories]);

  // Compute active filters count and tags
  const hasActiveFilters =
    Boolean(applied.q) ||
    Boolean(applied.category) ||
    applied.sizes.length > 0 ||
    applied.colors.length > 0 ||
    applied.minPrice !== undefined ||
    applied.maxPrice !== undefined ||
    applied.inStock;

  return (
    <main className="page-shell">
      {/* Catalog Header */}
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">D&K Editorial Collection</p>
          <h1 className="page-heading mt-2">Bộ Sưu Tập Thời Trang</h1>
          <p className="mt-2 max-w-xl text-sm leading-6 text-muted sm:text-base">
            Khám phá phom dáng tinh tế, chất liệu cao cấp và bảng màu trang nhã được tuyển chọn.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <p className="text-sm font-medium text-muted" aria-live="polite">
            {loading && items.length === 0
              ? "Đang tìm sản phẩm…"
              : `${items.length.toLocaleString("vi-VN")} sản phẩm`}
          </p>
          <button
            aria-expanded={filtersOpen}
            className="button-secondary px-4 lg:hidden inline-flex items-center gap-2"
            onClick={() => setFiltersOpen((current) => !current)}
            type="button"
          >
            <Icon name={filtersOpen ? "close" : "filter"} size={17} />
            {filtersOpen ? "Đóng bộ lọc" : "Bộ lọc"}
          </button>
        </div>
      </header>

      {/* Active Filter Chips Bar */}
      {hasActiveFilters && (
        <div className="mt-6 flex flex-wrap items-center gap-2 rounded-2xl border border-line bg-paper/60 p-3 sm:px-4">
          <span className="text-xs font-semibold uppercase tracking-wider text-muted mr-1">
            Đang lọc:
          </span>
          {applied.q && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-ink shadow-2xs">
              Từ khóa: &quot;{applied.q}&quot;
              <button
                aria-label="Xóa lọc từ khóa"
                className="text-muted hover:text-accent"
                onClick={() => removeSingleFilter("q")}
                type="button"
              >
                <Icon name="close" size={13} />
              </button>
            </span>
          )}
          {applied.category && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-ink shadow-2xs">
              {categoryNameMap.get(applied.category) || applied.category}
              <button
                aria-label="Xóa lọc danh mục"
                className="text-muted hover:text-accent"
                onClick={() => removeSingleFilter("category")}
                type="button"
              >
                <Icon name="close" size={13} />
              </button>
            </span>
          )}
          {applied.sizes.map((s) => (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-ink shadow-2xs"
              key={s}
            >
              Size: {s}
              <button
                aria-label={`Xóa lọc size ${s}`}
                className="text-muted hover:text-accent"
                onClick={() => removeSingleFilter("sizes", s)}
                type="button"
              >
                <Icon name="close" size={13} />
              </button>
            </span>
          ))}
          {applied.colors.map((c) => (
            <span
              className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-ink shadow-2xs"
              key={c}
            >
              <span
                className="h-2.5 w-2.5 rounded-full border border-black/10 inline-block"
                style={{ backgroundColor: getColorHex(c) }}
              />
              Màu: {getColorLabel(c)}
              <button
                aria-label={`Xóa lọc màu ${c}`}
                className="text-muted hover:text-accent"
                onClick={() => removeSingleFilter("colors", c)}
                type="button"
              >
                <Icon name="close" size={13} />
              </button>
            </span>
          ))}
          {applied.minPrice !== undefined && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-ink shadow-2xs">
              Từ {formatVnd(applied.minPrice)}
              <button
                aria-label="Xóa lọc giá tối thiểu"
                className="text-muted hover:text-accent"
                onClick={() => removeSingleFilter("minPrice")}
                type="button"
              >
                <Icon name="close" size={13} />
              </button>
            </span>
          )}
          {applied.maxPrice !== undefined && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-ink shadow-2xs">
              Đến {formatVnd(applied.maxPrice)}
              <button
                aria-label="Xóa lọc giá tối đa"
                className="text-muted hover:text-accent"
                onClick={() => removeSingleFilter("maxPrice")}
                type="button"
              >
                <Icon name="close" size={13} />
              </button>
            </span>
          )}
          {applied.inStock && (
            <span className="inline-flex items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1 text-xs font-medium text-emerald-800 shadow-2xs">
              Chỉ còn hàng
              <button
                aria-label="Xóa lọc tồn kho"
                className="text-muted hover:text-accent"
                onClick={() => removeSingleFilter("inStock")}
                type="button"
              >
                <Icon name="close" size={13} />
              </button>
            </span>
          )}

          <button
            className="ml-auto text-xs font-semibold text-accent hover:underline px-2 py-1"
            onClick={resetFilters}
            type="button"
          >
            Xóa tất cả
          </button>
        </div>
      )}

      {/* Main Layout */}
      <div className="mt-8 grid items-start gap-8 lg:grid-cols-[18rem_minmax(0,1fr)]">
        {/* Filter Sidebar */}
        <form
          className={`${
            filtersOpen ? "block" : "hidden"
          } surface-card p-6 lg:sticky lg:top-24 lg:block`}
          onSubmit={applyFilters}
        >
          <div className="flex items-center justify-between border-b border-line pb-4">
            <div className="flex items-center gap-2">
              <Icon className="text-moss" name="filter" size={18} />
              <h2 className="font-semibold text-ink">Bộ lọc tìm kiếm</h2>
            </div>
            <button
              className="text-xs font-semibold text-accent hover:underline py-1"
              onClick={resetFilters}
              type="button"
            >
              Đặt lại
            </button>
          </div>

          <div className="mt-5 space-y-5">
            {/* Keyword Search */}
            <div>
              <label className="text-xs font-semibold text-ink uppercase tracking-wider block" htmlFor="catalog-search">
                Tìm kiếm
              </label>
              <div className="mt-1.5 relative">
                <input
                  className="form-control text-sm pr-9"
                  id="catalog-search"
                  maxLength={100}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Áo sơ mi, quần kaki..."
                  type="search"
                  value={query}
                />
                <button
                  aria-label="Tìm kiếm"
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-muted hover:text-accent"
                  type="submit"
                >
                  <Icon name="search" size={16} />
                </button>
              </div>
            </div>

            {/* Categories */}
            <div>
              <label className="text-xs font-semibold text-ink uppercase tracking-wider block" htmlFor="catalog-category">
                Danh mục sản phẩm
              </label>
              <select
                className="form-control mt-1.5 text-sm"
                id="catalog-category"
                onChange={(event) => setCategory(event.target.value)}
                value={category}
              >
                <option value="">Tất cả danh mục</option>
                {categories.map((item) => (
                  <option key={item.code} value={item.code}>
                    {item.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Multi-select Sizes */}
            {facets.sizes.length > 0 && (
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-ink uppercase tracking-wider">
                    Kích cỡ (Size)
                  </span>
                  {selectedSizes.length > 0 && (
                    <span className="text-[11px] text-accent font-medium">
                      Đã chọn ({selectedSizes.length})
                    </span>
                  )}
                </div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {facets.sizes.map((s) => {
                    const isSelected = selectedSizes.includes(s);
                    return (
                      <button
                        aria-pressed={isSelected}
                        className={`min-h-8 min-w-9 rounded-lg border px-2.5 py-1 text-xs font-semibold transition ${
                          isSelected
                            ? "border-ink bg-ink text-paper shadow-2xs"
                            : "border-line bg-paper text-ink hover:border-ink/40"
                        }`}
                        key={s}
                        onClick={() => toggleSize(s)}
                        type="button"
                      >
                        {s}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Multi-select Colors */}
            {facets.colors.length > 0 && (
              <div>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-ink uppercase tracking-wider">
                    Màu sắc
                  </span>
                  {selectedColors.length > 0 && (
                    <span className="text-[11px] text-accent font-medium">
                      Đã chọn ({selectedColors.length})
                    </span>
                  )}
                </div>
                <div className="mt-2.5 flex flex-wrap gap-2">
                  {facets.colors.map((c) => {
                    const meta = getColorMeta(c);
                    const isSelected = selectedColors.includes(c);
                    return (
                      <button
                        aria-label={`Màu ${meta.label}`}
                        className={`group relative flex h-7 w-7 items-center justify-center rounded-full border transition ${
                          isSelected
                            ? "ring-2 ring-accent ring-offset-2 border-transparent scale-105"
                            : "border-line hover:scale-105"
                        }`}
                        key={c}
                        onClick={() => toggleColor(c)}
                        style={{ backgroundColor: meta.hex }}
                        title={meta.label}
                        type="button"
                      >
                        {isSelected && (
                          <Icon
                            className={meta.isLight ? "text-ink" : "text-white"}
                            name="check"
                            size={11}
                          />
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Price Range */}
            <div>
              <span className="text-xs font-semibold text-ink uppercase tracking-wider block">
                Khoảng giá (VNĐ)
              </span>
              <div className="mt-1.5 grid grid-cols-2 gap-2">
                <input
                  className="form-control text-xs"
                  min={0}
                  onChange={(event) => setMinPrice(event.target.value)}
                  placeholder="Từ..."
                  type="number"
                  value={minPrice}
                />
                <input
                  className="form-control text-xs"
                  min={0}
                  onChange={(event) => setMaxPrice(event.target.value)}
                  placeholder="Đến..."
                  type="number"
                  value={maxPrice}
                />
              </div>
            </div>

            {/* Sort Order */}
            <div>
              <label className="text-xs font-semibold text-ink uppercase tracking-wider block" htmlFor="catalog-sort">
                Sắp xếp
              </label>
              <select
                className="form-control mt-1.5 text-sm"
                id="catalog-sort"
                onChange={(event) => setSort(event.target.value as ProductSort)}
                value={sort}
              >
                <option value="newest">Mới nhất</option>
                <option value="price_asc">Giá: Thấp đến Cao</option>
                <option value="price_desc">Giá: Cao đến Thấp</option>
              </select>
            </div>

            {/* In stock toggle */}
            <label className="flex items-center gap-3 rounded-xl border border-line bg-paper p-3 text-xs font-medium text-ink cursor-pointer hover:bg-sand/30 transition">
              <input
                checked={inStock}
                className="h-4 w-4 accent-accent rounded"
                onChange={(event) => setInStock(event.target.checked)}
                type="checkbox"
              />
              Chỉ hiển thị sản phẩm còn hàng
            </label>
          </div>

          <button className="button-accent mt-6 w-full py-2.5" type="submit">
            <Icon name="search" size={16} />
            Áp dụng bộ lọc
          </button>
        </form>

        {/* Product Grid Section */}
        <section className="min-w-0" aria-label="Danh sách sản phẩm">
          {facetsError ? <div className="feedback-error mb-5" role="alert">{facetsError}</div> : null}
          {error ? <div className="feedback-error mb-5" role="alert">{error}</div> : null}

          <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3">
            {items.map((product) => {
              const wishlisted = wishlistIds.has(product.public_id);
              return (
                <article
                  key={product.public_id}
                  className="group relative flex flex-col justify-between overflow-hidden rounded-3xl border border-line bg-surface shadow-soft transition duration-300 hover:-translate-y-1 hover:shadow-lift"
                >
                  {/* Top Badges & Actions */}
                  <div className="relative aspect-[4/5] overflow-hidden bg-sand/40">
                    {/* Status Badge */}
                    <span
                      className={`absolute left-3 top-3 z-10 inline-flex rounded-full px-2.5 py-0.5 text-[11px] font-semibold backdrop-blur-md shadow-2xs ${
                        product.in_stock
                          ? "bg-emerald-950/80 text-emerald-300 border border-emerald-500/20"
                          : "bg-rose-950/80 text-rose-300 border border-rose-500/20"
                      }`}
                    >
                      {product.in_stock ? "Sẵn hàng" : "Tạm hết"}
                    </span>

                    {/* Wishlist Button */}
                    <button
                      aria-label={wishlisted ? "Xóa khỏi yêu thích" : "Thêm vào yêu thích"}
                      className={`absolute right-3 top-3 z-10 flex h-10 w-10 items-center justify-center rounded-full border shadow-sm backdrop-blur transition ${
                        wishlisted
                          ? "border-accent/25 bg-surface text-accent"
                          : "border-white/70 bg-surface/90 text-ink hover:text-accent hover:scale-105"
                      }`}
                      disabled={wishlistBusy.has(product.public_id)}
                      onClick={(e) => {
                        e.preventDefault();
                        void toggleWishlist(product);
                      }}
                      type="button"
                    >
                      <Icon filled={wishlisted} name="heart" size={18} />
                    </button>

                    {/* Product Image Link */}
                    <Link className="block h-full w-full" href={`/products/${product.slug}`}>
                      {product.image_url ? (
                        <Image
                          alt={product.name}
                          className="object-cover transition duration-500 group-hover:scale-[1.04]"
                          fill
                          sizes="(min-width: 1280px) 25vw, (min-width: 640px) 45vw, 100vw"
                          src={product.image_url}
                        />
                      ) : (
                        <span className="flex h-full items-center justify-center text-sm text-muted">
                          Chưa có ảnh
                        </span>
                      )}
                    </Link>

                    {/* Quick View Button on Hover */}
                    <button
                      aria-label={`Xem nhanh ${product.name}`}
                      className="absolute inset-x-4 bottom-4 z-10 flex items-center justify-center gap-1.5 rounded-xl bg-surface/95 py-2.5 text-xs font-semibold text-ink shadow-md backdrop-blur-md transition duration-200 opacity-0 group-hover:opacity-100 sm:translate-y-2 group-hover:translate-y-0 hover:bg-ink hover:text-paper"
                      onClick={() => setQuickViewSlug(product.slug)}
                      type="button"
                    >
                      <Icon name="eye" size={15} />
                      Xem nhanh
                    </button>
                  </div>

                  {/* Card Body */}
                  <div className="p-5 flex-1 flex flex-col justify-between">
                    <div>
                      <p className="eyebrow text-[10px]">
                        {categoryNameMap.get(product.category_code) || product.category_code}
                      </p>
                      <h2 className="mt-1 font-serif text-lg leading-snug text-ink line-clamp-1 group-hover:text-accent transition">
                        <Link href={`/products/${product.slug}`}>{product.name}</Link>
                      </h2>
                    </div>

                    <div className="mt-4 pt-3 border-t border-line/60 flex items-center justify-between">
                      <div>
                        <span className="text-xs text-muted block">Giá từ</span>
                        <span className="font-semibold text-ink text-base">
                          {formatVnd(product.min_price_vnd)}
                        </span>
                      </div>

                      <Link
                        aria-label={`Chi tiết ${product.name}`}
                        className="flex h-9 w-9 items-center justify-center rounded-full border border-line bg-paper text-muted transition group-hover:border-accent group-hover:text-accent group-hover:translate-x-0.5"
                        href={`/products/${product.slug}`}
                      >
                        <Icon name="arrow-right" size={16} />
                      </Link>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>

          {/* Loading Skeletons */}
          {loading && items.length === 0 ? (
            <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 xl:grid-cols-3" aria-label="Đang tải sản phẩm">
              {[0, 1, 2, 3, 4, 5].map((item) => (
                <div className="aspect-[4/5] animate-pulse rounded-3xl border border-line bg-sand/60" key={item} />
              ))}
            </div>
          ) : null}

          {/* Empty State */}
          {!loading && items.length === 0 ? (
            <div className="surface-card p-12 text-center my-8">
              <span className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-paper text-moss border border-line">
                <Icon name="search" size={26} />
              </span>
              <h2 className="mt-5 text-2xl font-serif text-ink">Không tìm thấy sản phẩm</h2>
              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">
                Không có sản phẩm nào thỏa mãn các bộ lọc đã chọn. Hãy thử xóa bớt tiêu chí lọc hoặc thay đổi khoảng giá.
              </p>
              <button className="button-secondary mt-6" onClick={resetFilters} type="button">
                Xóa toàn bộ bộ lọc
              </button>
            </div>
          ) : null}

          {/* Pagination / Cursor Load More */}
          {cursor ? (
            <div className="mt-12 flex justify-center">
              <button
                className="button-secondary px-8 py-3 rounded-full text-sm font-semibold shadow-2xs hover:shadow-soft"
                disabled={loading}
                onClick={() => void load(applied, cursor)}
                type="button"
              >
                {loading ? "Đang tải thêm…" : "Tải thêm sản phẩm"}
              </button>
            </div>
          ) : null}
        </section>
      </div>

      {/* Quick View Modal */}
      <QuickViewModal
        isOpen={Boolean(quickViewSlug)}
        onClose={() => setQuickViewSlug(null)}
        slug={quickViewSlug}
      />
    </main>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<main className="page-shell"><div className="surface-card h-80 animate-pulse" /></main>}>
      <ProductsContent />
    </Suspense>
  );
}
