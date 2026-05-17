import { useState } from "react";
import { useAuthenticatedUrl } from "../hooks/useAuthenticatedUrl";

interface ImageViewerProps {
  src?: string;
  filename?: string;
  description?: string;
}

export function ImageViewerComponent({ src: srcProp, filename, description }: ImageViewerProps) {
  const [zoom, setZoom] = useState(1);
  const [imgError, setImgError] = useState(false);
  const { url: src, loading, error: fetchError } = useAuthenticatedUrl(srcProp);
  const error = fetchError || imgError;

  if (!srcProp) {
    return (
      <div className="rounded-lg border border-gray-200 bg-gray-50 p-6 text-center text-sm text-gray-400">
        No image source provided
      </div>
    );
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 p-6 text-center text-sm text-gray-400 animate-pulse">
        Loading image…
      </div>
    );
  }

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-3 py-2 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <span className="text-xs font-medium text-gray-600 dark:text-gray-300 truncate max-w-[200px]" title={filename}>
          {filename ?? "image"}
        </span>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setZoom((z) => Math.max(0.25, z - 0.25))}
            className="px-2 py-1 text-xs rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 font-mono"
            title="Zoom out"
          >
            −
          </button>
          <span className="text-xs text-gray-500 w-10 text-center">{Math.round(zoom * 100)}%</span>
          <button
            onClick={() => setZoom((z) => Math.min(4, z + 0.25))}
            className="px-2 py-1 text-xs rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 font-mono"
            title="Zoom in"
          >
            +
          </button>
          <button
            onClick={() => setZoom(1)}
            className="px-2 py-1 text-xs rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-500 dark:text-gray-400"
            title="Reset zoom"
          >
            Reset
          </button>
          {src && (
            <a
              href={src}
              download={filename}
              className="px-2 py-1 text-xs rounded hover:bg-gray-100 dark:hover:bg-gray-700 text-indigo-600 dark:text-indigo-400"
              title="Download"
            >
              ↓ Save
            </a>
          )}
        </div>
      </div>

      {/* Image area */}
      <div className="overflow-auto bg-[#1e1e1e] flex items-center justify-center min-h-[200px] max-h-[500px] p-4">
        {error ? (
          <div className="text-sm text-gray-400 text-center space-y-2">
            <p>Could not load image.</p>
            <a
              href={srcProp}
              target="_blank"
              rel="noopener noreferrer"
              className="text-indigo-400 hover:underline text-xs"
            >
              Open directly
            </a>
          </div>
        ) : (
          <img
            src={src}
            alt={filename ?? "uploaded image"}
            style={{ transform: `scale(${zoom})`, transformOrigin: "center", transition: "transform 0.15s" }}
            className="max-w-full object-contain"
            onError={() => setImgError(true)}
          />
        )}
      </div>

      {/* Description / metadata strip */}
      {description && (
        <div className="px-4 py-3 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 text-sm text-gray-700 dark:text-gray-300">
          <p className="text-xs font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Description</p>
          <p className="leading-relaxed">{description}</p>
        </div>
      )}
    </div>
  );
}
