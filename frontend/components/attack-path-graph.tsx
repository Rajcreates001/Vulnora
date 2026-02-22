"use client";

import { useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  ConnectionLineType,
  MarkerType,
  useNodesState,
  useEdgesState,
} from "reactflow";
import "reactflow/dist/style.css";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { GitBranch } from "lucide-react";

const NODE_COLORS: Record<string, { bg: string; border: string; text: string }> = {
  entry_point: { bg: "#1e3a5f", border: "#3b82f6", text: "#93c5fd" },
  function: { bg: "#3b1f2b", border: "#ef4444", text: "#fca5a5" },
  database: { bg: "#1a3329", border: "#22c55e", text: "#86efac" },
  exploit_outcome: { bg: "#3b2f1f", border: "#f97316", text: "#fdba74" },
};

function CustomNode({ data }: { data: any }) {
  const colors = NODE_COLORS[data.nodeType] || NODE_COLORS.function;
  return (
    <div
      className="rounded-lg px-4 py-3 shadow-lg min-w-[160px] max-w-[220px]"
      style={{
        backgroundColor: colors.bg,
        border: `2px solid ${colors.border}`,
      }}
    >
      <div className="text-xs font-semibold mb-1" style={{ color: colors.text }}>
        {data.label}
      </div>
      {data.description && (
        <div className="text-[10px] opacity-70" style={{ color: colors.text }}>
          {data.description}
        </div>
      )}
    </div>
  );
}

const nodeTypes = { custom: CustomNode };

interface AttackPathGraphProps {
  attackPaths: any[];
}

export function AttackPathGraph({ attackPaths }: AttackPathGraphProps) {
  const { nodes: flowNodes, edges: flowEdges } = useMemo(() => {
    const allNodes: Node[] = [];
    const allEdges: Edge[] = [];

    attackPaths.forEach((path, pathIndex) => {
      const yOffset = pathIndex * 200;

      (path.nodes || []).forEach((node: any, nodeIndex: number) => {
        allNodes.push({
          id: `${pathIndex}-${node.id}`,
          type: "custom",
          position: { x: nodeIndex * 280, y: yOffset },
          data: {
            label: node.label,
            description: node.data?.description || "",
            nodeType: node.node_type,
          },
        });
      });

      (path.edges || []).forEach((edge: any) => {
        allEdges.push({
          id: `${pathIndex}-${edge.id}`,
          source: `${pathIndex}-${edge.source}`,
          target: `${pathIndex}-${edge.target}`,
          label: edge.label || "",
          type: "smoothstep",
          animated: true,
          style: { stroke: "#6366f1", strokeWidth: 2 },
          markerEnd: { type: MarkerType.ArrowClosed, color: "#6366f1" },
        });
      });
    });

    return { nodes: allNodes, edges: allEdges };
  }, [attackPaths]);

  const [nodes, setNodes, onNodesChange] = useNodesState(flowNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(flowEdges);

  if (!attackPaths?.length) {
    return (
      <Card className="border-border/50 bg-card/50">
        <CardContent className="flex items-center justify-center py-16 text-muted-foreground">
          <div className="text-center">
            <GitBranch className="h-10 w-10 mx-auto mb-3 opacity-30" />
            <p className="text-sm">No attack paths available</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-border/50 bg-card/50">
      <CardHeader className="pb-2">
        <CardTitle className="text-lg flex items-center gap-2">
          <GitBranch className="h-5 w-5 text-indigo-400" />
          Attack Path Visualization
        </CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="h-[500px] rounded-b-lg overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            nodeTypes={nodeTypes}
            connectionLineType={ConnectionLineType.SmoothStep}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            proOptions={{ hideAttribution: true }}
          >
            <Background color="#1e293b" gap={20} />
            <Controls className="!bg-card !border-border !shadow-lg" />
            <MiniMap
              nodeColor={(node) => {
                const colors = NODE_COLORS[node.data?.nodeType] || NODE_COLORS.function;
                return colors.border;
              }}
              className="!bg-card !border-border"
            />
          </ReactFlow>
        </div>
      </CardContent>
    </Card>
  );
}
