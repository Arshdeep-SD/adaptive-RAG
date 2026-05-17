import type { ReactNode } from "react";

interface TextProps {
  content?: string;
  variant?: "body" | "caption" | "heading";
}

const variantClass: Record<string, string> = {
  body:    "text-sm text-gray-800 dark:text-gray-200 leading-relaxed",
  caption: "text-xs text-gray-500 dark:text-gray-400",
  heading: "text-lg font-semibold text-gray-900 dark:text-gray-100",
};

function renderWithCitations(text: string): ReactNode[] {
  const parts = text.split(/(\[ref:[^\]]+\])/g);
  return parts.map((part, i) => {
    const match = part.match(/^\[ref:([^\]]+)\]$/);
    if (match) {
      const shortId = match[1].slice(0, 8);
      return (
        <span
          key={i}
          className="inline-block mx-0.5 px-1.5 py-0.5 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 text-xs rounded font-mono align-middle"
          title={match[1]}
        >
          [{shortId}]
        </span>
      );
    }
    return <span key={i}>{part}</span>;
  });
}

export function TextComponent({ content = "", variant = "body" }: TextProps) {
  return (
    <p className={variantClass[variant] ?? variantClass.body}>
      {renderWithCitations(content)}
    </p>
  );
}
