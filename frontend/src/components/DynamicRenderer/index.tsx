import type { UISchema } from "../../types/ui";
import { validateUISchema } from "../../schemas/uiSchema";
import { LayoutRenderer } from "./LayoutRenderer";
import { FallbackView } from "./FallbackView";

interface DynamicRendererProps {
  uiSchema: unknown;
  fallbackAnswer?: string;
  fallbackSources?: { record_id: string; source_ref: string; text: string; score: number }[];
}

export function DynamicRenderer({
  uiSchema,
  fallbackAnswer,
  fallbackSources,
}: DynamicRendererProps) {
  const valid = validateUISchema(uiSchema);

  if (!valid) {
    if (import.meta.env.DEV) {
      console.warn(
        "UI schema validation failed:",
        validateUISchema.errors?.map((e) => e.message).join("; ")
      );
    }
    return <FallbackView answer={fallbackAnswer} sources={fallbackSources} />;
  }

  const schema = uiSchema as UISchema;

  return (
    <div className="space-y-4">
      {schema.title && (
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{schema.title}</h2>
      )}
      <LayoutRenderer node={schema.layout} bindings={schema.data_bindings} />
    </div>
  );
}
