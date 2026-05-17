import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { UserResponse, UserRole } from "../../types/ui";

const inputClass =
  "w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-400";
const btnClass =
  "w-full py-2 bg-indigo-600 text-white text-sm font-medium rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed";

function ChevronIcon({ open }: { open: boolean }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={`transition-transform duration-200 ${open ? "rotate-180" : ""}`}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  );
}

function SpinnerIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className="animate-spin text-gray-400 dark:text-gray-500"
    >
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  );
}

const roleBadge: Record<string, string> = {
  admin:       "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300",
  contributor: "bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300",
  user:        "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300",
};

function UsersContent() {
  const queryClient = useQueryClient();
  const { user: currentUser } = useAuth();

  const { data: users = [], isLoading, isError } = useQuery<UserResponse[]>({
    queryKey: ["users"],
    queryFn: () => api.listUsers(),
  });

  const { mutate: deleteUser, variables: deletingUserId } = useMutation({
    mutationFn: (userId: string) => api.deleteUser(userId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["users"] }),
  });

  const [showForm, setShowForm] = useState(false);
  const [newUsername, setNewUsername] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [newRole, setNewRole] = useState<UserRole>("user");
  const [formError, setFormError] = useState("");

  const { mutate: createUser, isPending: creating } = useMutation({
    mutationFn: () => api.createUser(newUsername, newPassword, newRole),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
      setShowForm(false);
      setNewUsername("");
      setNewPassword("");
      setNewRole("user");
      setFormError("");
    },
    onError: (err) => setFormError((err as Error).message),
  });

  if (isLoading) return <p className="text-xs text-gray-400 animate-pulse">Loading…</p>;
  if (isError) return <p className="text-xs text-red-500">Failed to load users.</p>;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          {users.length} user{users.length !== 1 ? "s" : ""}
        </p>
        <button
          onClick={() => setShowForm((s) => !s)}
          className="text-xs px-2 py-1 bg-indigo-600 text-white rounded hover:bg-indigo-700"
        >
          {showForm ? "Cancel" : "+ Add User"}
        </button>
      </div>

      {showForm && (
        <div className="space-y-2 p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
          <input
            type="text"
            placeholder="Username"
            value={newUsername}
            onChange={(e) => setNewUsername(e.target.value)}
            className={inputClass}
          />
          <input
            type="password"
            placeholder="Password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className={inputClass}
          />
          <select
            value={newRole}
            onChange={(e) => setNewRole(e.target.value as UserRole)}
            className={inputClass}
          >
            <option value="user">User</option>
            <option value="contributor">Contributor</option>
            <option value="admin">Admin</option>
          </select>
          {formError && <p className="text-red-500 text-xs">{formError}</p>}
          <button
            onClick={() => createUser()}
            disabled={!newUsername || !newPassword || creating}
            className={btnClass}
          >
            {creating ? "Creating…" : "Create User"}
          </button>
        </div>
      )}

      <div className="space-y-1">
        {users.map((u) => (
          <div
            key={u.user_id}
            className="flex items-center justify-between px-2 py-1.5 rounded hover:bg-gray-50 dark:hover:bg-gray-700/40 group"
          >
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-xs font-medium text-gray-800 dark:text-gray-200 truncate">
                {u.username}
              </span>
              <span
                className={`px-1.5 py-0.5 rounded text-xs font-medium flex-shrink-0 ${roleBadge[u.role] ?? ""}`}
              >
                {u.role}
              </span>
            </div>
            {u.user_id !== currentUser?.user_id &&
              (deletingUserId === u.user_id ? (
                <SpinnerIcon />
              ) : (
                <button
                  onClick={() => deleteUser(u.user_id)}
                  className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400"
                  title="Delete user"
                >
                  <TrashIcon />
                </button>
              ))}
          </div>
        ))}
      </div>
    </div>
  );
}

export function UsersPanel() {
  const [open, setOpen] = useState(true);

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm overflow-hidden">
      <button
        onClick={() => setOpen((s) => !s)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-700/40 transition-colors"
      >
        <h2 className="font-semibold text-sm text-gray-900 dark:text-gray-100">User Management</h2>
        <span className="text-gray-400 dark:text-gray-500">
          <ChevronIcon open={open} />
        </span>
      </button>

      {open && (
        <div className="px-4 pb-4 pt-1 border-t border-gray-100 dark:border-gray-700">
          <UsersContent />
        </div>
      )}
    </div>
  );
}
