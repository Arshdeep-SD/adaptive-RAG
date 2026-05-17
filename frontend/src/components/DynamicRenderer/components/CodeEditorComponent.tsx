import { useState } from "react";
import { Light as SyntaxHighlighter } from "react-syntax-highlighter";
import { githubGist } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { atomOneDark } from "react-syntax-highlighter/dist/esm/styles/hljs";
import { useDarkMode } from "../../../context/ThemeContext";

// Register only the languages we need (keeps bundle small)
import js from "react-syntax-highlighter/dist/esm/languages/hljs/javascript";
import ts from "react-syntax-highlighter/dist/esm/languages/hljs/typescript";
import py from "react-syntax-highlighter/dist/esm/languages/hljs/python";
import go from "react-syntax-highlighter/dist/esm/languages/hljs/go";
import rust from "react-syntax-highlighter/dist/esm/languages/hljs/rust";
import java from "react-syntax-highlighter/dist/esm/languages/hljs/java";
import cpp from "react-syntax-highlighter/dist/esm/languages/hljs/cpp";
import cs from "react-syntax-highlighter/dist/esm/languages/hljs/csharp";
import rb from "react-syntax-highlighter/dist/esm/languages/hljs/ruby";
import bash from "react-syntax-highlighter/dist/esm/languages/hljs/bash";
import sql from "react-syntax-highlighter/dist/esm/languages/hljs/sql";
import html from "react-syntax-highlighter/dist/esm/languages/hljs/xml";
import css from "react-syntax-highlighter/dist/esm/languages/hljs/css";
import yaml from "react-syntax-highlighter/dist/esm/languages/hljs/yaml";
import json from "react-syntax-highlighter/dist/esm/languages/hljs/json";
import kotlin from "react-syntax-highlighter/dist/esm/languages/hljs/kotlin";
import swift from "react-syntax-highlighter/dist/esm/languages/hljs/swift";
import php from "react-syntax-highlighter/dist/esm/languages/hljs/php";
import scala from "react-syntax-highlighter/dist/esm/languages/hljs/scala";
import c from "react-syntax-highlighter/dist/esm/languages/hljs/c";
import lua from "react-syntax-highlighter/dist/esm/languages/hljs/lua";

SyntaxHighlighter.registerLanguage("javascript", js);
SyntaxHighlighter.registerLanguage("typescript", ts);
SyntaxHighlighter.registerLanguage("python", py);
SyntaxHighlighter.registerLanguage("go", go);
SyntaxHighlighter.registerLanguage("rust", rust);
SyntaxHighlighter.registerLanguage("java", java);
SyntaxHighlighter.registerLanguage("cpp", cpp);
SyntaxHighlighter.registerLanguage("csharp", cs);
SyntaxHighlighter.registerLanguage("ruby", rb);
SyntaxHighlighter.registerLanguage("bash", bash);
SyntaxHighlighter.registerLanguage("sql", sql);
SyntaxHighlighter.registerLanguage("html", html);
SyntaxHighlighter.registerLanguage("css", css);
SyntaxHighlighter.registerLanguage("yaml", yaml);
SyntaxHighlighter.registerLanguage("json", json);
SyntaxHighlighter.registerLanguage("kotlin", kotlin);
SyntaxHighlighter.registerLanguage("swift", swift);
SyntaxHighlighter.registerLanguage("php", php);
SyntaxHighlighter.registerLanguage("scala", scala);
SyntaxHighlighter.registerLanguage("c", c);
SyntaxHighlighter.registerLanguage("lua", lua);

const LANG_BADGE: Record<string, string> = {
  python:     "bg-blue-100 text-blue-700",
  javascript: "bg-yellow-100 text-yellow-700",
  typescript: "bg-blue-100 text-blue-800",
  tsx:        "bg-cyan-100 text-cyan-700",
  jsx:        "bg-yellow-100 text-yellow-600",
  go:         "bg-teal-100 text-teal-700",
  rust:       "bg-orange-100 text-orange-700",
  java:       "bg-red-100 text-red-700",
  cpp:        "bg-purple-100 text-purple-700",
  c:          "bg-purple-100 text-purple-600",
  csharp:     "bg-green-100 text-green-700",
  ruby:       "bg-red-100 text-red-600",
  bash:       "bg-gray-100 text-gray-700",
  sql:        "bg-indigo-100 text-indigo-700",
  html:       "bg-orange-100 text-orange-600",
  css:        "bg-pink-100 text-pink-700",
  yaml:       "bg-lime-100 text-lime-700",
  json:       "bg-gray-100 text-gray-600",
  kotlin:     "bg-violet-100 text-violet-700",
  swift:      "bg-orange-100 text-orange-500",
};

// tsx/jsx share the js highlighter
const HLJS_LANG: Record<string, string> = {
  tsx: "typescript",
  jsx: "javascript",
};

interface CodeEditorProps {
  code?: string;
  language?: string;
  filename?: string;
}

export function CodeEditorComponent({ code = "", language = "plaintext", filename }: CodeEditorProps) {
  const [copied, setCopied] = useState(false);
  const { isDark } = useDarkMode();

  const handleCopy = () => {
    navigator.clipboard.writeText(code).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  const lines = code.split("\n").length;
  const badgeClass = LANG_BADGE[language] ?? "bg-gray-100 text-gray-600";
  const hljsLang = HLJS_LANG[language] ?? language;
  const hlStyle = isDark ? atomOneDark : githubGist;

  return (
    <div className="rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden font-mono text-sm">
      {/* Header */}
      <div className="flex items-center justify-between px-3 py-2 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center gap-2">
          {filename && (
            <span className="text-gray-600 dark:text-gray-300 text-xs truncate max-w-[220px]" title={filename}>
              {filename}
            </span>
          )}
          <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${badgeClass}`}>
            {language}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-gray-400 dark:text-gray-500 text-xs">{lines} lines</span>
          <button
            onClick={handleCopy}
            className="px-2 py-1 text-xs rounded bg-white dark:bg-gray-700 border border-gray-200 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 text-gray-600 dark:text-gray-300 transition-colors"
          >
            {copied ? "✓ Copied" : "Copy"}
          </button>
        </div>
      </div>

      {/* Highlighted code */}
      <SyntaxHighlighter
        language={hljsLang}
        style={hlStyle}
        showLineNumbers
        lineNumberStyle={{ color: isDark ? "#4b5563" : "#d1d5db", fontSize: "0.75rem", minWidth: "2.5rem" }}
        customStyle={{
          margin: 0,
          padding: "1rem",
          background: isDark ? "#1f2937" : "#ffffff",
          fontSize: "0.8125rem",
          lineHeight: "1.6",
          maxHeight: "500px",
          overflowY: "auto",
        }}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}
