import type { ComponentType } from "../../types/ui";
import type { ComponentType as ReactComponentType } from "react";

import { TextComponent } from "./components/TextComponent";
import { KpiComponent } from "./components/KpiComponent";
import { TableComponent } from "./components/TableComponent";
import { ChartComponent } from "./components/ChartComponent";
import { CardComponent } from "./components/CardComponent";
import { ListComponent } from "./components/ListComponent";
import { TimelineComponent } from "./components/TimelineComponent";
import { FormComponent } from "./components/FormComponent";
import { SourceRefsComponent } from "./components/SourceRefsComponent";
import { ImageViewerComponent } from "./components/ImageViewerComponent";
import { CodeEditorComponent } from "./components/CodeEditorComponent";
import { AudioPlayerComponent } from "./components/AudioPlayerComponent";
import { PdfViewerComponent } from "./components/PdfViewerComponent";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const ComponentRegistry: Record<ComponentType, ReactComponentType<any>> = {
  text: TextComponent,
  kpi: KpiComponent,
  table: TableComponent,
  chart: ChartComponent,
  card: CardComponent,
  list: ListComponent,
  timeline: TimelineComponent,
  form: FormComponent,
  source_refs: SourceRefsComponent,
  image_viewer: ImageViewerComponent,
  code_editor: CodeEditorComponent,
  audio_player: AudioPlayerComponent,
  pdf_viewer: PdfViewerComponent,
};

/**
 * Resolve *_binding props: replace { refs_binding: "sources" } with { refs: data_bindings["sources"] }.
 * Non-binding props are passed through unchanged.
 */
export function resolveBindings(
  props: Record<string, unknown>,
  bindings: Record<string, unknown>
): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(props)) {
    if (k.endsWith("_binding") && typeof v === "string") {
      const outKey = k.slice(0, -"_binding".length);
      out[outKey] = bindings[v];
    } else {
      out[k] = v;
    }
  }
  return out;
}
