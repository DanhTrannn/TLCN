import Link from "next/link";

const blocks = [
  ["Source", "Next.js, FastAPI và MySQL tạo dữ liệu giao dịch chính thức."],
  ["Lakehouse", "Airflow và Spark xây Bronze, Silver, Gold trên MinIO."],
  ["Analytics", "Gold được publish sang MySQL analytics cho Superset."],
  ["ML", "Gold cung cấp feature point-in-time cho dự đoán mua lại 30 ngày."]
];

export default function HomePage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-16">
      <p className="mb-4 text-sm font-semibold uppercase tracking-[0.24em] text-accent">
        Tiểu luận chuyên ngành
      </p>
      <h1 className="max-w-4xl text-4xl font-semibold leading-tight md:text-6xl">
        Batch Data Lakehouse từ một website thương mại điện tử tối giản.
      </h1>
      <p className="mt-6 max-w-2xl text-lg leading-8 text-ink/70">
        Storefront này là source application. Trọng tâm của hệ thống nằm ở pipeline dữ liệu,
        khả năng đối soát, chạy lại và tái lập.
      </p>
      <Link
        className="mt-8 inline-flex rounded-full bg-ink px-6 py-3 font-medium text-paper"
        href="/products"
      >
        Mở catalog
      </Link>
      <section className="mt-16 grid gap-4 md:grid-cols-2">
        {blocks.map(([title, description]) => (
          <article className="rounded-3xl border border-ink/10 bg-white/60 p-6" key={title}>
            <h2 className="text-xl font-semibold">{title}</h2>
            <p className="mt-2 leading-7 text-ink/70">{description}</p>
          </article>
        ))}
      </section>
    </main>
  );
}

