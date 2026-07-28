import Link from "next/link";

const collections = [
  {
    number: "01",
    title: "Thanh lịch mỗi ngày",
    description: "Những phom dáng gọn gàng, dễ mặc từ công sở đến buổi hẹn cuối ngày.",
    classes: "border-[#d9b6a7] bg-[#ead1c6]",
  },
  {
    number: "02",
    title: "Mềm mại & tự do",
    description: "Bảng màu nhẹ, chất liệu thoải mái và chuyển động tự nhiên.",
    classes: "border-[#b7c8bd] bg-[#cfddd3]",
  },
  {
    number: "03",
    title: "Điểm nhấn cá tính",
    description: "Các thiết kế có đường nét rõ ràng để bạn tạo dấu ấn riêng.",
    classes: "border-[#c9b58a] bg-[#dfcfaa]",
  },
] as const;

const promises = [
  ["500K", "Miễn phí vận chuyển từ"],
  ["VND", "Giá và thanh toán minh bạch"],
  ["LIVE", "Tồn kho được cập nhật trực tiếp"],
] as const;

export default function HomePage() {
  return (
    <main className="overflow-hidden">
      <section className="mx-auto grid max-w-6xl gap-10 px-6 py-12 sm:py-16 lg:grid-cols-[1.05fr_0.95fr] lg:items-center lg:gap-16 lg:py-20">
        <div className="relative z-10">
          <div className="inline-flex items-center gap-3 rounded-full border border-ink/10 bg-white/60 px-4 py-2 text-xs font-semibold uppercase tracking-[0.18em] text-moss">
            <span className="h-2 w-2 rounded-full bg-accent" />
            New season / 2026
          </div>
          <h1 className="mt-7 max-w-2xl font-serif text-5xl leading-[0.96] tracking-[-0.045em] text-ink sm:text-6xl lg:text-7xl">
            Mỗi ngày,
            <span className="block italic text-accent">một nét riêng.</span>
          </h1>
          <p className="mt-7 max-w-xl text-base leading-7 text-ink/65 sm:text-lg sm:leading-8">
            NÉT Studio mang đến trang phục nữ tối giản, hiện đại và dễ phối — để bạn tự tin tạo nên phong cách của chính mình.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link className="inline-flex items-center gap-3 rounded-full bg-ink px-6 py-3.5 text-sm font-semibold text-paper transition hover:bg-moss" href="/products">
              Khám phá bộ sưu tập <span aria-hidden="true">→</span>
            </Link>
            <Link className="inline-flex rounded-full border border-ink/20 bg-white/55 px-6 py-3.5 text-sm font-semibold transition hover:border-accent/40 hover:bg-white" href="/wishlist">
              Xem yêu thích
            </Link>
          </div>
          <div className="mt-10 flex items-center gap-4 text-sm text-ink/50">
            <div className="flex -space-x-2" aria-hidden="true">
              <span className="h-8 w-8 rounded-full border-2 border-paper bg-[#c95f36]" />
              <span className="h-8 w-8 rounded-full border-2 border-paper bg-[#42665a]" />
              <span className="h-8 w-8 rounded-full border-2 border-paper bg-[#d9b6a7]" />
            </div>
            <span>Chọn màu sắc phù hợp với nét riêng của bạn</span>
          </div>
        </div>

        <div className="relative mx-auto w-full max-w-lg lg:max-w-none">
          <div className="absolute -left-12 top-14 hidden h-40 w-40 rounded-full border border-accent/20 bg-accent/10 blur-sm sm:block" />
          <div className="absolute -right-16 bottom-8 hidden h-52 w-52 rounded-full border border-moss/15 bg-moss/10 blur-sm sm:block" />
          <div className="relative overflow-hidden rounded-[2.5rem] border border-ink/10 bg-white/50 p-3 shadow-[0_28px_80px_rgba(19,35,31,0.14)]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img className="aspect-[4/5] w-full rounded-[2rem] object-cover" src="/net-studio-hero.svg" alt="Minh họa bộ sưu tập thời trang nữ NÉT Studio" />
            <div className="absolute bottom-7 left-7 rounded-2xl border border-white/50 bg-paper/90 px-4 py-3 shadow-lg backdrop-blur">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-accent">Selected look</p>
              <p className="mt-1 font-serif text-xl">The Signature Line</p>
            </div>
          </div>
          <div className="absolute -right-3 top-8 rotate-6 rounded-full bg-ink px-4 py-2 text-xs font-semibold uppercase tracking-widest text-paper shadow-lg sm:-right-6">
            NÉT / 26
          </div>
        </div>
      </section>

      <section className="border-y border-ink/10 bg-white/45">
        <div className="mx-auto grid max-w-6xl divide-y divide-ink/10 px-6 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          {promises.map(([value, label]) => (
            <div className="flex items-center gap-4 py-6 sm:justify-center sm:px-6" key={value}>
              <span className="text-xl font-semibold text-accent">{value}</span>
              <span className="max-w-40 text-sm leading-5 text-ink/55">{label}</span>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16 sm:py-24">
        <div className="flex flex-col gap-5 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">NÉT Collections</p>
            <h2 className="mt-3 max-w-xl font-serif text-4xl leading-tight sm:text-5xl">Chọn cảm hứng cho hôm nay</h2>
          </div>
          <Link className="text-sm font-semibold text-moss hover:text-accent" href="/products">Xem tất cả sản phẩm →</Link>
        </div>

        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {collections.map((collection) => (
            <Link
              className={`group relative min-h-72 overflow-hidden rounded-[2rem] border p-6 transition duration-300 hover:-translate-y-1 hover:shadow-[0_20px_50px_rgba(19,35,31,0.12)] ${collection.classes}`}
              href="/products"
              key={collection.number}
            >
              <span className="text-xs font-semibold tracking-[0.2em] text-ink/45">COLLECTION {collection.number}</span>
              <div className="absolute -right-10 -top-10 h-40 w-40 rounded-full border border-white/50 bg-white/25 transition duration-500 group-hover:scale-125" />
              <div className="absolute bottom-0 right-0 h-28 w-28 rounded-tl-[5rem] bg-ink/10" />
              <div className="relative mt-24 max-w-xs">
                <h3 className="font-serif text-3xl leading-tight">{collection.title}</h3>
                <p className="mt-3 text-sm leading-6 text-ink/60">{collection.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-16 sm:pb-24">
        <div className="relative overflow-hidden rounded-[2.5rem] bg-ink px-7 py-12 text-paper sm:px-12 sm:py-16 lg:px-16">
          <div className="absolute -right-24 -top-32 h-96 w-96 rounded-full border border-paper/10 bg-accent/80" />
          <div className="absolute -bottom-40 right-36 h-80 w-80 rounded-full border border-paper/10 bg-moss" />
          <div className="relative max-w-2xl">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-paper/55">Create your own line</p>
            <h2 className="mt-4 font-serif text-4xl leading-tight sm:text-5xl">Phong cách không cần ồn ào để được nhận ra.</h2>
            <p className="mt-5 max-w-xl leading-7 text-paper/65">
              Bắt đầu từ những thiết kế vừa vặn với bạn, lưu lại món đồ yêu thích và hoàn thiện tủ đồ theo cách riêng.
            </p>
            <Link className="mt-7 inline-flex rounded-full bg-paper px-6 py-3 text-sm font-semibold text-ink transition hover:bg-white" href="/products">
              Bắt đầu mua sắm
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
