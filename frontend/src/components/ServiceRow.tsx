import { Play, Square, Minus, Plus } from "lucide-react";
import type { CatalogService } from "../api/types";
import StatusBadge from "./StatusBadge";
import { useDeployService, useStopService, useScaleService } from "../hooks/useApi";

export default function ServiceRow({ service }: { service: CatalogService }) {
  const deploy = useDeployService();
  const stop = useStopService();
  const scale = useScaleService();

  const isRunning = service.status === "running";

  return (
    <tr className="border-b border-gray-800 hover:bg-gray-900/50">
      <td className="py-3 px-4 font-medium">{service.name}</td>
      <td className="py-3 px-4 text-sm text-gray-400">{service.definition.image}</td>
      <td className="py-3 px-4"><StatusBadge status={service.status} /></td>
      <td className="py-3 px-4 text-sm">{service.definition.replicas}</td>
      <td className="py-3 px-4 text-sm text-gray-400">{service.definition.ports.join(", ") || "-"}</td>
      <td className="py-3 px-4">
        <div className="flex gap-1">
          {!isRunning && (
            <button
              onClick={() => deploy.mutate(service.name)}
              className="p-1.5 rounded hover:bg-green-500/20 text-green-400"
              title="Deploy"
            >
              <Play size={14} />
            </button>
          )}
          {isRunning && (
            <>
              <button
                onClick={() => stop.mutate(service.name)}
                className="p-1.5 rounded hover:bg-red-500/20 text-red-400"
                title="Stop"
              >
                <Square size={14} />
              </button>
              <button
                onClick={() => scale.mutate({ name: service.name, replicas: Math.max(0, service.definition.replicas - 1) })}
                className="p-1.5 rounded hover:bg-gray-700 text-gray-400"
                title="Scale down"
              >
                <Minus size={14} />
              </button>
              <button
                onClick={() => scale.mutate({ name: service.name, replicas: service.definition.replicas + 1 })}
                className="p-1.5 rounded hover:bg-gray-700 text-gray-400"
                title="Scale up"
              >
                <Plus size={14} />
              </button>
            </>
          )}
        </div>
      </td>
    </tr>
  );
}
