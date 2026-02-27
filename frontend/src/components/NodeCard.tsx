import { Cpu, HardDrive, MonitorSpeaker, Box } from "lucide-react";
import type { SwarmNode } from "../api/types";
import StatusBadge from "./StatusBadge";

export default function NodeCard({ node }: { node: SwarmNode }) {
  const { hostname, role, status, availability, addr, platform_arch, engine_version, resources, services } = node;
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
      {services.length > 0 && (
        <div className="border-t border-gray-800 pt-3 space-y-1.5">
          <p className="text-xs text-gray-500 font-medium uppercase tracking-wide">Running Services</p>
          {services.map((svc) => (
            <div key={svc.name} className="flex items-center gap-2 text-xs">
              <Box size={12} className="text-blue-400 shrink-0" />
              <span className="font-medium text-gray-200">{svc.name}</span>
              {svc.replicas_on_node > 1 && (
                <span className="text-gray-500">&times;{svc.replicas_on_node}</span>
              )}
              <span className="text-gray-600 truncate ml-auto">{svc.image.split("/").pop()?.split(":")[0]}</span>
            </div>
          ))}
        </div>
      )}
      {services.length === 0 && (
        <div className="border-t border-gray-800 pt-3">
          <p className="text-xs text-gray-600">No running services</p>
        </div>
      )}
    </div>
  );
}
