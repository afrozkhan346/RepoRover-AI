import { useEffect, useMemo, useState } from "react";
import axios from "axios";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";

type GraphApiNode = {
  id: string;
  data?: {
    label?: string;
  };
};

type GraphApiEdge = {
  id: string;
  source: string;
  target: string;
  label?: string;
};

type GraphApiResponse = {
  nodes: GraphApiNode[];
  edges: GraphApiEdge[];
};

type GraphViewProps = {
  projectName?: string | null;
  title?: string;
};

export default function GraphView({ projectName, title = "Project Graph" }: GraphViewProps) {
  const [graph, setGraph] = useState<GraphApiResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!projectName) {
      setGraph(null);
      setError("Upload or clone a project first to view its graph.");
      return;
    }

    const loadGraph = async () => {
      setLoading(true);
      setError(null);

      try {
        const res = await axios.get<GraphApiResponse>(
          `http://127.0.0.1:8000/project/graph-full/${encodeURIComponent(projectName)}`,
        );
        setGraph(res.data);
      } catch (requestError) {
        const message = axios.isAxiosError(requestError)
          ? requestError.response?.data?.detail || requestError.message || "Unable to load graph"
          : requestError instanceof Error
            ? requestError.message
            : "Unable to load graph";
        setError(message);
        setGraph(null);
      } finally {
        setLoading(false);
      }
    };

    void loadGraph();
  }, [projectName]);

  const { nodes, edges } = useMemo(() => {
    if (!graph) {
      return { nodes: [], edges: [] };
    }

    const columnWidths = 280;
    const rowSpacing = 120;
    const groupHeights: Record<string, number> = {};
    const order = ["file", "class", "function", "module"];

    const mappedNodes: Node[] = graph.nodes.map((node) => {
      const label = node.data?.label || node.id;
      const type = node.id.startsWith("file:")
        ? "file"
        : node.id.startsWith("class:")
          ? "class"
          : node.id.startsWith("function:")
            ? "function"
            : node.id.startsWith("module:")
              ? "module"
              : "other";

      const nodeBackground = node.id.includes("func")
        ? "#4CAF50"
        : node.id.includes("file")
          ? "#2196F3"
          : "#FF9800";
      const column = Math.max(0, order.indexOf(type));
      const row = groupHeights[type] ?? 0;
      groupHeights[type] = row + 1;

      return {
        id: node.id,
        position: { x: column * columnWidths, y: row * rowSpacing },
        data: { label },
        style: {
          border: "1px solid rgba(15, 23, 42, 0.12)",
          borderRadius: 16,
          padding: 14,
          minWidth: 180,
          background: nodeBackground,
          boxShadow: "0 14px 30px rgba(15, 23, 42, 0.12)",
          fontWeight: 700,
          color: "#ffffff",
        },
      };
    });

    const mappedEdges: Edge[] = graph.edges.map((edge, index) => ({
      id: edge.id || `${edge.source}-${edge.target}-${index}`,
      source: edge.source,
      target: edge.target,
      label: edge.label,
      markerEnd: { type: MarkerType.ArrowClosed },
      animated: edge.label === "calls",
      style: {
        stroke: edge.label === "calls" ? "#2563eb" : edge.label === "imports" ? "#f59e0b" : "#94a3b8",
        strokeWidth: 1.8,
      },
      labelStyle: {
        fill: "#334155",
        fontSize: 11,
        fontWeight: 700,
      },
    }));

    return { nodes: mappedNodes, edges: mappedEdges };
  }, [graph]);

  if (loading) {
    return <div className="graph-visualizer-empty">Loading graph...</div>;
  }

  if (error) {
    return <div className="graph-visualizer-empty">{error}</div>;
  }

  if (!nodes.length) {
    return <div className="graph-visualizer-empty">No graph data available yet.</div>;
  }

  return (
    <div className="graph-visualizer-shell">
      <div className="graph-visualizer-header">
        <div>
          <h3>{title}</h3>
          <p>Interactive project graph rendered from backend node-edge data.</p>
        </div>
        <div className="graph-visualizer-meta">
          <span>{nodes.length} nodes</span>
          <span>{edges.length} edges</span>
        </div>
      </div>

      <div className="graph-visualizer-canvas">
        <ReactFlow nodes={nodes} edges={edges} fitView nodesDraggable nodesConnectable={false} elementsSelectable proOptions={{ hideAttribution: true }}>
          <MiniMap zoomable pannable />
          <Controls />
          <Background gap={18} size={1.2} color="rgba(148, 163, 184, 0.28)" />
        </ReactFlow>
      </div>
    </div>
  );
}
