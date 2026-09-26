"use client";

import React, { useEffect, useRef } from "react";
import * as echarts from "echarts/core";
import {
  BarChart,
  LineChart,
  PieChart,
  FunnelChart,
  GaugeChart,
} from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  DataZoomComponent,
} from "echarts/components";
import { CanvasRenderer } from "echarts/renderers";
import type { EChartsOption } from "echarts";

// Register necessary ECharts components once
echarts.use([
  BarChart,
  LineChart,
  PieChart,
  FunnelChart,
  GaugeChart,
  TitleComponent,
  TooltipComponent,
  GridComponent,
  LegendComponent,
  ToolboxComponent,
  DataZoomComponent,
  CanvasRenderer,
]);

export type { EChartsOption };

export interface EChartProps {
  option: EChartsOption;
  height?: number | string;
  width?: number | string;
  loading?: boolean;
  className?: string;
  onChartReady?: (chart: echarts.ECharts) => void;
}

export const BRAND_COLORS = [
  "#152722", // Ink / Primary
  "#a94728", // Accent terracotta
  "#315b4f", // Deep moss
  "#8b5b16", // Gold / amber
  "#3d647a", // Steel blue
  "#9b4d6e", // Mulberry
  "#dcd8cf", // Muted sand
];

export function EChart({
  option,
  height = 320,
  width = "100%",
  loading = false,
  className = "",
  onChartReady,
}: EChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartInstance = useRef<echarts.ECharts | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    if (!chartInstance.current) {
      chartInstance.current = echarts.init(containerRef.current, undefined, {
        renderer: "canvas",
      });
      if (onChartReady) {
        onChartReady(chartInstance.current);
      }
    }

    const chart = chartInstance.current;

    // Apply brand color palette if not specified
    const styledOption: EChartsOption = {
      color: BRAND_COLORS,
      textStyle: {
        fontFamily: "inherit",
      },
      ...option,
    };

    chart.setOption(styledOption, { notMerge: true });

    if (loading) {
      chart.showLoading({
        text: "Đang tải dữ liệu...",
        color: "#152722",
        textColor: "#152722",
        maskColor: "rgba(255, 255, 255, 0.7)",
      });
    } else {
      chart.hideLoading();
    }
  }, [option, loading, onChartReady]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;

    const resizeObserver = new ResizeObserver(() => {
      chartInstance.current?.resize();
    });
    resizeObserver.observe(el);

    return () => {
      resizeObserver.disconnect();
    };
  }, []);

  useEffect(() => {
    return () => {
      chartInstance.current?.dispose();
      chartInstance.current = null;
    };
  }, []);

  const heightStyle = typeof height === "number" ? `${height}px` : height;
  const widthStyle = typeof width === "number" ? `${width}px` : width;

  return (
    <div
      ref={containerRef}
      className={`relative w-full ${className}`}
      style={{ height: heightStyle, width: widthStyle, minHeight: heightStyle }}
    />
  );
}

export default EChart;
