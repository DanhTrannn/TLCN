"use client";

import { useEffect, useState } from "react";
import { Icon } from "@/components/ui/Icon";

interface SizeGuideModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SizeGuideModal({ isOpen, onClose }: SizeGuideModalProps) {
  const [activeTab, setActiveTab] = useState<"tops" | "bottoms">("tops");

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }
    if (isOpen) {
      window.addEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "hidden";
    }
    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = "";
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div
      aria-modal="true"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6"
      role="dialog"
    >
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-ink/50 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Modal Dialog */}
      <div className="relative w-full max-w-2xl overflow-hidden rounded-3xl border border-line bg-surface p-6 shadow-lift sm:p-8">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="inline-flex items-center gap-1.5 rounded-full border border-accent/20 bg-accent/10 px-3 py-0.5 text-xs font-semibold text-accent">
              <Icon name="sparkles" size={13} />
              D&K Sizing Guide
            </div>
            <h2 className="mt-2 font-serif text-2xl sm:text-3xl text-ink">Bảng hướng dẫn chọn kích cỡ</h2>
            <p className="mt-1 text-xs sm:text-sm text-muted">
              Thông số chuẩn phom dáng nữ châu Á. Nếu phân vân giữa 2 size, bạn nên chọn size lớn hơn.
            </p>
          </div>
          <button
            aria-label="Đóng bảng size"
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-line bg-paper text-muted transition hover:bg-surface hover:text-ink"
            onClick={onClose}
            type="button"
          >
            <Icon name="close" size={16} />
          </button>
        </div>

        {/* Tab Switcher */}
        <div className="mt-6 flex border-b border-line">
          <button
            className={`border-b-2 px-5 py-2.5 text-sm font-semibold transition ${
              activeTab === "tops"
                ? "border-accent text-accent"
                : "border-transparent text-muted hover:text-ink"
            }`}
            onClick={() => setActiveTab("tops")}
            type="button"
          >
            Áo, Sơ mi & Đầm liền
          </button>
          <button
            className={`border-b-2 px-5 py-2.5 text-sm font-semibold transition ${
              activeTab === "bottoms"
                ? "border-accent text-accent"
                : "border-transparent text-muted hover:text-ink"
            }`}
            onClick={() => setActiveTab("bottoms")}
            type="button"
          >
            Quần tây & Chân váy
          </button>
        </div>

        {/* Tables */}
        <div className="mt-5 overflow-x-auto">
          {activeTab === "tops" ? (
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-line bg-paper/60 text-muted">
                  <th className="py-2.5 px-3 font-semibold">Size</th>
                  <th className="py-2.5 px-3 font-semibold">Chiều cao (cm)</th>
                  <th className="py-2.5 px-3 font-semibold">Cân nặng (kg)</th>
                  <th className="py-2.5 px-3 font-semibold">Vòng 1 (Ngực)</th>
                  <th className="py-2.5 px-3 font-semibold">Vòng 2 (Eo)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line text-ink">
                <tr>
                  <td className="py-3 px-3 font-bold text-accent">S</td>
                  <td className="py-3 px-3">150 - 155</td>
                  <td className="py-3 px-3">42 - 47</td>
                  <td className="py-3 px-3">80 - 84 cm</td>
                  <td className="py-3 px-3">62 - 66 cm</td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-bold text-accent">M</td>
                  <td className="py-3 px-3">156 - 160</td>
                  <td className="py-3 px-3">48 - 53</td>
                  <td className="py-3 px-3">85 - 88 cm</td>
                  <td className="py-3 px-3">67 - 70 cm</td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-bold text-accent">L</td>
                  <td className="py-3 px-3">161 - 165</td>
                  <td className="py-3 px-3">54 - 58</td>
                  <td className="py-3 px-3">89 - 92 cm</td>
                  <td className="py-3 px-3">71 - 74 cm</td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-bold text-accent">XL</td>
                  <td className="py-3 px-3">165 - 170</td>
                  <td className="py-3 px-3">59 - 64</td>
                  <td className="py-3 px-3">93 - 96 cm</td>
                  <td className="py-3 px-3">75 - 80 cm</td>
                </tr>
              </tbody>
            </table>
          ) : (
            <table className="w-full text-left text-xs sm:text-sm">
              <thead>
                <tr className="border-b border-line bg-paper/60 text-muted">
                  <th className="py-2.5 px-3 font-semibold">Size</th>
                  <th className="py-2.5 px-3 font-semibold">Vòng 2 (Eo)</th>
                  <th className="py-2.5 px-3 font-semibold">Vòng 3 (Mông)</th>
                  <th className="py-2.5 px-3 font-semibold">Dài quần (cm)</th>
                  <th className="py-2.5 px-3 font-semibold">Cân nặng (kg)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-line text-ink">
                <tr>
                  <td className="py-3 px-3 font-bold text-accent">S</td>
                  <td className="py-3 px-3">62 - 66 cm</td>
                  <td className="py-3 px-3">86 - 90 cm</td>
                  <td className="py-3 px-3">92 - 94</td>
                  <td className="py-3 px-3">42 - 47</td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-bold text-accent">M</td>
                  <td className="py-3 px-3">67 - 70 cm</td>
                  <td className="py-3 px-3">91 - 94 cm</td>
                  <td className="py-3 px-3">94 - 96</td>
                  <td className="py-3 px-3">48 - 53</td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-bold text-accent">L</td>
                  <td className="py-3 px-3">71 - 74 cm</td>
                  <td className="py-3 px-3">95 - 98 cm</td>
                  <td className="py-3 px-3">96 - 98</td>
                  <td className="py-3 px-3">54 - 58</td>
                </tr>
                <tr>
                  <td className="py-3 px-3 font-bold text-accent">XL</td>
                  <td className="py-3 px-3">75 - 80 cm</td>
                  <td className="py-3 px-3">99 - 104 cm</td>
                  <td className="py-3 px-3">98 - 100</td>
                  <td className="py-3 px-3">59 - 64</td>
                </tr>
              </tbody>
            </table>
          )}
        </div>

        {/* Return Guarantee Note */}
        <div className="mt-6 flex items-center gap-3 rounded-2xl border border-moss/20 bg-moss/[0.08] p-4 text-xs sm:text-sm text-moss">
          <Icon name="rotate-ccw" size={20} />
          <span>
            <strong>Yên tâm mua sắm:</strong> Nếu sản phẩm nhận được chưa vừa vặn, D&K hỗ trợ đổi size miễn phí trong vòng 7 ngày kể từ khi nhận hàng.
          </span>
        </div>
      </div>
    </div>
  );
}
