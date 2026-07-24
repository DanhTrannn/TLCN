export default function ProductsPage() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-14">
      <p className="text-sm font-semibold uppercase tracking-[0.2em] text-accent">Catalog</p>
      <h1 className="mt-3 text-4xl font-semibold">Sản phẩm</h1>
      <div className="mt-8 rounded-3xl border border-dashed border-ink/25 bg-white/50 p-10">
        <p className="font-medium">Catalog module đã sẵn sàng để nối API.</p>
        <p className="mt-2 text-ink/65">
          Product listing, category filter và variant selector được triển khai trong milestone WEB-M1.
        </p>
      </div>
    </main>
  );
}

