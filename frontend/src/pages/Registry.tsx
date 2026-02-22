import { useState } from "react";
import { useRegistryRepos } from "../hooks/useApi";
import { api } from "../api/client";

export default function Registry() {
  const { data: repos, isLoading, error } = useRegistryRepos();
  const [tags, setTags] = useState<Record<string, string[]>>({});

  const loadTags = async (name: string) => {
    if (tags[name]) return;
    const data = await api.get<{ tags: string[] }>(`/registry/repositories/${name}/tags`);
    setTags((prev) => ({ ...prev, [name]: data.tags }));
  };

  if (isLoading) return <p className="text-gray-400">Loading registry...</p>;
  if (error) return <p className="text-red-400">Error: {(error as Error).message}</p>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Registry</h2>

      {repos && repos.length > 0 ? (
        <div className="space-y-2">
          {repos.map((r) => (
            <div key={r.name} className="rounded-xl border border-gray-800 bg-gray-900 p-4">
              <button
                onClick={() => loadTags(r.name)}
                className="font-medium hover:text-blue-400 transition-colors"
              >
                {r.name}
              </button>
              {tags[r.name] && (
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {tags[r.name].map((t) => (
                    <span key={t} className="bg-gray-800 text-gray-300 text-xs px-2 py-0.5 rounded">
                      {t}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      ) : (
        <p className="text-gray-500">No images found in registry.</p>
      )}
    </div>
  );
}
