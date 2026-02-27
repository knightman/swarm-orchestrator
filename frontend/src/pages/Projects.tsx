import { useProjects } from "../hooks/useApi";
import type { ProjectFolder } from "../api/types";

export default function Projects() {
  const { data: projects, isLoading, error, refetch } = useProjects();

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">Projects</h2>
        <button
          onClick={() => refetch()}
          className="text-sm text-gray-400 hover:text-white border border-gray-700 rounded-lg px-3 py-1.5 transition-colors"
        >
          Refresh
        </button>
      </div>

      {isLoading && <p className="text-gray-400">Loading projects...</p>}
      {error && <p className="text-red-400">Error: {(error as Error).message}</p>}

      {projects && projects.length > 0 ? (
        <div className="overflow-x-auto rounded-xl border border-gray-800">
          <table className="w-full text-left">
            <thead className="bg-gray-900 text-xs text-gray-400 uppercase">
              <tr>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Files</th>
              </tr>
            </thead>
            <tbody>
              {projects.map((p) => (
                <ProjectRow key={p.name} project={p} />
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        !isLoading && <p className="text-gray-500">No projects found.</p>
      )}
    </div>
  );
}

function ProjectRow({ project }: { project: ProjectFolder }) {
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-900/50">
      <td className="py-3 px-4 font-medium">{project.name}</td>
      <td className="py-3 px-4 flex gap-2">
        {project.has_dockerfile && (
          <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-blue-500/20 text-blue-400">
            Dockerfile
          </span>
        )}
        {project.has_compose && (
          <span className="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium bg-purple-500/20 text-purple-400">
            docker-compose
          </span>
        )}
        {!project.has_dockerfile && !project.has_compose && (
          <span className="text-sm text-gray-500">—</span>
        )}
      </td>
    </tr>
  );
}
