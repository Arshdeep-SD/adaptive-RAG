import { useState } from "react";
import type { LayoutNode, ComponentType as UIComponentType } from "../../types/ui";
import { ComponentRegistry, resolveBindings } from "./ComponentRegistry";

interface LayoutRendererProps {
  node: LayoutNode;
  bindings: Record<string, unknown>;
}

export function LayoutRenderer({ node, bindings }: LayoutRendererProps) {
  switch (node.type) {
    case "stack": {
      const flex = node.direction === "vertical" ? "flex-col" : "flex-row flex-wrap";
      return (
        <div className={`flex ${flex} gap-4`}>
          {node.children.map((child, i) => (
            <LayoutRenderer key={i} node={child} bindings={bindings} />
          ))}
        </div>
      );
    }

    case "grid":
      return (
        <div
          className="grid gap-4"
          style={{ gridTemplateColumns: `repeat(${node.columns}, minmax(0, 1fr))` }}
        >
          {node.children.map((child, i) => (
            <LayoutRenderer key={i} node={child} bindings={bindings} />
          ))}
        </div>
      );

    case "tabs":
      return <TabsRenderer node={node} bindings={bindings} />;

    case "section":
      return (
        <section className="space-y-2">
          <h3 className="text-base font-semibold text-gray-800 dark:text-gray-100 border-b border-gray-200 dark:border-gray-700 pb-1">
            {node.heading}
          </h3>
          <LayoutRenderer node={node.child} bindings={bindings} />
        </section>
      );

    case "component": {
      const Comp = ComponentRegistry[node.component as UIComponentType];
      if (!Comp) {
        console.warn("Unknown component:", node.component);
        return null;
      }
      const resolvedProps = resolveBindings(node.props, bindings);
      return <Comp {...resolvedProps} />;
    }

    default:
      return null;
  }
}

function TabsRenderer({
  node,
  bindings,
}: {
  node: Extract<LayoutNode, { type: "tabs" }>;
  bindings: Record<string, unknown>;
}) {
  const [active, setActive] = useState(0);

  return (
    <div>
      <div className="flex border-b border-gray-200 dark:border-gray-700 gap-2 mb-4">
        {node.tabs.map((tab, i) => (
          <button
            key={i}
            onClick={() => setActive(i)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              active === i
                ? "border-indigo-500 text-indigo-600 dark:text-indigo-400"
                : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      <LayoutRenderer node={node.tabs[active].content} bindings={bindings} />
    </div>
  );
}
