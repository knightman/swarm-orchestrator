import { Cpu, HardDrive, MonitorSpeaker } from "lucide-react";
import type { SwarmNode } from "../api/types";
import StatusBadge from "./StatusBadge";

export default function NodeCard({ node }: { node: SwarmNode }) {
  const { hostname, role, status, availability, addr, platform_arch, engine_version, resources } = node;
  return (
    <div className="rounded-xl border border-gray-800 bg-gray-900 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="font-semibold">{hostname}</h3>
          <p className="text-xs text-gray-500">{addr} &middot; {platform_arch} &middot; {role}</p>
        </div>
        <div className="flex gap-1.5">
          <StatusBadge status={status} />
          <StatusBadge status={availability} />
        </div>
      </div>
      <div className="flex gap-4 text-xs text-gray-400">
        <span className="flex items-center gap-1"><Cpu size={14} /> {resources.cpus.toFixed(0)} cores</span>
        <span className="flex items-center gap-1"><HardDrive size={14} /> {(resources.memory_mb / 1024).toFixed(1)} GB</span>
        {resources.gpus > 0 && <span className="flex items-center gap-1"><MonitorSpeaker size={14} /> {resources.gpus} GPU</span>}
        <span className="ml-auto">Docker {engine_version}</span>
      </div>
    </div>
  );
}
