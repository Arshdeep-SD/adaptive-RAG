import type { QueryResponse } from "../../types/ui";

interface FallbackViewProps {
  answer?: string;
  sources?: QueryResponse["sources"];
}

export function FallbackView({ answer, sources = [] }: FallbackViewProps) {
  return (
    <div className="space-y-3">
      {answer && <p className="text-sm text-gray-800 dark:text-gray-200 whitespace-pre-wrap">{answer}</p>}
      {sources.length > 0 && (
        <div className="border-t border-gray-100 dark:border-gray-700 pt-3">
          <p className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">Sources</p>
          <div className="flex flex-wrap gap-2">
            {sources.map((ref) => (
              <span
                key={ref.record_id}
                className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 text-xs rounded-full"
              >
                {ref.source_ref}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
