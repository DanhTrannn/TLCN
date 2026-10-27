import type { EChartsOption } from "@/components/ui/EChart";
import { number } from "./AnalyticsUI";

export function barOption(rows: { name: string; value: number }[], seriesName: string, format: (value: number) => string = number, color = "#315b4f"): EChartsOption {
  return {
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" }, renderMode: "richText", confine: true, valueFormatter: value => format(Number(value)) },
    grid: { left: 4, right: 22, top: 12, bottom: 10, containLabel: true },
    xAxis: { type: "value", min: ({ min }) => Math.min(0, min), axisLabel: { color: "#5d6965", fontSize: 11, formatter: format }, splitLine: { lineStyle: { color: "#ece6da", type: "dashed" } } },
    yAxis: { type: "category", inverse: true, data: rows.map(row => row.name), axisTick: { show: false }, axisLine: { show: false }, axisLabel: { color: "#152722", fontSize: 11, width: 115, overflow: "truncate" } },
    series: [{ name: seriesName, type: "bar", data: rows.map(row => row.value), barMaxWidth: 22, itemStyle: { color, borderRadius: [0, 3, 3, 0] } }],
  };
}
