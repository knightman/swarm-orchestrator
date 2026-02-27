export interface ServiceDefinition {
  image: string;
  replicas: number;
  ports: string[];
  env: Record<string, string>;
  constraints: string[];
  labels: Record<string, string>;
  networks: string[];
  mounts: string[];
  command: string | null;
  build_context: string | null;
}

export interface CatalogService {
  name: string;
  description: string;
  definition: ServiceDefinition;
  status: "registered" | "running" | "stopped" | "failed" | "unknown";
  swarm_id: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface NodeService {
  name: string;
  image: string;
  replicas_on_node: number;
}

export interface SwarmNode {
  id: string;
  hostname: string;
  role: string;
  status: "ready" | "down" | "disconnected" | "unknown";
  availability: "active" | "pause" | "drain";
  addr: string;
  platform_os: string;
  platform_arch: string;
  engine_version: string;
  labels: Record<string, string>;
  resources: {
    cpus: number;
    memory_mb: number;
    gpus: number;
  };
  services: NodeService[];
}

export interface ClusterHealth {
  status: string;
  swarm_id: string;
  node_count: number;
  service_count: number;
  nodes: SwarmNode[];
  errors: string[];
}

export interface SwarmService {
  id: string;
  name: string;
  image: string;
  replicas: number;
  running_replicas: number;
  completed_replicas: number;
  ports: string[];
  created_at: string;
}

export interface ProjectFolder {
  name: string;
  has_dockerfile: boolean;
  has_compose: boolean;
}

export interface RegistryRepository {
  name: string;
  tags: string[];
}

export interface TagDetail {
  tag: string;
  digest: string;
  media_type: string;
  size: number;
  architecture: string;
  os: string;
  created: string;
}

export interface RegistryRepositoryDetail {
  name: string;
  tags: TagDetail[];
  tag_count: number;
}
