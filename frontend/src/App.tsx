import { BrowserRouter, Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Dashboard from "./pages/Dashboard";
import Services from "./pages/Services";
import Nodes from "./pages/Nodes";
import Registry from "./pages/Registry";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="services" element={<Services />} />
          <Route path="nodes" element={<Nodes />} />
          <Route path="registry" element={<Registry />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
