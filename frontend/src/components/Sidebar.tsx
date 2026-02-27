import { NavLink } from "react-router-dom";
import { LayoutDashboard, Box, Server, Archive, FolderOpen } from "lucide-react";

const links = [
  { to: "/", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/services", icon: Box, label: "Services" },
  { to: "/nodes", icon: Server, label: "Nodes" },
  { to: "/registry", icon: Archive, label: "Registry" },
  { to: "/projects", icon: FolderOpen, label: "Projects" },
];

export default function Sidebar() {
  return (
    <aside className="w-56 border-r border-gray-800 bg-gray-900 flex flex-col">
      <div className="p-4 border-b border-gray-800">
        <h1 className="text-lg font-bold tracking-tight">Swarm Orchestrator</h1>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {links.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${
                isActive ? "bg-gray-800 text-white" : "text-gray-400 hover:text-gray-200 hover:bg-gray-800/50"
              }`
            }
          >
            <Icon size={18} />
            {label}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
