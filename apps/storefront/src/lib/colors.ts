/**
 * Color mapping utilities for D&K Fashion product swatches and labels.
 */

export interface ColorMeta {
  hex: string;
  label: string;
  textColor?: string;
  isLight?: boolean;
}

const COLOR_MAP: Record<string, ColorMeta> = {
  black: { hex: "#18181b", label: "Đen", textColor: "#ffffff", isLight: false },
  den: { hex: "#18181b", label: "Đen", textColor: "#ffffff", isLight: false },
  white: { hex: "#ffffff", label: "Trắng", textColor: "#18181b", isLight: true },
  trang: { hex: "#ffffff", label: "Trắng", textColor: "#18181b", isLight: true },
  beige: { hex: "#d8c4b6", label: "Be", textColor: "#18181b", isLight: true },
  be: { hex: "#d8c4b6", label: "Be", textColor: "#18181b", isLight: true },
  gray: { hex: "#6b7280", label: "Xám", textColor: "#ffffff", isLight: false },
  xam: { hex: "#6b7280", label: "Xám", textColor: "#ffffff", isLight: false },
  navy: { hex: "#1e3a8a", label: "Xanh Navy", textColor: "#ffffff", isLight: false },
  blue: { hex: "#2563eb", label: "Xanh Dương", textColor: "#ffffff", isLight: false },
  xanh: { hex: "#2563eb", label: "Xanh Dương", textColor: "#ffffff", isLight: false },
  brown: { hex: "#78350f", label: "Nâu", textColor: "#ffffff", isLight: false },
  nau: { hex: "#78350f", label: "Nâu", textColor: "#ffffff", isLight: false },
  red: { hex: "#dc2626", label: "Đỏ", textColor: "#ffffff", isLight: false },
  do: { hex: "#dc2626", label: "Đỏ", textColor: "#ffffff", isLight: false },
  green: { hex: "#15803d", label: "Xanh Lá", textColor: "#ffffff", isLight: false },
  pink: { hex: "#f472b6", label: "Hồng", textColor: "#18181b", isLight: true },
  hong: { hex: "#f472b6", label: "Hồng", textColor: "#18181b", isLight: true },
  yellow: { hex: "#facc15", label: "Vàng", textColor: "#18181b", isLight: true },
  vang: { hex: "#facc15", label: "Vàng", textColor: "#18181b", isLight: true },
  orange: { hex: "#f97316", label: "Cam", textColor: "#ffffff", isLight: false },
  cam: { hex: "#f97316", label: "Cam", textColor: "#ffffff", isLight: false },
  purple: { hex: "#9333ea", label: "Tím", textColor: "#ffffff", isLight: false },
  tim: { hex: "#9333ea", label: "Tím", textColor: "#ffffff", isLight: false },
};

export function getColorMeta(colorCode: string | null | undefined): ColorMeta {
  if (!colorCode) {
    return { hex: "#9ca3af", label: "Mặc định", textColor: "#ffffff", isLight: false };
  }
  const normalized = colorCode.trim().toLowerCase();
  return (
    COLOR_MAP[normalized] || {
      hex: "#9ca3af",
      label: colorCode,
      textColor: "#ffffff",
      isLight: false,
    }
  );
}

export function getColorHex(colorCode: string | null | undefined): string {
  return getColorMeta(colorCode).hex;
}

export function getColorLabel(colorCode: string | null | undefined): string {
  return getColorMeta(colorCode).label;
}
