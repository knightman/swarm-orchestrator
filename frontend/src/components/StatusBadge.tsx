const colors: Record<string, string> = {
  running: "bg-green-500/20 text-green-400",
  ready: "bg-green-500/20 text-green-400",
  active: "bg-green-500/20 text-green-400",
  healthy: "bg-green-500/20 text-green-400",
  stopped: "bg-gray-500/20 text-gray-400",
  registered: "bg-blue-500/20 text-blue-400",
  failed: "bg-red-500/20 text-red-400",
  down: "bg-red-500/20 text-red-400",
  degraded: "bg-yellow-500/20 text-yellow-400",
  drain: "bg-yellow-500/20 text-yellow-400",
  disconnected: "bg-yellow-500/20 text-yellow-400",
  unknown: "bg-gray-500/20 text-gray-400",
  pause: "bg-yellow-500/20 text-yellow-400",
};

export default function StatusBadge({ status }: { status: string }) {
  const cls = colors[status] ?? colors.unknown;
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
}
