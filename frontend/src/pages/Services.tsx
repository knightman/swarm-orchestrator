import { useServices, useLiveServices } from "../hooks/useApi";
import ServiceRow from "../components/ServiceRow";
import StatusBadge from "../components/StatusBadge";
import type { SwarmService } from "../api/types";

export default function Services() {
  const { data: catalogServices, isLoading: catalogLoading } = useServices();
  const { data: liveServices, isLoading: liveLoading, error: liveError } = useLiveServices();

  return (
    <div className="space-y-8">
      <h2 className="text-2xl font-bold">Services</h2>

      {/* Live Swarm Services */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-300">Swarm Services</h3>
        {liveLoading && <p className="text-gray-400">Loading live services...</p>}
        {liveError && <p className="text-red-400">Error: {(liveError as Error).message}</p>}
        {liveServices && liveServices.length > 0 ? (
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-left">
              <thead className="bg-gray-900 text-xs text-gray-400 uppercase">
                <tr>
                  <th className="py-3 px-4">Name</th>
                  <th className="py-3 px-4">Image</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Replicas</th>
                  <th className="py-3 px-4">Ports</th>
                </tr>
              </thead>
              <tbody>
                {liveServices.map((s) => (
                  <LiveServiceRow key={s.id} service={s} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          !liveLoading && <p className="text-gray-500">No services running in swarm.</p>
        )}
      </section>

      {/* Catalog Services */}
      <section className="space-y-3">
        <h3 className="text-lg font-semibold text-gray-300">Catalog</h3>
        {catalogLoading && <p className="text-gray-400">Loading catalog...</p>}
        {catalogServices && catalogServices.length > 0 ? (
          <div className="overflow-x-auto rounded-xl border border-gray-800">
            <table className="w-full text-left">
              <thead className="bg-gray-900 text-xs text-gray-400 uppercase">
                <tr>
                  <th className="py-3 px-4">Name</th>
                  <th className="py-3 px-4">Image</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Replicas</th>
                  <th className="py-3 px-4">Ports</th>
                  <th className="py-3 px-4">Actions</th>
                </tr>
              </thead>
              <tbody>
                {catalogServices.map((s) => (
                  <ServiceRow key={s.name} service={s} />
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          !catalogLoading && <p className="text-gray-500">No services in catalog. Register a service via the API.</p>
        )}
      </section>
    </div>
  );
}

function LiveServiceRow({ service }: { service: SwarmService }) {
  const healthy = service.running_replicas >= service.replicas;
  return (
    <tr className="border-b border-gray-800 hover:bg-gray-900/50">
      <td className="py-3 px-4 font-medium">{service.name}</td>
      <td className="py-3 px-4 text-sm text-gray-400 max-w-xs truncate">{service.image.split("@")[0]}</td>
      <td className="py-3 px-4">
        <StatusBadge status={healthy ? "running" : "failed"} />
      </td>
      <td className="py-3 px-4 text-sm">{service.running_replicas}/{service.replicas}</td>
      <td className="py-3 px-4 text-sm text-gray-400">{service.ports.join(", ") || "-"}</td>
    </tr>
  );
}
