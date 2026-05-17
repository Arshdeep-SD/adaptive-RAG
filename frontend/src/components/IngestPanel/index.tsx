import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../../api/client";
import { useAuth } from "../../context/AuthContext";
import type { IngestResponse, JobResponse } from "../../types/ui";


type TabId = "file" | "json" | "url" | "files";

export function IngestPanel() {
  const [tab, setTab] = useState<TabId>("file");
  const [activeJob, setActiveJob] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  const { data: job } = useQuery({
    queryKey: ["job", activeJob],
    queryFn: () => api.getJob(activeJob!),
    enabled: !!activeJob,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "READY" || status === "FAILED" ? false : 2000;
    },
  });

  const onIngestStart = () => setUploading(true);
  const onIngestSuccess = (res: IngestResponse) => { setUploading(false); setActiveJob(res.job_id); };
  const onIngestError = () => setUploading(false);

  const tabs: TabId[] = ["file", "json", "url", "files"];

  const displayStatus = uploading ? "UPLOADING" : job?.status;

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 shadow-sm p-4 flex flex-col gap-4">
      <h2 className="font-semibold text-gray-900 dark:text-gray-100">Ingest Data</h2>

      {/* Tab bar */}
      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700 flex-wrap">
        {tabs.map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-3 py-2 text-sm capitalize transition-colors border-b-2 ${
              tab === t
                ? "border-indigo-500 text-indigo-600 dark:text-indigo-400 font-medium"
                : "border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      {tab === "file" && <FileTab onStart={onIngestStart} onSuccess={onIngestSuccess} onError={onIngestError} />}
      {tab === "json" && <JsonTab onStart={onIngestStart} onSuccess={onIngestSuccess} onError={onIngestError} />}
      {tab === "url" && <UrlTab onStart={onIngestStart} onSuccess={onIngestSuccess} onError={onIngestError} />}
      {tab === "files" && <FilesTab />}

      {/* Job status */}
      {displayStatus && (
        <div className="text-sm">
          <JobStatusBadge status={displayStatus} />
          {job?.record_count != null && job.record_count > 0 && (
            <span className="ml-2 text-gray-500 dark:text-gray-400">{job.record_count} records indexed</span>
          )}
          {job?.error && <p className="text-red-500 mt-1">{job.error}</p>}
        </div>
      )}
    </div>
  );
}

function JobStatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    UPLOADING:  "bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-400",
    PENDING:    "bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400",
    PROCESSING: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400",
    READY:      "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400",
    FAILED:     "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400",
  };
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${styles[status] ?? "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"}`}>
      {status}
    </span>
  );
}

const inputClass = "w-full border border-gray-300 dark:border-gray-600 rounded px-3 py-1.5 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-400";
const btnClass = "w-full py-2 bg-indigo-600 text-white text-sm font-medium rounded hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed";

type TabProps = {
  onStart: () => void;
  onSuccess: (r: IngestResponse) => void;
  onError: () => void;
};

function FileTab({ onStart, onSuccess, onError }: TabProps) {
  const [file, setFile] = useState<File | null>(null);
  const { mutate, isPending, error } = useMutation({
    mutationFn: () => api.ingestFile(file!),
    onMutate: onStart,
    onSuccess,
    onError,
  });

  return (
    <div className="space-y-3">
      <input
        type="file"
        accept="*"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        className="block w-full text-sm text-gray-500 dark:text-gray-400 file:mr-3 file:py-1.5 file:px-3 file:border-0 file:text-sm file:bg-indigo-50 dark:file:bg-indigo-900/40 file:text-indigo-700 dark:file:text-indigo-300 file:rounded cursor-pointer"
      />
      <button onClick={() => mutate()} disabled={!file || isPending} className={btnClass}>
        {isPending ? "Uploading…" : "Upload & Ingest"}
      </button>
      {error && <p className="text-red-500 text-xs">{(error as Error).message}</p>}
    </div>
  );
}

function JsonTab({ onStart, onSuccess, onError }: TabProps) {
  const [raw, setRaw] = useState("");
  const [label, setLabel] = useState("paste");
  const [parseError, setParseError] = useState("");
  const { mutate, isPending, error } = useMutation({
    mutationFn: (data: object) => api.ingestJson(data, label),
    onMutate: onStart,
    onSuccess,
    onError,
  });

  const handleSubmit = () => {
    setParseError("");
    try { mutate(JSON.parse(raw)); }
    catch { setParseError("Invalid JSON"); }
  };

  return (
    <div className="space-y-3">
      <input type="text" placeholder="Source label" value={label} onChange={(e) => setLabel(e.target.value)} className={inputClass} />
      <textarea
        rows={6}
        placeholder='{"key": "value"}'
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        className={`${inputClass} font-mono resize-y`}
      />
      {parseError && <p className="text-red-500 text-xs">{parseError}</p>}
      {error && <p className="text-red-500 text-xs">{(error as Error).message}</p>}
      <button onClick={handleSubmit} disabled={!raw.trim() || isPending} className={btnClass}>
        {isPending ? "Ingesting…" : "Ingest JSON"}
      </button>
    </div>
  );
}

function UrlTab({ onStart, onSuccess, onError }: TabProps) {
  const [url, setUrl] = useState("");
  const { mutate, isPending, error } = useMutation({
    mutationFn: () => api.ingestUrl(url),
    onMutate: onStart,
    onSuccess,
    onError,
  });

  return (
    <div className="space-y-3">
      <input type="url" placeholder="https://example.com/data.csv" value={url} onChange={(e) => setUrl(e.target.value)} className={inputClass} />
      {error && <p className="text-red-500 text-xs">{(error as Error).message}</p>}
      <button onClick={() => mutate()} disabled={!url.trim() || isPending} className={btnClass}>
        {isPending ? "Fetching…" : "Fetch & Ingest URL"}
      </button>
    </div>
  );
}

function formatBytes(bytes?: number): string {
  if (bytes == null) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(iso?: string): string {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
}

const statusColors: Record<string, string> = {
  UPLOADING:  "bg-orange-100 dark:bg-orange-900/40 text-orange-700 dark:text-orange-400",
  PENDING:    "bg-yellow-100 dark:bg-yellow-900/40 text-yellow-700 dark:text-yellow-400",
  PROCESSING: "bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-400",
  READY:      "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400",
  FAILED:     "bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-400",
};

function FilesTab() {
  const { user } = useAuth();
  const queryClient = useQueryClient();

  const { data: jobs = [], isLoading, isError } = useQuery<JobResponse[]>({
    queryKey: ["jobs"],
    queryFn: () => api.listJobs(),
    refetchInterval: (query) => {
      const jobs = query.state.data ?? [];
      return jobs.some((j) => j.status === "PENDING" || j.status === "PROCESSING") ? 2000 : 10000;
    },
  });

  const [deleteError, setDeleteError] = useState<string | null>(null);
  const { mutate: deleteJob, variables: deletingId } = useMutation({
    mutationFn: (jobId: string) => api.deleteJob(jobId),
    onSuccess: () => {
      setDeleteError(null);
      queryClient.invalidateQueries({ queryKey: ["jobs"] });
    },
    onError: (err: unknown) => {
      const msg = err instanceof Error ? err.message : "Delete failed";
      setDeleteError(msg);
    },
  });

  const { mutate: toggleVisibility, variables: togglingId, isPending: isToggling } = useMutation({
    mutationFn: ({ jobId, visibility }: { jobId: string; visibility: "private" | "public" }) =>
      api.setJobVisibility(jobId, visibility),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["jobs"] }),
  });

  if (isLoading) return <p className="text-xs text-gray-400 dark:text-gray-500 animate-pulse">Loading…</p>;
  if (isError) return <p className="text-xs text-red-500">Failed to load files.</p>;
  if (jobs.length === 0) return <p className="text-xs text-gray-400 dark:text-gray-500 text-center py-4">No files ingested yet.</p>;

  const isAdmin = user?.role === "admin";

  return (
    <div className="overflow-x-auto -mx-1">
      {deleteError && (
        <p className="text-xs text-red-500 mb-2">Delete failed: {deleteError}</p>
      )}
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-200 dark:border-gray-700 text-left text-gray-500 dark:text-gray-400">
            <th className="pb-1.5 pr-2 font-medium">File</th>
            <th className="pb-1.5 pr-2 font-medium">Size</th>
            <th className="pb-1.5 pr-2 font-medium">Added</th>
            <th className="pb-1.5 pr-2 font-medium">Status</th>
            {isAdmin && <th className="pb-1.5 pr-2 font-medium">Visibility</th>}
            <th className="pb-1.5" />
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
          {jobs.map((job) => (
            <tr key={job.job_id} className="hover:bg-gray-50 dark:hover:bg-gray-700/40 group">
              <td className="py-2 pr-2 max-w-[90px]">
                <span className="block truncate font-medium text-gray-800 dark:text-gray-200" title={job.source_ref}>
                  {job.source_ref ?? "—"}
                </span>
                {job.record_count > 0 && (
                  <span className="text-gray-400 dark:text-gray-500">{job.record_count} records</span>
                )}
              </td>
              <td className="py-2 pr-2 text-gray-500 dark:text-gray-400 whitespace-nowrap">{formatBytes(job.file_size)}</td>
              <td className="py-2 pr-2 text-gray-500 dark:text-gray-400 whitespace-nowrap">{formatDate(job.created_at)}</td>
              <td className="py-2 pr-2">
                <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${statusColors[job.status] ?? "bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300"}`}>
                  {job.status}
                </span>
              </td>
              {isAdmin && (
                <td className="py-2 pr-2">
                  {isToggling && togglingId?.jobId === job.job_id ? (
                    <SpinnerIcon />
                  ) : (
                    <button
                      onClick={() =>
                        toggleVisibility({
                          jobId: job.job_id,
                          visibility: job.visibility === "public" ? "private" : "public",
                        })
                      }
                      className={`px-1.5 py-0.5 rounded text-xs font-medium transition-colors ${
                        job.visibility === "public"
                          ? "bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-400 hover:bg-green-200"
                          : "bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-600"
                      }`}
                      title={job.visibility === "public" ? "Make private" : "Make public"}
                    >
                      {job.visibility === "public" ? "Public" : "Private"}
                    </button>
                  )}
                </td>
              )}
              <td className="py-2">
                {deletingId === job.job_id ? (
                  <SpinnerIcon />
                ) : (
                  <button
                    onClick={() => deleteJob(job.job_id)}
                    title="Delete file"
                    className="opacity-0 group-hover:opacity-100 transition-opacity text-gray-400 dark:text-gray-500 hover:text-red-500 dark:hover:text-red-400"
                  >
                    <TrashIcon />
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SpinnerIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="animate-spin text-gray-400 dark:text-gray-500">
      <path d="M21 12a9 9 0 1 1-6.219-8.56" />
    </svg>
  );
}

function TrashIcon() {
  return (
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="3 6 5 6 21 6" />
      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
      <path d="M10 11v6M14 11v6" />
      <path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2" />
    </svg>
  );
}
