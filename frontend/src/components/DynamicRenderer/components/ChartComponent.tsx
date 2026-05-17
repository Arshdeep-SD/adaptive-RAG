import React from "react";
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

const COLORS = ["#6366f1", "#22d3ee", "#f59e0b", "#10b981", "#f43f5e", "#8b5cf6"];

interface ChartProps {
  kind: "bar" | "line" | "pie" | "scatter";
  x: string;
  y: string | string[];
  data?: Record<string, unknown>[];
}

export function ChartComponent({ kind, x, y, data = [] }: ChartProps) {
  const yKeys = Array.isArray(y) ? y : [y];

  if (kind === "pie") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie data={data} dataKey={yKeys[0]} nameKey={x} cx="50%" cy="50%" outerRadius={100} label>
            {data.map((_, i) => (
              <Cell key={i} fill={COLORS[i % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip />
          <Legend />
        </PieChart>
      </ResponsiveContainer>
    );
  }

  if (kind === "scatter") {
    return (
      <ResponsiveContainer width="100%" height={300}>
        <ScatterChart>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={x} />
          <YAxis dataKey={yKeys[0]} />
          <Tooltip />
          <Scatter data={data} fill={COLORS[0]} />
        </ScatterChart>
      </ResponsiveContainer>
    );
  }

  const ChartWrapper = kind === "line" ? LineChart : BarChart;
  const DataComponent = (kind === "line" ? Line : Bar) as React.ElementType;

  return (
    <ResponsiveContainer width="100%" height={300}>
      <ChartWrapper data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey={x} />
        <YAxis />
        <Tooltip />
        <Legend />
        {yKeys.map((key, i) => (
          <DataComponent
            key={key}
            type="monotone"
            dataKey={key}
            fill={COLORS[i % COLORS.length]}
            stroke={COLORS[i % COLORS.length]}
          />
        ))}
      </ChartWrapper>
    </ResponsiveContainer>
  );
}
