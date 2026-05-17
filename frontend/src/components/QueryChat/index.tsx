import { useState, useRef, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import { api } from "../../api/client";
import type { QueryResponse } from "../../types/ui";
import { DynamicRenderer } from "../DynamicRenderer";
import { ErrorBoundary } from "../ErrorBoundary";

interface Message {
  id: string;
  query: string;
  response?: QueryResponse;
  error?: string;
  loading: boolean;
}

export function QueryChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const { mutate, isPending } = useMutation({
    mutationFn: (query: string) => api.query(query),
    onSuccess: (data, query) => {
      setMessages((msgs) =>
        msgs.map((m) =>
          m.query === query && m.loading ? { ...m, response: data, loading: false } : m
        )
      );
    },
    onError: (error, query) => {
      setMessages((msgs) =>
        msgs.map((m) =>
          m.query === query && m.loading
            ? { ...m, error: (error as Error).message, loading: false }
            : m
        )
      );
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const q = input.trim();
    if (!q || isPending) return;

    const id = typeof crypto.randomUUID === "function"
      ? crypto.randomUUID()
      : `${Date.now()}-${Math.random().toString(36).slice(2)}`;
    const msg: Message = { id, query: q, loading: true };
    setMessages((msgs) => [...msgs, msg]);
    setInput("");
    mutate(q);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Message thread */}
      <div className="flex-1 overflow-y-auto space-y-6 p-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-gray-400 dark:text-gray-600 text-sm">
            Ingest some data, then ask a question.
          </div>
        )}
        {messages.map((msg) => (
          <div key={msg.id} className="space-y-3">
            {/* User query */}
            <div className="flex justify-end">
              <div className="bg-indigo-600 text-white text-sm rounded-2xl rounded-tr-sm px-4 py-2 max-w-sm">
                {msg.query}
              </div>
            </div>

            {/* Response */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl rounded-tl-sm p-4 shadow-sm">
              {msg.loading ? (
                <SkeletonLoader />
              ) : msg.error ? (
                <p className="text-red-500 text-sm">{msg.error}</p>
              ) : msg.response ? (
                <div className="space-y-3">
                  {msg.response.cache_hit && (
                    <span className="inline-block px-2 py-0.5 bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-400 text-xs rounded-full">
                      Cached layout
                    </span>
                  )}
                  <ErrorBoundary>
                    <DynamicRenderer
                      uiSchema={msg.response.ui_schema}
                      fallbackAnswer={msg.response.answer}
                      fallbackSources={msg.response.sources}
                    />
                  </ErrorBoundary>
                </div>
              ) : null}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form
        onSubmit={handleSubmit}
        className="border-t border-gray-200 dark:border-gray-700 p-4 flex gap-2 bg-white dark:bg-gray-900"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your data…"
          disabled={isPending}
          className="flex-1 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 text-sm bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-400 disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={!input.trim() || isPending}
          className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isPending ? "…" : "Ask"}
        </button>
      </form>
    </div>
  );
}

function SkeletonLoader() {
  return (
    <div className="space-y-2 animate-pulse">
      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
      <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-5/6" />
    </div>
  );
}
