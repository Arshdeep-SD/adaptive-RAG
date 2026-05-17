interface CardProps {
  title?: string;
  body?: string;
  footer?: string;
}

export function CardComponent({ title, body, footer }: CardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex flex-col gap-2 shadow-sm">
      {title && <h3 className="font-semibold text-gray-900 dark:text-gray-100">{title}</h3>}
      {body && <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">{body}</p>}
      {footer && <p className="text-xs text-gray-400 dark:text-gray-500 border-t border-gray-100 dark:border-gray-700 pt-2">{footer}</p>}
    </div>
  );
}
