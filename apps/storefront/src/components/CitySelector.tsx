"use client";

import { useRef, useState, useEffect } from "react";

import { Icon } from "@/components/ui/Icon";
import { useLocation } from "@/components/LocationContext";

export function CitySelector() {
  const { selectedCity, cities, setSelectedCity, isLoading } = useLocation();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    if (open) document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, [open]);

  if (isLoading || cities.length === 0) return null;

  return (
    <div className="relative" ref={ref}>
      <button
        aria-label="Chọn tỉnh / thành phố"
        className="flex min-h-10 items-center gap-1.5 rounded-full border border-line bg-surface px-3 py-1.5 text-sm font-semibold text-ink transition hover:border-ink/30 hover:bg-paper"
        onClick={() => setOpen((prev) => !prev)}
        type="button"
      >
        <Icon name="home" size={16} />
        <span className="hidden sm:inline">{selectedCity?.name ?? "Chọn thành phố"}</span>
        <Icon name="chevron-right" size={14} className={`transition-transform ${open ? "rotate-90" : ""}`} />
      </button>

      {open ? (
        <div className="absolute right-0 top-full z-50 mt-2 w-72 rounded-2xl border border-line bg-surface p-2 shadow-lift">
          <p className="px-3 py-2 text-xs font-semibold uppercase tracking-[0.15em] text-muted">
            Chọn tỉnh / thành phố
          </p>
          <ul className="max-h-72 overflow-y-auto">
            {cities.map((city) => {
              const active = city.code === selectedCity?.code;
              return (
                <li key={city.code}>
                  <button
                    className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-sm transition ${
                      active ? "bg-ink text-paper" : "text-ink hover:bg-paper"
                    }`}
                    onClick={() => {
                      setSelectedCity(city);
                      setOpen(false);
                    }}
                    type="button"
                  >
                    <span className="font-medium">{city.name}</span>
                    <span className={`text-xs ${active ? "text-paper/65" : "text-muted"}`}>
                      {city.store_count} cửa hàng
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
