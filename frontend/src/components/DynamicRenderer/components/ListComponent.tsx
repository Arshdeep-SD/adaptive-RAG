interface ListItem {
  title?: string;
  subtitle?: string;
  label?: string;
  [key: string]: unknown;
}

interface ListProps {
  items?: ListItem[];
  item_template?: "title_subtitle" | "bullet";
}

export function ListComponent({ items = [], item_template = "bullet" }: ListProps) {
  if (item_template === "title_subtitle") {
    return (
      <ul className="divide-y divide-gray-100 dark:divide-gray-700">
        {items.map((item, i) => (
          <li key={i} className="py-2">
            <p className="font-medium text-sm text-gray-900 dark:text-gray-100">
              {item.title ?? String(Object.values(item)[0] ?? "")}
            </p>
            {item.subtitle && <p className="text-xs text-gray-500 dark:text-gray-400">{item.subtitle}</p>}
          </li>
        ))}
      </ul>
    );
  }

  return (
    <ul className="list-disc list-inside space-y-1">
      {items.map((item, i) => (
        <li key={i} className="text-sm text-gray-800 dark:text-gray-200">
          {item.title ?? item.label ?? String(Object.values(item)[0] ?? "")}
        </li>
      ))}
    </ul>
  );
}
