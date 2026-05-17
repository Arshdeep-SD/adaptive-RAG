interface KpiProps {
  label: string;
  value?: string | number;
  delta?: number;
  unit?: string;
}

export function KpiComponent({ label, value, delta, unit }: KpiProps) {
  const display = value !== undefined ? String(value) : "—";
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col gap-1">
      <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wide">{label}</p>
      <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">
        {display}
        {unit && <span className="text-sm font-normal ml-1 text-gray-500 dark:text-gray-400">{unit}</span>}
      </p>
      {delta !== undefined && (
        <p className={`text-xs font-medium ${delta >= 0 ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`}>
          {delta >= 0 ? "▲" : "▼"} {Math.abs(delta)}
        </p>
      )}
    </div>
  );
}
