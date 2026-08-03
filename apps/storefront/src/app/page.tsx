import Image from "next/image";
import Link from "next/link";

import { Icon, type IconName } from "@/components/ui/Icon";

const collections = [
  {
    number: "01",
    title: "Thanh lịch mỗi ngày",
    description: "Phom dáng gọn gàng, linh hoạt từ công sở đến buổi hẹn cuối ngày.",
    classes: "border-accent/20 bg-accent/[0.08]",
  },
  {
    number: "02",
    title: "Mềm mại & tự do",
    description: "Bảng màu nhẹ, chất liệu thoải mái và chuyển động tự nhiên.",
    classes: "border-moss/20 bg-moss/[0.08]",
  },
  {
    number: "03",
    title: "Điểm nhấn cá tính",
    description: "Đường nét rõ ràng và những chi tiết vừa đủ để tạo dấu ấn riêng.",
    classes: "border-line bg-sand/55",
  },
] as const;

const promises: ReadonlyArray<{ icon: IconName; value: string; label: string }> = [
  { icon: "truck", value: "500K", label: "Miễn phí vận chuyển từ" },
  { icon: "shield", value: "VND", label: "Giá và thanh toán minh bạch" },
  { icon: "package", value: "LIVE", label: "Tồn kho cập nhật trực tiếp" },
];

export default function HomePage() {
  return (
    <main className="overflow-hidden">
      <section className="mx-auto grid max-w-6xl gap-10 px-5 py-10 sm:px-6 sm:py-16 lg:grid-cols-[1.02fr_0.98fr] lg:items-center lg:gap-16 lg:py-20">
        <div className="relative z-10">
          <div className="inline-flex min-h-10 items-center gap-2 rounded-full border border-line bg-surface px-4 text-xs font-semibold uppercase tracking-[0.18em] text-moss shadow-sm">
            <Icon name="sparkles" size={16} />
            New season · 2026
          </div>
          <h1 className="mt-7 max-w-2xl font-serif text-5xl leading-[0.96] tracking-[-0.05em] text-ink sm:text-6xl lg:text-7xl">
            Mỗi ngày,
            <span className="block italic text-accent">một phong cách riêng.</span>
          </h1>
          <p className="mt-7 max-w-xl text-base leading-7 text-muted sm:text-lg sm:leading-8">
            D&K mang đến trang phục nữ tối giản, hiện đại và dễ phối để bạn tự tin tạo nên phong cách của chính mình.
          </p>
          <div className="mt-8 flex flex-col gap-3 min-[420px]:flex-row">
            <Link className="button-primary" href="/products">
              Khám phá bộ sưu tập
              <Icon name="arrow-right" size={18} />
            </Link>
            <Link className="button-secondary" href="/wishlist">
              <Icon name="heart" size={18} />
              Xem yêu thích
            </Link>
          </div>
          <p className="mt-8 flex max-w-md items-center gap-3 text-sm leading-6 text-muted">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-moss/10 text-moss">
              <Icon name="sparkles" size={18} />
            </span>
            Chọn màu sắc và phom dáng phù hợp với phong cách riêng của bạn.
          </p>
        </div>

        <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
          <div className="absolute -left-10 top-12 hidden h-40 w-40 rounded-full border border-accent/15 bg-accent/10 sm:block" />
          <div className="absolute -right-12 bottom-8 hidden h-48 w-48 rounded-full border border-moss/15 bg-moss/10 sm:block" />
          <div className="relative overflow-hidden rounded-[2.5rem] border border-line bg-surface p-3 shadow-lift">
            <Image
              alt="Bộ sưu tập thời trang nữ tối giản của D&K"
              className="aspect-[4/5] w-full rounded-[2rem] object-cover"
              height={800}
              priority
              src="/dk-hero.svg"
              width={640}
            />
            <div className="absolute bottom-7 left-7 rounded-2xl border border-white/60 bg-surface/95 px-4 py-3 shadow-soft backdrop-blur">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Selected look</p>
              <p className="mt-1 font-serif text-xl">The Signature Line</p>
            </div>
          </div>
          <div className="absolute -right-2 top-8 rotate-3 rounded-full bg-ink px-4 py-2 text-xs font-semibold uppercase tracking-widest text-paper shadow-soft sm:-right-5">
            D&K / 26
          </div>
        </div>
      </section>

      <section className="border-y border-line bg-surface">
        <div className="mx-auto grid max-w-6xl divide-y divide-line px-5 sm:grid-cols-3 sm:divide-x sm:divide-y-0 sm:px-6">
          {promises.map(({ icon, value, label }) => (
            <div className="flex items-center gap-4 py-6 sm:justify-center sm:px-5" key={value}>
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-paper text-accent">
                <Icon name={icon} size={20} />
              </span>
              <span>
                <strong className="block text-sm text-ink">{value}</strong>
                <span className="text-sm text-muted">{label}</span>
              </span>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 py-16 sm:px-6 sm:py-24">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="eyebrow">D&K Collections</p>
            <h2 className="mt-3 max-w-xl font-serif text-4xl leading-tight tracking-[-0.035em] sm:text-5xl">Chọn cảm hứng cho hôm nay</h2>
          </div>
          <Link className="inline-flex min-h-11 items-center gap-2 text-sm font-semibold text-moss hover:text-accent" href="/products">
            Xem tất cả sản phẩm
            <Icon name="arrow-right" size={17} />
          </Link>
        </div>

        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {collections.map((collection) => (
            <Link
              className={`group relative min-h-72 overflow-hidden rounded-[2rem] border p-6 transition duration-200 hover:-translate-y-1 hover:shadow-soft ${collection.classes}`}
              href="/products"
              key={collection.number}
            >
              <span className="text-xs font-semibold tracking-[0.2em] text-muted">COLLECTION {collection.number}</span>
              <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full border border-surface/70 bg-surface/30 transition duration-300 group-hover:scale-110" />
              <div className="relative mt-24 max-w-xs">
                <h3 className="font-serif text-3xl leading-tight">{collection.title}</h3>
                <p className="mt-3 text-sm leading-6 text-muted">{collection.description}</p>
                <span className="mt-5 inline-flex items-center gap-2 text-sm font-semibold text-ink">
                  Khám phá <Icon name="arrow-right" size={16} />
                </span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-5 pb-16 sm:px-6 sm:pb-24">
        <div className="relative overflow-hidden rounded-[2.5rem] bg-ink px-7 py-12 text-paper shadow-lift sm:px-12 sm:py-16 lg:px-16">
          <div className="absolute -right-24 -top-32 h-96 w-96 rounded-full border border-paper/10 bg-accent/80" />
          <div className="absolute -bottom-44 right-40 h-80 w-80 rounded-full border border-paper/10 bg-moss" />
          <div className="relative max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-paper/60">Create your own line</p>
            <h2 className="mt-4 font-serif text-4xl leading-tight tracking-[-0.03em] sm:text-5xl">Phong cách không cần ồn ào để được nhận ra.</h2>
            <p className="mt-5 max-w-xl leading-7 text-paper/70">
              Bắt đầu từ những thiết kế vừa vặn, lưu lại món đồ yêu thích và hoàn thiện tủ đồ theo cách riêng.
            </p>
            <Link className="mt-7 inline-flex min-h-11 items-center gap-2 rounded-full bg-paper px-6 py-2.5 text-sm font-semibold text-ink transition hover:bg-white" href="/products">
              Bắt đầu mua sắm <Icon name="arrow-right" size={17} />
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
