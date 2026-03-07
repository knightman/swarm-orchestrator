import { Activity, Box, Server, AlertTriangle, Layers, MapPin, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { useHealth, useStacks } from "../hooks/useApi";
import StatusBadge from "../components/StatusBadge";
import type { SwarmStack } from "../api/types";

export default function Dashboard() {
  const { data: health, isLoading, error } = useHealth();
  const { data: stacks } = useStacks();

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
        <StatCard icon={Server} label="Nodes" value={String(health.node_count)} to="/nodes" />
        <StatCard icon={Box} label="Services" value={String(health.service_count)} to="/services" />
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

      {stacks && stacks.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Stacks</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {stacks.map((stack) => (
              <StackCard key={stack.name} stack={stack} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StackCard({ stack }: { stack: SwarmStack }) {
  const statusColors: Record<string, string> = {
    running: "text-green-400 bg-green-400/10 border-green-800",
    degraded: "text-yellow-400 bg-yellow-400/10 border-yellow-800",
    stopped: "text-gray-400 bg-gray-400/10 border-gray-700",
  };
  const badgeClass = statusColors[stack.status] ?? statusColors.stopped;
  const host = window.location.hostname;

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4 space-y-3">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Layers size={16} className="text-gray-400 shrink-0" />
          <span className="font-semibold truncate">{stack.name}</span>
        </div>
        <span className={`text-xs px-2 py-0.5 rounded-full border ${badgeClass}`}>
          {stack.status}
        </span>
      </div>

      <div className="text-sm text-gray-400 space-y-1.5">
        <div className="flex items-start gap-2">
          <Box size={13} className="mt-0.5 shrink-0" />
          <div className="flex flex-wrap gap-1">
            {stack.services.map((s) => (
              <span key={s} className="bg-gray-800 px-1.5 py-0.5 rounded text-xs text-gray-300">{s}</span>
            ))}
          </div>
        </div>

        {stack.nodes.length > 0 && (
          <div className="flex items-center gap-2">
            <MapPin size={13} className="shrink-0" />
            <span className="truncate">{stack.nodes.join(", ")}</span>
          </div>
        )}

        {stack.ports.length > 0 && (
          <div className="flex items-center gap-2 flex-wrap">
            <ExternalLink size={13} className="shrink-0" />
            {stack.ports.map((port) => (
              <a
                key={port}
                href={`http://${host}:${port}`}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 hover:underline text-xs"
              >
                :{port}
              </a>
            ))}
          </div>
        )}
      </div>

      <div className="text-xs text-gray-500">
        {stack.running_replicas}/{stack.desired_replicas} replicas running
      </div>
    </div>
  );
}

function StatCard({
  icon: Icon,
  label,
  value,
  to,
  children,
}: {
  icon: React.ComponentType<{ size?: number }>;
  label: string;
  value: string;
  to?: string;
  children?: React.ReactNode;
}) {
  const content = (
    <div className="flex items-center gap-2 text-gray-400 text-sm mb-1">
      <Icon size={16} />
      {label}
    </div>
  );

  const inner = (
    <>
      {content}
      {children ?? <p className="text-2xl font-bold">{value}</p>}
    </>
  );

  if (to) {
    return (
      <Link
        to={to}
        className="block rounded-xl border border-gray-800 bg-gray-900 p-4 hover:border-gray-600 hover:bg-gray-800 transition-colors"
      >
        {inner}
      </Link>
    );
  }

  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4">
      {inner}
    </div>
  );
}
