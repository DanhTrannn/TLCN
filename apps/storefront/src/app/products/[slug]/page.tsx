"use client";

import Image from "next/image";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

import { ProductReviews } from "@/components/ProductReviews";
import { SizeGuideModal } from "@/components/SizeGuideModal";
import { StoreAvailabilityBox } from "@/components/StoreAvailabilityBox";
import { Icon } from "@/components/ui/Icon";
import {
  ApiError,
  addWishlistProduct,
  formatVnd,
  getProduct,
  getWishlist,
  removeWishlistProduct,
  type ProductDetail,
  type Variant,
} from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useCartDrawer } from "@/lib/cart-context";
import { getColorMeta } from "@/lib/colors";

export default function ProductDetailPage() {
  const params = useParams<{ slug: string }>();
  const slug = params.slug;
  const router = useRouter();
  const { customer } = useAuth();
  const { addItemAndOpen } = useCartDrawer();

  const [product, setProduct] = useState<ProductDetail | null>(null);
  const [selectedColor, setSelectedColor] = useState<string | null>(null);
  const [selectedSize, setSelectedSize] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [wishlisted, setWishlisted] = useState(false);
  const [wishlistBusy, setWishlistBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [adding, setAdding] = useState(false);
  const [sizeGuideOpen, setSizeGuideOpen] = useState(false);

  // Accordion state
  const [accordionOpen, setAccordionOpen] = useState<{ [key: string]: boolean }>({
    description: true,
    materials: false,
    shipping: false,
  });

  // Sticky Buy Bar on mobile when primary CTA is out of view
  const mainCtaRef = useRef<HTMLButtonElement | null>(null);
  const [showStickyBar, setShowStickyBar] = useState(false);

  useEffect(() => {
    if (!slug) return;
    getProduct(slug)
      .then((loadedProduct) => {
        setProduct(loadedProduct);
        const firstSellable =
          loadedProduct.variants.find((v) => v.in_stock && v.stock_quantity > 0) ??
          loadedProduct.variants[0];
        if (firstSellable) {
          setSelectedColor(firstSellable.color_code);
          setSelectedSize(firstSellable.size_code);
        }
      })
      .catch(() => setError("Không tìm thấy sản phẩm"));
  }, [slug]);

  useEffect(() => {
    if (!customer || !product) {
      setWishlisted(false);
      return;
    }
    getWishlist()
      .then((wishlist) =>
        setWishlisted(wishlist.items.some((item) => item.product_public_id === product.public_id))
      )
      .catch(() => undefined);
  }, [customer, product]);

  // Observer for Mobile Sticky Buy Bar
  useEffect(() => {
    const target = mainCtaRef.current;
    if (!target) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        // Show sticky bar when the main button scrolls out of view
        setShowStickyBar(!entry.isIntersecting);
      },
      { threshold: 0.1 }
    );

    observer.observe(target);
    return () => observer.disconnect();
  }, [product]);

  // Distinct colors
  const availableColors = useMemo(() => {
    if (!product) return [];
    return Array.from(new Set(product.variants.map((v) => v.color_code)));
  }, [product]);

  // Distinct sizes for the currently selected color
  const sizesForColor = useMemo(() => {
    if (!product) return [];
    const sizes = Array.from(new Set(product.variants.map((v) => v.size_code)));
    return sizes.map((size) => {
      const match = product.variants.find(
        (v) => v.color_code === selectedColor && v.size_code === size
      );
      return {
        size,
        inStock: match ? match.in_stock && match.stock_quantity > 0 : false,
        stockQuantity: match ? match.stock_quantity : 0,
      };
    });
  }, [product, selectedColor]);

  // Active resolved variant
  const variant: Variant | undefined = useMemo(() => {
    if (!product) return undefined;
    return product.variants.find(
      (v) => v.color_code === selectedColor && v.size_code === selectedSize
    );
  }, [product, selectedColor, selectedSize]);

  // If selected size is not in stock for new color, auto-select first available size
  useEffect(() => {
    if (!selectedColor || sizesForColor.length === 0) return;
    const currentSizeAvailable = sizesForColor.some(
      (s) => s.size === selectedSize && s.inStock
    );
    if (!currentSizeAvailable) {
      const firstInStockSize = sizesForColor.find((s) => s.inStock);
      if (firstInStockSize) {
        setSelectedSize(firstInStockSize.size);
      }
    }
  }, [selectedColor, sizesForColor, selectedSize]);

  // Ensure quantity does not exceed variant stock
  useEffect(() => {
    if (variant && variant.stock_quantity > 0) {
      if (quantity > variant.stock_quantity) {
        setQuantity(variant.stock_quantity);
      }
    }
  }, [variant, quantity]);

  function toggleAccordion(key: string) {
    setAccordionOpen((prev) => ({ ...prev, [key]: !prev[key] }));
  }

  async function handleAddToCart() {
    if (!variant) return;
    if (!customer) {
      router.push(`/login?returnTo=${encodeURIComponent(`/products/${slug}`)}`);
      return;
    }
    setAdding(true);
    setMessage(null);
    setError(null);
    try {
      await addItemAndOpen(variant.public_id, quantity);
      setMessage(`Đã thêm ${quantity} sản phẩm vào giỏ hàng.`);
    } catch (requestError) {
      setError(requestError instanceof ApiError ? requestError.message : "Không thêm được vào giỏ");
    } finally {
      setAdding(false);
    }
  }

  async function handleWishlist() {
    if (!product) return;
    if (!customer) {
      router.push(`/login?returnTo=${encodeURIComponent(`/products/${slug}`)}`);
      return;
    }
    setWishlistBusy(true);
    setError(null);
    try {
      if (wishlisted) {
        await removeWishlistProduct(product.public_id);
        setWishlisted(false);
      } else {
        await addWishlistProduct(product.public_id);
        setWishlisted(true);
      }
    } catch (requestError) {
      setError(
        requestError instanceof ApiError
          ? requestError.message
          : "Không cập nhật được danh sách yêu thích"
      );
    } finally {
      setWishlistBusy(false);
    }
  }

  if (error && !product) {
    return (
      <main className="page-shell">
        <div className="feedback-error">{error}</div>
      </main>
    );
  }

  if (!product) {
    return (
      <main className="page-shell">
        <div className="grid gap-7 md:grid-cols-2">
          <div className="aspect-[4/5] animate-pulse rounded-3xl bg-sand/60" />
          <div className="h-80 animate-pulse rounded-3xl bg-sand/50" />
        </div>
      </main>
    );
  }

  return (
    <main className="page-shell pb-20 sm:pb-8">
      {/* Breadcrumbs */}
      <nav aria-label="Breadcrumb" className="mb-6 flex items-center gap-2 text-sm text-muted">
        <Link className="min-h-11 content-center hover:text-accent" href="/products">
          Sản phẩm
        </Link>
        <Icon name="chevron-right" size={15} />
        {product.category_name && (
          <>
            <Link
              className="min-h-11 content-center hover:text-accent"
              href={`/products?category=${encodeURIComponent(product.category_name)}`}
            >
              {product.category_name}
            </Link>
            <Icon name="chevron-right" size={15} />
          </>
        )}
        <span className="truncate text-ink font-medium">{product.name}</span>
      </nav>

      <div className="grid gap-8 lg:grid-cols-[1.08fr_0.92fr] lg:gap-12">
        {/* Left Column: Product Gallery */}
        <section className="overflow-hidden rounded-[2rem] border border-line bg-surface p-3 shadow-soft" aria-label="Ảnh sản phẩm">
          <div className="relative aspect-[4/5] overflow-hidden rounded-[1.5rem] bg-sand/50">
            {product.image_url ? (
              <Image
                alt={product.name}
                className="object-cover"
                fill
                priority
                sizes="(min-width: 1024px) 52vw, 100vw"
                src={product.image_url}
              />
            ) : (
              <span className="flex h-full items-center justify-center text-muted">
                Sản phẩm chưa có ảnh
              </span>
            )}
            <span
              className={`absolute left-4 top-4 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-semibold backdrop-blur-md shadow-2xs ${
                variant?.in_stock
                  ? "bg-emerald-950/80 text-emerald-300 border border-emerald-500/20"
                  : "bg-rose-950/80 text-rose-300 border border-rose-500/20"
              }`}
            >
              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  variant?.in_stock ? "bg-emerald-400" : "bg-rose-400"
                }`}
              />
              {variant?.in_stock ? "Sẵn hàng" : "Tạm hết hàng"}
            </span>
          </div>
        </section>

        {/* Right Column: Product Info & Buy Box */}
        <section className="lg:py-3">
          <p className="eyebrow">{product.category_name}</p>
          <div className="mt-2 flex items-start justify-between gap-4">
            <h1 className="font-serif text-3xl leading-tight tracking-[-0.03em] sm:text-4xl text-ink">
              {product.name}
            </h1>
            <button
              aria-label={wishlisted ? "Xóa khỏi yêu thích" : "Thêm vào yêu thích"}
              className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-full border bg-surface shadow-2xs transition ${
                wishlisted
                  ? "border-accent/40 text-accent bg-accent/5"
                  : "border-line text-muted hover:text-accent hover:border-accent/30"
              }`}
              disabled={wishlistBusy}
              onClick={() => void handleWishlist()}
              type="button"
            >
              <Icon filled={wishlisted} name="heart" size={21} />
            </button>
          </div>

          <div className="mt-4 flex items-baseline gap-3">
            <p className="text-3xl font-semibold text-ink">
              {formatVnd(variant?.price_vnd ?? product.variants[0]?.price_vnd ?? null)}
            </p>
          </div>

          {product.description ? (
            <p className="mt-4 text-sm leading-6 text-muted">{product.description}</p>
          ) : null}

          {/* 2-Tier Selection: 1. Color Swatches */}
          {availableColors.length > 0 && (
            <div className="mt-6 border-t border-line pt-6">
              <div className="flex items-center justify-between text-xs">
                <span className="font-semibold text-ink">
                  Màu sắc:{" "}
                  <span className="font-normal text-muted">
                    {getColorMeta(selectedColor).label}
                  </span>
                </span>
                <span className="text-xs text-muted">
                  {availableColors.length} màu sắc có sẵn
                </span>
              </div>
              <div className="mt-3 flex flex-wrap gap-3">
                {availableColors.map((color) => {
                  const meta = getColorMeta(color);
                  const isSelected = selectedColor === color;
                  return (
                    <button
                      aria-label={`Màu ${meta.label}`}
                      className={`group relative flex h-9 w-9 items-center justify-center rounded-full border transition ${
                        isSelected
                          ? "ring-2 ring-accent ring-offset-2 border-transparent scale-105 shadow-sm"
                          : "border-line hover:scale-105 hover:border-ink/40"
                      }`}
                      key={color}
                      onClick={() => setSelectedColor(color)}
                      style={{ backgroundColor: meta.hex }}
                      title={meta.label}
                      type="button"
                    >
                      {isSelected && (
                        <Icon
                          className={meta.isLight ? "text-ink" : "text-white"}
                          name="check"
                          size={14}
                        />
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* 2-Tier Selection: 2. Size Pills */}
          {sizesForColor.length > 0 && (
            <div className="mt-6">
              <div className="flex items-center justify-between gap-4 text-xs">
                <div className="flex items-center gap-3">
                  <span className="font-semibold text-ink">Kích cỡ</span>
                  <button
                    className="inline-flex items-center gap-1 rounded-full border border-line bg-paper px-2.5 py-0.5 text-xs font-medium text-accent transition hover:border-accent/40"
                    onClick={() => setSizeGuideOpen(true)}
                    type="button"
                  >
                    <Icon name="sparkles" size={12} />
                    Bảng kích cỡ
                  </button>
                </div>
                <span
                  className={`text-xs font-semibold ${
                    variant?.in_stock ? "text-success" : "text-danger"
                  }`}
                >
                  {variant?.in_stock ? `Còn ${variant.stock_quantity} sản phẩm` : "Tạm hết hàng"}
                </span>
              </div>

              <div className="mt-3 flex flex-wrap gap-2.5">
                {sizesForColor.map(({ size, inStock, stockQuantity }) => {
                  const isSelected = selectedSize === size;
                  return (
                    <button
                      aria-pressed={isSelected}
                      className={`min-h-11 min-w-14 rounded-xl border px-3.5 py-2 text-xs font-semibold transition ${
                        isSelected
                          ? "border-ink bg-ink text-paper shadow-2xs"
                          : inStock
                          ? "border-line bg-surface text-ink hover:border-ink/40"
                          : "border-line/60 bg-paper/50 text-muted/40 cursor-not-allowed line-through"
                      }`}
                      disabled={!inStock}
                      key={size}
                      onClick={() => setSelectedSize(size)}
                      type="button"
                    >
                      {size}
                      <span className="block text-[10px] font-normal opacity-80">
                        {inStock ? `${stockQuantity} cái` : "Hết"}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Quantity Stepper */}
          <div className="mt-6 flex items-center gap-4">
            <span className="text-xs font-semibold text-ink">Số lượng:</span>
            <div className="flex items-center rounded-xl border border-line bg-surface">
              <button
                aria-label="Giảm số lượng"
                className="flex h-10 w-10 items-center justify-center text-muted transition hover:text-ink disabled:opacity-30"
                disabled={quantity <= 1}
                onClick={() => setQuantity((q) => Math.max(1, q - 1))}
                type="button"
              >
                <Icon name="minus" size={15} />
              </button>
              <span className="w-10 text-center text-sm font-semibold text-ink">
                {quantity}
              </span>
              <button
                aria-label="Tăng số lượng"
                className="flex h-10 w-10 items-center justify-center text-muted transition hover:text-ink disabled:opacity-30"
                disabled={
                  quantity >= (variant?.stock_quantity ?? 1) || !variant?.in_stock
                }
                onClick={() =>
                  setQuantity((q) =>
                    Math.min(variant?.stock_quantity ?? 1, q + 1)
                  )
                }
                type="button"
              >
                <Icon name="plus" size={15} />
              </button>
            </div>
            {variant?.stock_quantity ? (
              <span className="text-xs text-muted">
                (Tối đa {variant.stock_quantity} sản phẩm)
              </span>
            ) : null}
          </div>

          {/* Primary Action Button */}
          <button
            className="button-accent mt-7 w-full shadow-soft"
            disabled={adding || !variant || !variant.in_stock}
            onClick={() => void handleAddToCart()}
            ref={mainCtaRef}
            type="button"
          >
            <Icon name="bag" size={19} />
            {variant?.in_stock
              ? adding
                ? "Đang thêm vào giỏ hàng…"
                : `Thêm vào giỏ hàng · ${formatVnd((variant.price_vnd ?? 0) * quantity)}`
              : "Phiên bản đã hết hàng"}
          </button>

          {/* User Feedback Alerts */}
          <div aria-live="polite" className="mt-4 space-y-3">
            {message ? (
              <div className="feedback-success flex items-center justify-between gap-3">
                <span className="flex items-center gap-2">
                  <Icon name="check" size={18} />
                  {message}
                </span>
                <Link
                  className="font-semibold underline hover:opacity-80 shrink-0 text-xs sm:text-sm"
                  href="/cart"
                >
                  Xem giỏ hàng →
                </Link>
              </div>
            ) : null}
            {error ? <p className="feedback-error">{error}</p> : null}
          </div>

          {/* Trust Guarantees */}
          <div className="mt-7 grid gap-3 border-t border-line pt-6 sm:grid-cols-2">
            <div className="flex gap-3 rounded-2xl bg-surface p-4 shadow-sm border border-line/60">
              <Icon className="shrink-0 text-moss" name="truck" />
              <div>
                <p className="text-sm font-semibold text-ink">Giao hàng miễn phí</p>
                <p className="mt-0.5 text-xs leading-5 text-muted">Cho đơn từ 500.000₫</p>
              </div>
            </div>
            <div className="flex gap-3 rounded-2xl bg-surface p-4 shadow-sm border border-line/60">
              <Icon className="shrink-0 text-moss" name="shield" />
              <div>
                <p className="text-sm font-semibold text-ink">Đổi trả 30 ngày</p>
                <p className="mt-0.5 text-xs leading-5 text-muted">Dễ dàng & miễn phí tận nơi</p>
              </div>
            </div>
          </div>

          {/* Product Information Accordion */}
          <div className="mt-8 divide-y divide-line border-y border-line">
            {/* Accordion Item 1: Description & Silhouette */}
            <div>
              <button
                aria-expanded={accordionOpen.description}
                className="flex w-full items-center justify-between py-4 text-left text-sm font-semibold text-ink hover:text-accent transition"
                onClick={() => toggleAccordion("description")}
                type="button"
              >
                <span>Chi tiết & Phom dáng thiết kế</span>
                <Icon
                  className={`text-muted transition-transform duration-200 ${
                    accordionOpen.description ? "rotate-90" : ""
                  }`}
                  name="chevron-right"
                  size={16}
                />
              </button>
              {accordionOpen.description && (
                <div className="pb-4 text-xs leading-6 text-muted space-y-2">
                  <p>
                    {product.description ||
                      "Thiết kế mang phong cách Editorial Minimalist tôn vinh nét đẹp tinh tế và tiện dụng thường ngày."}
                  </p>
                  <ul className="list-inside list-disc space-y-1 text-muted">
                    <li>Phom dáng vừa vặn (Regular Fit) tôn đường nét tự nhiên</li>
                    <li>Đường may đôi chắc chắn, hoàn thiện tỉ mỉ từng chi tiết</li>
                    <li>Mã dòng sản phẩm: {product.slug}</li>
                  </ul>
                </div>
              )}
            </div>

            {/* Accordion Item 2: Materials & Care */}
            <div>
              <button
                aria-expanded={accordionOpen.materials}
                className="flex w-full items-center justify-between py-4 text-left text-sm font-semibold text-ink hover:text-accent transition"
                onClick={() => toggleAccordion("materials")}
                type="button"
              >
                <span>Chất liệu & Hướng dẫn bảo quản</span>
                <Icon
                  className={`text-muted transition-transform duration-200 ${
                    accordionOpen.materials ? "rotate-90" : ""
                  }`}
                  name="chevron-right"
                  size={16}
                />
              </button>
              {accordionOpen.materials && (
                <div className="pb-4 text-xs leading-6 text-muted space-y-2">
                  <p className="font-medium text-ink">
                    100% sợi cao cấp chọn lọc, mềm mại, thoáng khí và thân thiện với làn da.
                  </p>
                  <ul className="list-inside list-disc space-y-1">
                    <li>Giặt máy ở chế độ nhẹ nhàng với nước lạnh dưới 30°C</li>
                    <li>Không sử dụng hóa chất tẩy rửa mạnh chứa clo</li>
                    <li>Phơi trong bóng râm, tránh ánh nắng trực tiếp gay gắt</li>
                    <li>Là/ủi ở nhiệt độ trung bình (tối đa 150°C)</li>
                  </ul>
                </div>
              )}
            </div>

            {/* Accordion Item 3: Shipping & Returns */}
            <div>
              <button
                aria-expanded={accordionOpen.shipping}
                className="flex w-full items-center justify-between py-4 text-left text-sm font-semibold text-ink hover:text-accent transition"
                onClick={() => toggleAccordion("shipping")}
                type="button"
              >
                <span>Chính sách đổi trả 30 ngày & Giao hàng</span>
                <Icon
                  className={`text-muted transition-transform duration-200 ${
                    accordionOpen.shipping ? "rotate-90" : ""
                  }`}
                  name="chevron-right"
                  size={16}
                />
              </button>
              {accordionOpen.shipping && (
                <div className="pb-4 text-xs leading-6 text-muted space-y-2">
                  <p>
                    D&K cam kết mang lại trải nghiệm mua sắm an tâm tuyệt đối:
                  </p>
                  <ul className="list-inside list-disc space-y-1">
                    <li>Giao hàng nhanh toàn quốc từ 2 - 4 ngày làm việc</li>
                    <li>Đổi hàng miễn phí trong vòng 30 ngày cho sản phẩm còn nguyên tem mác</li>
                    <li>Hỗ trợ xem hàng và thanh toán khi nhận hàng (COD)</li>
                    <li>Trải nghiệm và thử đồ trực tiếp tại hệ thống cửa hàng D&K</li>
                  </ul>
                </div>
              )}
            </div>
          </div>

          {/* Store Availability Checker */}
          <div className="mt-8">
            <StoreAvailabilityBox slug={product.slug} variantPublicId={variant?.public_id ?? null} />
          </div>
        </section>
      </div>

      {/* Customer Reviews Section */}
      <ProductReviews slug={product.slug} />

      {/* Size Guide Modal */}
      <SizeGuideModal
        isOpen={sizeGuideOpen}
        onClose={() => setSizeGuideOpen(false)}
      />

      {/* Mobile Sticky Buy Bar */}
      <div
        className={`sm:hidden fixed bottom-0 left-0 right-0 z-40 border-t border-line bg-surface/95 px-4 py-3 backdrop-blur-md shadow-lift transition-transform duration-300 ${
          showStickyBar ? "translate-y-0" : "translate-y-full"
        }`}
      >
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2.5 min-w-0">
            {product.image_url ? (
              <div className="relative h-11 w-9 shrink-0 overflow-hidden rounded-lg bg-sand/40 border border-line">
                <Image
                  alt={product.name}
                  className="object-cover"
                  fill
                  sizes="36px"
                  src={product.image_url}
                />
              </div>
            ) : null}
            <div className="min-w-0">
              <p className="truncate text-xs font-semibold text-ink">{product.name}</p>
              <p className="text-xs text-muted">
                {selectedColor ? getColorMeta(selectedColor).label : ""}
                {selectedSize ? ` / ${selectedSize}` : ""} ·{" "}
                <span className="font-semibold text-ink">
                  {formatVnd(variant?.price_vnd ?? null)}
                </span>
              </p>
            </div>
          </div>
          <button
            className="button-accent shrink-0 px-4 py-2 text-xs"
            disabled={adding || !variant || !variant.in_stock}
            onClick={() => void handleAddToCart()}
            type="button"
          >
            <Icon name="bag" size={15} />
            {variant?.in_stock ? (adding ? "Thêm…" : "Thêm giỏ") : "Hết hàng"}
          </button>
        </div>
      </div>
    </main>
  );
}
