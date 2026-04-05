import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  MarkerType,
  type Edge,
  type Node,
} from "reactflow";
import "reactflow/dist/style.css";

type GraphNode = {
  id: string;
  node_type: string;
  label: string;
  file_path?: string | null;
};

type GraphEdge = {
  source: string;
  target: string;
  edge_type: string;
};

type GraphData = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  summary?: Record<string, unknown>;
};

type GraphVisualizerProps = {
  title: string;
  description?: string;
  graphData?: GraphData | null;
  flowPath?: string[] | null;
};

type FlowNodeData = {
  label: string;
  nodeType: string;
};

const NODE_COLUMNS: Record<string, number> = {
  file: 0,
  class: 1,
  function: 2,
  module: 3,
  "import-context": 3,
  external: 4,
};

const NODE_COLORS: Record<string, string> = {
  file: "#0ea5e9",
  class: "#8b5cf6",
  function: "#10b981",
  module: "#f59e0b",
  "import-context": "#f97316",
  external: "#ef4444",
  flow: "#2563eb",
};

function escapeLabel(value: string) {
  return value.replace(/\n/g, " ").slice(0, 42);
}

export function GraphVisualizer({ title, description, graphData, flowPath }: GraphVisualizerProps) {
  const { nodes, edges } = useMemo(() => {
    if (graphData?.nodes?.length) {
      const columnCounts = new Map<number, number>();

      const mappedNodes: Node[] = graphData.nodes.map((node) => {
        const column = NODE_COLUMNS[node.node_type] ?? 2;
        const row = columnCounts.get(column) ?? 0;
        columnCounts.set(column, row + 1);

        return {
          id: node.id,
          type: "default",
          position: { x: column * 260, y: row * 120 },
          data: {
            label: node.label,
            nodeType: node.node_type,
          },
          style: {
            border: `1px solid ${NODE_COLORS[node.node_type] ?? "#94a3b8"}`,
            borderRadius: 16,
            padding: 14,
            background: "rgba(255, 255, 255, 0.96)",
            color: "#0f172a",
            boxShadow: "0 14px 36px rgba(15, 23, 42, 0.12)",
            fontSize: 13,
            fontWeight: 700,
            minWidth: 170,
            maxWidth: 220,
          },
        };
      });

      const mappedEdges: Edge[] = graphData.edges.map((edge, index) => ({
        id: `${edge.source}-${edge.target}-${index}`,
        source: edge.source,
        target: edge.target,
        label: edge.edge_type,
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: edge.edge_type === "calls",
        style: {
          stroke: edge.edge_type === "calls" ? "#2563eb" : edge.edge_type === "imports" ? "#f59e0b" : "#94a3b8",
          strokeWidth: 1.8,
        },
        labelStyle: {
          fill: "#334155",
          fontSize: 11,
          fontWeight: 700,
        },
      }));

      return { nodes: mappedNodes, edges: mappedEdges };
    }

    if (flowPath?.length) {
      const mappedNodes: Node[] = flowPath.map((label, index) => ({
        id: `flow-${index}`,
        type: "default",
        position: { x: index * 240, y: 0 },
        data: {
          label: escapeLabel(label),
          nodeType: "flow",
        },
        style: {
          border: "1px solid #2563eb",
          borderRadius: 16,
          padding: 14,
          background: "rgba(255, 255, 255, 0.96)",
          color: "#0f172a",
          boxShadow: "0 14px 36px rgba(15, 23, 42, 0.12)",
          fontSize: 13,
          fontWeight: 700,
          minWidth: 180,
          maxWidth: 220,
        },
      }));

      const mappedEdges: Edge[] = flowPath.slice(0, -1).map((_, index) => ({
        id: `flow-edge-${index}`,
        source: `flow-${index}`,
        target: `flow-${index + 1}`,
        markerEnd: { type: MarkerType.ArrowClosed },
        animated: true,
        style: {
          stroke: "#2563eb",
          strokeWidth: 2,
        },
      }));

      return { nodes: mappedNodes, edges: mappedEdges };
    }

    return { nodes: [], edges: [] };
  }, [flowPath, graphData]);

  const summaryText = graphData?.summary ? JSON.stringify(graphData.summary, null, 2) : null;
  const hasContent = nodes.length > 0;

  return (
    <div className="graph-visualizer-shell">
      <div className="graph-visualizer-header">
        <div>
          <h3>{title}</h3>
          {description ? <p>{description}</p> : null}
        </div>
        <div className="graph-visualizer-meta">
          <span>{nodes.length} nodes</span>
          <span>{edges.length} edges</span>
        </div>
      </div>

      {hasContent ? (
        <div className="graph-visualizer-canvas">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            fitView
            nodesDraggable
            nodesConnectable={false}
            elementsSelectable
            proOptions={{ hideAttribution: true }}
          >
            <MiniMap
              zoomable
              pannable
              nodeStrokeColor={(node) => {
                const data = node.data as Partial<FlowNodeData> | undefined;
                return NODE_COLORS[data?.nodeType || "flow"] ?? "#94a3b8";
              }}
            />
            <Controls />
            <Background gap={18} size={1.2} color="rgba(148, 163, 184, 0.28)" />
          </ReactFlow>
        </div>
      ) : (
        <div className="graph-visualizer-empty">No graph data available yet. Run Graph or Flow analysis first.</div>
      )}

      {summaryText ? (
        <details className="graph-visualizer-summary">
          <summary>Graph summary</summary>
          <pre>{summaryText}</pre>
        </details>
      ) : null}
    </div>
  );
}
