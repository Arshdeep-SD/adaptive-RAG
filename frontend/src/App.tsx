import { useQueryClient } from "@tanstack/react-query";
import { IngestPanel } from "./components/IngestPanel";
import { UsersPanel } from "./components/UsersPanel";
import { QueryChat } from "./components/QueryChat";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { LoginScreen } from "./components/LoginScreen";
import { ThemeProvider, useDarkMode } from "./context/ThemeContext";
import { AuthProvider, useAuth } from "./context/AuthContext";

function MoonIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  );
}

const ROLE_BADGE: Record<string, string> = {
  admin:       "bg-red-50 dark:bg-red-900/40 text-red-700 dark:text-red-300",
  contributor: "bg-amber-50 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300",
  user:        "bg-blue-50 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
};

function Shell() {
  const { isDark, toggle } = useDarkMode();
  const { user, logout, isLoading } = useAuth();
  const queryClient = useQueryClient();
  const handleLogout = () => { queryClient.clear(); logout(); };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="animate-pulse text-gray-400 dark:text-gray-500 text-sm">Loading…</div>
      </div>
    );
  }

  if (!user) return <LoginScreen />;

  const showIngestPanel = user.role === "admin" || user.role === "contributor";

  return (
    <ErrorBoundary>
      <div className="min-h-screen flex flex-col bg-white dark:bg-gray-950 transition-colors">
        {/* Header */}
        <header className="bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-6 py-3 flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900 dark:text-gray-100">Adaptive RAG Data Platform</h1>
            <p className="text-xs text-gray-400 dark:text-gray-500">EE 547 — Dynamic UI Generation Demo</p>
          </div>
          <div className="flex items-center gap-3">
            {/* User info */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-700 dark:text-gray-300">{user.username}</span>
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_BADGE[user.role] ?? "bg-gray-100 text-gray-600"}`}>
                {user.role}
              </span>
            </div>
            <button
              onClick={handleLogout}
              className="text-xs text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 px-2 py-1 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
            >
              Sign out
            </button>
            <div className="w-px h-4 bg-gray-200 dark:bg-gray-700" />
            <button
              onClick={toggle}
              className="p-2 rounded-lg text-gray-500 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title={isDark ? "Switch to light mode" : "Switch to dark mode"}
            >
              {isDark ? <SunIcon /> : <MoonIcon />}
            </button>
            <span className="px-2 py-1 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 text-xs rounded-full font-medium">
              v1.0
            </span>
          </div>
        </header>

        {/* Main layout */}
        <div className="flex flex-1 overflow-hidden">
          {showIngestPanel && (
            <aside className="w-80 flex-shrink-0 border-r border-gray-200 dark:border-gray-700 overflow-y-auto p-4 bg-white dark:bg-gray-900 flex flex-col gap-4">
              <IngestPanel />
              {user.role === "admin" && <UsersPanel />}
            </aside>
          )}
          <main className="flex-1 flex flex-col overflow-hidden bg-gray-50 dark:bg-gray-950">
            <QueryChat />
          </main>
        </div>
      </div>
    </ErrorBoundary>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Shell />
      </AuthProvider>
    </ThemeProvider>
  );
}
