import type { SourceRef } from "../../../types/ui";

interface SourceRefsProps {
  refs?: SourceRef[];
}

export function SourceRefsComponent({ refs = [] }: SourceRefsProps) {
  if (refs.length === 0) return null;

  return (
    <div className="border-t border-gray-100 dark:border-gray-700 pt-3">
      <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Sources</p>
      <div className="flex flex-wrap gap-2">
        {refs.map((ref) => (
          <a
            key={ref.record_id}
            href={`/records/${ref.record_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2 py-1 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs rounded-full hover:bg-indigo-100 dark:hover:bg-indigo-900/60 transition-colors"
            title={ref.text}
          >
            <span className="font-mono">{ref.source_ref}</span>
            <span className="text-indigo-400 dark:text-indigo-500">({(ref.score * 100).toFixed(0)}%)</span>
          </a>
        ))}
      </div>
    </div>
  );
}
