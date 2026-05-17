import { useAuthenticatedUrl } from "../hooks/useAuthenticatedUrl";

interface PdfViewerProps {
  src?: string;
  filename?: string;
}

export function PdfViewerComponent({ src: srcProp, filename }: PdfViewerProps) {
  const { url, loading, error } = useAuthenticatedUrl(srcProp);

  if (!srcProp) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-6 text-center text-sm text-gray-400">
        No PDF source provided
      </div>
    );
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-6 text-center text-sm text-gray-400 animate-pulse">
        Loading PDF…
      </div>
    );
  }

  if (error || !url) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-6 text-center text-sm text-gray-400">
        Could not load PDF.
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
      <div className="flex items-center justify-between px-3 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <span className="text-xs font-medium text-gray-600 dark:text-gray-300 truncate max-w-[280px]" title={filename}>
          {filename ?? "document.pdf"}
        </span>
        <a
          href={url}
          download={filename}
          className="px-2 py-1 text-xs rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-indigo-600 dark:text-indigo-400"
        >
          ↓ Save
        </a>
      </div>
      <iframe
        src={url}
        title={filename ?? "PDF viewer"}
        className="w-full"
        style={{ height: "600px", border: "none" }}
      />
    </div>
  );
}
