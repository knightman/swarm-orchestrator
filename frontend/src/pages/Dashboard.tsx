import { Activity, Box, Server, AlertTriangle } from "lucide-react";
import { useHealth } from "../hooks/useApi";
import NodeCard from "../components/NodeCard";
import StatusBadge from "../components/StatusBadge";

export default function Dashboard() {
  const { data: health, isLoading, error } = useHealth();

  if (isLoading) return <p className="text-gray-400">Loading cluster health...</p>;
  if (error) return <p className="text-red-400">Error: {(error as Error).message}</p>;
  if (!health) return null;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard icon={Activity} label="Status" value={health.status}>
          <StatusBadge status={health.status} />
        </StatCard>
        <StatCard icon={Server} label="Nodes" value={String(health.node_count)} />
        <StatCard icon={Box} label="Services" value={String(health.service_count)} />
        <StatCard icon={AlertTriangle} label="Errors" value={String(health.errors.length)} />
      </div>

      {health.errors.length > 0 && (
        <div className="rounded-xl border border-red-800 bg-red-900/20 p-4 space-y-1">
          <h3 className="font-semibold text-red-400">Errors</h3>
          {health.errors.map((e, i) => (
            <p key={i} className="text-sm text-red-300">{e}</p>
          ))}
        </div>
      )}

      <div>
        <h3 className="text-lg font-semibold mb-3">Nodes</h3>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {health.nodes.map((n) => (
            <NodeCard key={n.id} node={n} />
          ))}
        </div>
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  children,
}: {
  icon: React.ComponentType<{ size?: number }>;
  label: string;
  value: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
        <Icon size={16} />
        {label}
      </div>
      {children ?? <p className="text-2xl font-bold">{value}</p>}
    </div>
  );
}
