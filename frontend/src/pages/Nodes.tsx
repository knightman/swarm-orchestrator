import { useNodes, useDrainNode, useActivateNode } from "../hooks/useApi";
import NodeCard from "../components/NodeCard";

export default function Nodes() {
  const { data: nodes, isLoading, error } = useNodes();
  const drain = useDrainNode();
  const activate = useActivateNode();

  if (isLoading) return <p className="text-gray-400">Loading nodes...</p>;
  if (error) return <p className="text-red-400">Error: {(error as Error).message}</p>;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Nodes</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {nodes?.map((n) => (
          <div key={n.id} className="space-y-2">
            <NodeCard node={n} />
            <div className="flex gap-2 px-1">
              {n.availability !== "drain" && (
                <button
                  onClick={() => drain.mutate(n.id)}
                  className="text-xs px-3 py-1 rounded-lg bg-yellow-500/10 text-yellow-400 hover:bg-yellow-500/20"
                >
                  Drain
                </button>
              )}
              {n.availability !== "active" && (
                <button
                  onClick={() => activate.mutate(n.id)}
                  className="text-xs px-3 py-1 rounded-lg bg-green-500/10 text-green-400 hover:bg-green-500/20"
                >
                  Activate
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
