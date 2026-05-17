interface TimelineEvent {
  time?: string;
  title?: string;
  description?: string;
  [key: string]: unknown;
}

interface TimelineProps {
  events?: TimelineEvent[];
}

export function TimelineComponent({ events = [] }: TimelineProps) {
  return (
    <ol className="relative border-l border-gray-200 dark:border-gray-700 space-y-6 ml-3">
      {events.map((evt, i) => (
        <li key={i} className="ml-4">
          <div className="absolute w-3 h-3 bg-indigo-500 dark:bg-indigo-400 rounded-full -left-1.5 border-2 border-white dark:border-gray-900" />
          <time className="text-xs font-normal text-gray-400 dark:text-gray-500">{evt.time ?? ""}</time>
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{evt.title ?? ""}</h3>
          {evt.description && (
            <p className="text-xs text-gray-600 dark:text-gray-400">{evt.description}</p>
          )}
        </li>
      ))}
    </ol>
  );
}
