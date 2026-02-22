import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import type { CatalogService, ClusterHealth, RegistryRepository, SwarmNode, SwarmService } from "../api/types";

export function useHealth() {
  return useQuery<ClusterHealth>({
    queryKey: ["health"],
    queryFn: () => api.get("/health/detailed"),
  });
}

export function useNodes() {
  return useQuery<SwarmNode[]>({
    queryKey: ["nodes"],
    queryFn: () => api.get("/nodes"),
  });
}

export function useServices() {
  return useQuery<CatalogService[]>({
    queryKey: ["services"],
    queryFn: () => api.get("/services"),
  });
}

export function useLiveServices() {
  return useQuery<SwarmService[]>({
    queryKey: ["services-live"],
    queryFn: () => api.get("/services/live"),
  });
}

export function useRegistryRepos() {
  return useQuery<RegistryRepository[]>({
    queryKey: ["registry"],
    queryFn: () => api.get("/registry/repositories"),
  });
}

export function useDeployService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.post(`/services/${name}/deploy`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["services"] }),
  });
}

export function useStopService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.post(`/services/${name}/stop`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["services"] }),
  });
}

export function useScaleService() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name, replicas }: { name: string; replicas: number }) =>
      api.post(`/services/${name}/scale`, { replicas }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["services"] }),
  });
}

export function useDrainNode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post(`/nodes/${id}/drain`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["nodes"] }),
  });
}

export function useActivateNode() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => api.post(`/nodes/${id}/activate`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["nodes"] }),
  });
}
