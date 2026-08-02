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
import { Icon } from "@/components/ui/Icon";
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
  const [filtersOpen, setFiltersOpen] = useState(false);
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
    setFiltersOpen(false);
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
    <main className="page-shell">
      <header className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="eyebrow">D&K Catalog</p>
          <h1 className="page-heading mt-3">Sản phẩm</h1>
          <p className="mt-3 max-w-xl text-sm leading-6 text-muted sm:text-base">
            Tìm phom dáng, màu sắc và mức giá phù hợp với phong cách của bạn.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <p className="text-sm font-medium text-muted" aria-live="polite">
            {loading && items.length === 0 ? "Đang tìm sản phẩm…" : `${items.length.toLocaleString("vi-VN")} sản phẩm`}
          </p>
          <button
            aria-expanded={filtersOpen}
            className="button-secondary px-4 lg:hidden"
            onClick={() => setFiltersOpen((current) => !current)}
            type="button"
          >
            <Icon name={filtersOpen ? "close" : "search"} size={17} />
            {filtersOpen ? "Đóng bộ lọc" : "Bộ lọc"}
          </button>
        </div>
      </header>

      <div className="mt-9 grid items-start gap-6 lg:grid-cols-[17rem_minmax(0,1fr)]">
        <form className={`${filtersOpen ? "block" : "hidden"} surface-flat p-5 lg:sticky lg:top-24 lg:block`} onSubmit={applyFilters}>
          <div className="flex items-center justify-between border-b border-line pb-4">
            <div className="flex items-center gap-2">
              <Icon className="text-moss" name="search" size={18} />
              <h2 className="font-semibold">Tìm và lọc</h2>
            </div>
            <button className="min-h-11 px-2 text-sm font-semibold text-accent hover:underline" onClick={resetFilters} type="button">
              Đặt lại
            </button>
          </div>

          <div className="mt-5 space-y-4">
            <label className="field-label" htmlFor="catalog-search">Tìm kiếm
              <input className="form-control" id="catalog-search" maxLength={100} onChange={(event) => setQuery(event.target.value)} placeholder="Tên hoặc mô tả" type="search" value={query} />
            </label>
            <label className="field-label" htmlFor="catalog-category">Danh mục
              <select className="form-control" id="catalog-category" onChange={(event) => setCategory(event.target.value)} value={category}>
                <option value="">Tất cả danh mục</option>
                {categories.map((item) => <option key={item.code} value={item.code}>{item.name}</option>)}
              </select>
            </label>
            <div className="grid grid-cols-2 gap-3 lg:grid-cols-1">
              <label className="field-label" htmlFor="catalog-size">Size
                <select className="form-control" id="catalog-size" onChange={(event) => setSize(event.target.value)} value={size}>
                  <option value="">Tất cả</option>
                  {facets.sizes.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
              <label className="field-label" htmlFor="catalog-color">Màu
                <select className="form-control" id="catalog-color" onChange={(event) => setColor(event.target.value)} value={color}>
                  <option value="">Tất cả</option>
                  {facets.colors.map((value) => <option key={value} value={value}>{value}</option>)}
                </select>
              </label>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <label className="field-label" htmlFor="catalog-min-price">Giá từ
                <input className="form-control" id="catalog-min-price" min={0} onChange={(event) => setMinPrice(event.target.value)} placeholder={facets.min_price_vnd?.toString()} type="number" value={minPrice} />
              </label>
              <label className="field-label" htmlFor="catalog-max-price">Giá đến
                <input className="form-control" id="catalog-max-price" min={0} onChange={(event) => setMaxPrice(event.target.value)} placeholder={facets.max_price_vnd?.toString()} type="number" value={maxPrice} />
              </label>
            </div>
            <label className="field-label" htmlFor="catalog-sort">Sắp xếp
              <select className="form-control" id="catalog-sort" onChange={(event) => setSort(event.target.value as ProductSort)} value={sort}>
                <option value="newest">Mới nhất</option>
                <option value="price_asc">Giá tăng dần</option>
                <option value="price_desc">Giá giảm dần</option>
              </select>
            </label>
            <label className="flex min-h-11 items-center gap-3 rounded-xl border border-line bg-paper px-3.5 text-sm font-medium text-ink">
              <input checked={inStock} className="h-4 w-4 accent-accent" onChange={(event) => setInStock(event.target.checked)} type="checkbox" />
              Chỉ sản phẩm còn hàng
            </label>
          </div>
          <button className="button-primary mt-5 w-full" type="submit">
            <Icon name="search" size={17} />
            Áp dụng bộ lọc
          </button>
        </form>

        <section className="min-w-0" aria-label="Danh sách sản phẩm">
          {error ? <div className="feedback-error mb-5" role="alert">{error}</div> : null}

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
            {items.map((product) => {
              const wishlisted = wishlistIds.has(product.public_id);
              return (
                <article key={product.public_id} className="group relative overflow-hidden rounded-3xl border border-line bg-surface shadow-sm transition duration-200 hover:-translate-y-1 hover:shadow-soft">
                  <button
                    aria-label={wishlisted ? "Xóa khỏi yêu thích" : "Thêm vào yêu thích"}
                    className={`absolute right-3 top-3 z-10 flex h-11 w-11 items-center justify-center rounded-full border shadow-sm backdrop-blur transition ${wishlisted ? "border-accent/25 bg-surface text-accent" : "border-white/70 bg-surface/90 text-ink hover:text-accent"}`}
                    disabled={wishlistBusy.has(product.public_id)}
                    onClick={() => void toggleWishlist(product)}
                    type="button"
                  >
                    <Icon filled={wishlisted} name="heart" size={19} />
                  </button>
                  <Link className="block" href={`/products/${product.slug}`}>
                    <div className="aspect-[4/5] overflow-hidden bg-sand/55">
                      {product.image_url ? (
                        // eslint-disable-next-line @next/next/no-img-element
                        <img src={product.image_url} alt={product.name} className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.025]" />
                      ) : (
                        <span className="flex h-full items-center justify-center text-sm text-muted">Chưa có ảnh</span>
                      )}
                    </div>
                    <div className="p-5">
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <h2 className="font-serif text-xl leading-6 text-ink">{product.name}</h2>
                          <p className="mt-2 font-semibold text-ink">{formatVnd(product.min_price_vnd)}</p>
                        </div>
                        <Icon className="mt-1 shrink-0 text-muted transition group-hover:translate-x-1 group-hover:text-accent" name="arrow-right" size={18} />
                      </div>
                      <span className={`mt-4 inline-flex rounded-full px-3 py-1 text-xs font-semibold ${product.in_stock ? "bg-success/10 text-success" : "bg-danger/10 text-danger"}`}>
                        {product.in_stock ? "Sẵn hàng" : "Tạm hết hàng"}
                      </span>
                    </div>
                  </Link>
                </article>
              );
            })}
          </div>

          {loading && items.length === 0 ? (
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3" aria-label="Đang tải sản phẩm">
              {[0, 1, 2, 3, 4, 5].map((item) => <div className="aspect-[4/5] animate-pulse rounded-3xl border border-line bg-sand/60" key={item} />)}
            </div>
          ) : null}

          {!loading && items.length === 0 ? (
            <div className="surface-flat p-10 text-center">
              <span className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-paper text-moss"><Icon name="search" size={24} /></span>
              <h2 className="mt-5 text-xl font-semibold">Không tìm thấy sản phẩm</h2>
              <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-muted">Thử bỏ bớt điều kiện hoặc thay đổi khoảng giá để xem thêm lựa chọn.</p>
              <button className="button-secondary mt-6" onClick={resetFilters} type="button">Xóa bộ lọc</button>
            </div>
          ) : null}

          {cursor ? (
            <div className="mt-9 flex justify-center">
              <button className="button-secondary" disabled={loading} onClick={() => void load(applied, cursor)} type="button">
                {loading ? "Đang tải…" : "Xem thêm sản phẩm"}
              </button>
            </div>
          ) : null}
        </section>
      </div>
    </main>
  );
}
