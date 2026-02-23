import { useState } from "react";
import { useRegistryRepos } from "../hooks/useApi";
import type { RegistryRepositoryDetail, TagDetail } from "../api/types";
import { api } from "../api/client";
import { useQueryClient } from "@tanstack/react-query";

function formatBytes(bytes: number): string {
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${units[i]}`;
}

function timeAgo(iso: string): string {
  if (!iso) return "—";
  const seconds = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (seconds < 60) return "just now";
  if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
  if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
  return `${Math.floor(seconds / 86400)}d ago`;
}

function truncateDigest(digest: string): string {
  if (!digest) return "—";
  // sha256:abc123... → sha256:abc123
  const parts = digest.split(":");
  if (parts.length === 2) return `${parts[0]}:${parts[1].slice(0, 12)}`;
  return digest.slice(0, 19);
}

function RepoCard({ name }: { name: string }) {
  const [expanded, setExpanded] = useState(false);
  const [details, setDetails] = useState<RegistryRepositoryDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmingDelete, setConfirmingDelete] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const qc = useQueryClient();

  const toggle = async () => {
    if (expanded) {
      setExpanded(false);
      return;
    }
    setExpanded(true);
    if (details) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<RegistryRepositoryDetail>(`/registry/repositories/${name}/details`);
      setDetails(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const refresh = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get<RegistryRepositoryDetail>(`/registry/repositories/${name}/details`);
      setDetails(data);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const deleteTag = async (tag: string) => {
    setDeleting(true);
    try {
      await api.delete(`/registry/repositories/${name}/tags/${tag}`);
      setConfirmingDelete(null);
      await refresh();
      qc.invalidateQueries({ queryKey: ["registry"] });
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 overflow-hidden">
      <button
        onClick={toggle}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-800/50 transition-colors text-left"
      >
        <div className="flex items-center gap-3">
          <svg
            className={`w-4 h-4 text-gray-500 transition-transform ${expanded ? "rotate-90" : ""}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="font-medium">{name}</span>
          {details && (
            <span className="bg-blue-500/20 text-blue-400 text-xs px-2 py-0.5 rounded-full">
              {details.tag_count} tag{details.tag_count !== 1 ? "s" : ""}
            </span>
          )}
        </div>
      </button>

      {expanded && (
        <div className="border-t border-gray-800 p-4">
          {loading && <p className="text-gray-400 text-sm">Loading tags...</p>}
          {error && <p className="text-red-400 text-sm">Error: {error}</p>}
          {details && details.tags.length > 0 && (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-gray-500 text-left text-xs uppercase tracking-wider">
                    <th className="pb-2 pr-4">Tag</th>
                    <th className="pb-2 pr-4">Digest</th>
                    <th className="pb-2 pr-4">Size</th>
                    <th className="pb-2 pr-4">Arch</th>
                    <th className="pb-2 pr-4">OS</th>
                    <th className="pb-2 pr-4">Created</th>
                    <th className="pb-2">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-800">
                  {details.tags.map((t: TagDetail) => (
                    <tr key={t.tag} className="text-gray-300">
                      <td className="py-2 pr-4 font-medium text-white">{t.tag}</td>
                      <td className="py-2 pr-4 font-mono text-xs text-gray-400">{truncateDigest(t.digest)}</td>
                      <td className="py-2 pr-4">{t.size > 0 ? formatBytes(t.size) : "—"}</td>
                      <td className="py-2 pr-4">{t.architecture || "—"}</td>
                      <td className="py-2 pr-4">{t.os || "—"}</td>
                      <td className="py-2 pr-4" title={t.created}>{timeAgo(t.created)}</td>
                      <td className="py-2">
                        {confirmingDelete === t.tag ? (
                          <span className="flex items-center gap-2">
                            <span className="text-xs text-gray-400">Delete?</span>
                            <button
                              onClick={() => deleteTag(t.tag)}
                              disabled={deleting}
                              className="text-xs text-red-400 hover:text-red-300 disabled:opacity-50"
                            >
                              {deleting ? "..." : "Yes"}
                            </button>
                            <button
                              onClick={() => setConfirmingDelete(null)}
                              className="text-xs text-gray-400 hover:text-gray-300"
                            >
                              No
                            </button>
                          </span>
                        ) : (
                          <button
                            onClick={() => setConfirmingDelete(t.tag)}
                            className="text-xs text-red-400/60 hover:text-red-400 transition-colors"
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          {details && details.tags.length === 0 && (
            <p className="text-gray-500 text-sm">No tags found.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default function Registry() {
  const { data: repos, isLoading, error, refetch } = useRegistryRepos();

  if (isLoading) return <p className="text-gray-400">Loading registry...</p>;
  if (error) return <p className="text-red-400">Error: {(error as Error).message}</p>;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Registry</h2>
        <button
          onClick={() => refetch()}
          className="text-sm text-gray-400 hover:text-white border border-gray-700 rounded-lg px-3 py-1.5 transition-colors"
        >
          Refresh
        </button>
      </div>

      {repos && repos.length > 0 ? (
        <div className="space-y-2">
          {repos.map((r) => (
            <RepoCard key={r.name} name={r.name} />
          ))}
        </div>
      ) : (
        <p className="text-gray-500">No images found in registry.</p>
      )}
    </div>
  );
}
