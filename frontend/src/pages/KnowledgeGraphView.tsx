import React, { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  Node,
  Edge,
  BackgroundVariant
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import {
  Network,
  ShieldCheck,
  Beaker,
  Loader2,
  Search,
  X,
  BookOpen,
  ArrowRight,
  Filter
} from 'lucide-react';
import { api } from '../services/api';
import { GraphResponse } from '../types';
import { CodeChip, Badge, PageHeader } from '../components/ui';

export const KnowledgeGraphView: React.FC = () => {
  const { standardId } = useParams<{ standardId?: string }>();
  const navigate = useNavigate();

  const currentStandard = standardId || 'IS 694:2010';
  const [selectedStd, setSelectedStd] = useState(currentStandard);
  const [graphData, setGraphData] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);
  const [catalogueStandards, setCatalogueStandards] = useState<Array<{ standard_number: string; title: string }>>([]);
  const [catalogueLoading, setCatalogueLoading] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');

  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    let isMounted = true;
    setCatalogueLoading(true);
    api.listStandards()
      .then((stds) => {
        if (isMounted && stds && stds.length > 0) {
          setCatalogueStandards(stds);
        }
      })
      .catch(() => {})
      .finally(() => {
        if (isMounted) setCatalogueLoading(false);
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const loadGraph = useCallback(async (stdCode: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getStandardGraph(stdCode);
      setGraphData(data);

      // Enhance node visual styling for warm beige canvas
      const styledNodes = (data.nodes || []).map((node) => {
        const label = node.data?.label || '';
        const isRoot = label.includes(stdCode) || node.data?.standard_number === stdCode;
        const isTestMethod = label.includes('10810') || label.includes('516') || label.includes('2386') || node.data?.node_type === 'TEST_METHOD';
        const isQco = node.data?.node_type === 'QCO' || label.toLowerCase().includes('qco');

        let bg = '#FBF7EE';
        let borderColor = '#A89774';
        let textColor = '#14110C';
        let borderWidth = '2px';

        if (isRoot) {
          bg = '#FBF7EE';
          borderColor = '#0B2A5B';
          borderWidth = '3px';
        } else if (isTestMethod) {
          bg = '#D5EBD3';
          borderColor = '#14622B';
        } else if (isQco) {
          bg = '#F5D2CC';
          borderColor = '#A61B1B';
        }

        return {
          ...node,
          style: {
            ...node.style,
            background: bg,
            borderColor: borderColor,
            borderWidth: borderWidth,
            borderStyle: 'solid',
            color: textColor,
            borderRadius: '12px',
            padding: '12px 16px',
            fontSize: '13px',
            fontWeight: isRoot ? 700 : 600,
            boxShadow: '0 2px 8px rgba(60, 45, 20, 0.08)',
            fontFamily: '"JetBrains Mono", monospace',
          },
        };
      });

      const styledEdges = (data.edges || []).map((edge) => ({
        ...edge,
        style: {
          ...edge.style,
          stroke: '#8A4B00',
          strokeWidth: 2,
        },
      }));

      setNodes(styledNodes as Node[]);
      setEdges(styledEdges as Edge[]);
      setSelectedNodeData(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || `Unable to load relationship graph for ${stdCode}`);
    } finally {
      setLoading(false);
    }
  }, [setNodes, setEdges]);

  useEffect(() => {
    loadGraph(currentStandard);
  }, [currentStandard, loadGraph]);

  const handleSelectChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSelectedStd(val);
    navigate(`/graph/${encodeURIComponent(val)}`);
  };

  const onNodeClick = useCallback((_: any, node: Node) => {
    setSelectedNodeData(node.data);
  }, []);

  return (
    <div className="space-y-6">
      {/* ── 1. Page Header & Standard Selector ─────────────────────────────── */}
      <PageHeader
        title="Interactive Standards Knowledge Graph"
        description="Inspect normative dependencies, mandatory testing methods (IS 10810, IS 516), and statutory supersession relationships."
        badge={
          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-bg-sunken text-ink-900 border border-border-default">
            Ontology & Relationships
          </span>
        }
        action={
          <div className="flex items-center gap-2">
            <label htmlFor="std-select" className="text-xs font-bold uppercase tracking-wider text-ink-500 whitespace-nowrap">
              Root:
            </label>
            <select
              id="std-select"
              value={currentStandard}
              onChange={handleSelectChange}
              disabled={catalogueLoading && catalogueStandards.length === 0}
              className="px-3 py-2 bg-bg-surface border border-border-strong rounded-xl text-xs font-mono font-bold text-ink-900 focus:outline-none focus:border-brand shadow-warm-sm max-w-xs"
            >
              {catalogueStandards.length > 0 ? (
                catalogueStandards.map((std) => (
                  <option key={std.standard_number} value={std.standard_number}>
                    {std.standard_number}
                  </option>
                ))
              ) : (
                <>
                  <option value="IS 694:2010">IS 694:2010</option>
                  <option value="IS 1554 (Part 1):1988">IS 1554 (Part 1):1988</option>
                  <option value="IS 456:2000">IS 456:2000</option>
                  <option value="IS 800:2007">IS 800:2007</option>
                  <option value="IS 1786:2008">IS 1786:2008</option>
                </>
              )}
            </select>
          </div>
        }
      />

      {/* ── 2. Graph Canvas with Beige Background ──────────────────────────── */}
      <div className="relative h-[650px] w-full rounded-2xl border-2 border-border-default overflow-hidden bg-bg-base shadow-warm">
        {loading && (
          <div className="absolute inset-0 bg-bg-base/70 backdrop-blur-sm z-20 flex flex-col items-center justify-center space-y-2">
            <Loader2 className="w-8 h-8 text-brand animate-spin" />
            <p className="text-xs font-bold text-ink-700 font-mono">Building ontological dependency graph...</p>
          </div>
        )}

        {/* Legend Overlay Card */}
        <div className="absolute top-4 left-4 z-10 p-4 rounded-xl bg-bg-surface border border-border-default shadow-warm text-xs space-y-2.5 max-w-xs">
          <span className="font-bold uppercase tracking-wider text-ink-900 block text-[11px] border-b border-border-default pb-1.5">
            Graph Legend & Node Types
          </span>
          <div className="space-y-1.5 font-medium text-ink-700">
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded border-2 border-brand bg-bg-surface" />
              <span>Root Indian Standard</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded border-2 border-success bg-success-soft" />
              <span>Mandatory Test Method</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded border-2 border-danger bg-danger-soft" />
              <span>Statutory QCO Order</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="w-3.5 h-3.5 rounded border border-border-strong bg-bg-surface" />
              <span>Normative Reference</span>
            </div>
          </div>
        </div>

        {/* Selected Node Details Drawer */}
        {selectedNodeData && (
          <div className="absolute top-4 right-4 z-10 w-80 p-5 rounded-2xl bg-bg-surface border-2 border-border-strong shadow-warm-lg text-xs space-y-3 animate-slide-up">
            <div className="flex items-center justify-between border-b border-border-default pb-2">
              <span className="font-bold text-sm text-ink-900 font-serif">
                Node Properties
              </span>
              <button
                onClick={() => setSelectedNodeData(null)}
                className="text-ink-500 hover:text-ink-900 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-2">
              <div className="font-bold text-sm text-brand font-mono">
                {selectedNodeData.label || selectedNodeData.standard_number}
              </div>
              {selectedNodeData.node_type && (
                <div>
                  <span className="text-ink-500 font-semibold block text-[11px]">Type:</span>
                  <span className="font-bold text-ink-900">{selectedNodeData.node_type}</span>
                </div>
              )}
              {selectedNodeData.status && (
                <div>
                  <span className="text-ink-500 font-semibold block text-[11px]">Status:</span>
                  <Badge variant={selectedNodeData.status === 'ACTIVE' ? 'active' : 'superseded'} />
                </div>
              )}
            </div>

            {selectedNodeData.standard_number && (
              <div className="pt-2 border-t border-border-default">
                <Link
                  to={`/standards/${encodeURIComponent(selectedNodeData.standard_number)}`}
                  className="w-full py-2 px-3 rounded-lg bg-brand hover:bg-brand-hover text-white text-xs font-bold flex items-center justify-center gap-1.5 shadow-warm"
                >
                  <span>Open Full Standard</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}
          </div>
        )}

        {/* React Flow Component */}
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          fitView
          minZoom={0.2}
          maxZoom={2.5}
        >
          <Background
            color="#D3C6AB"
            variant={BackgroundVariant.Dots}
            gap={24}
            size={1.5}
          />
          <Controls className="!bg-bg-surface !border !border-border-default !rounded-xl !shadow-warm text-ink-900" />
          <MiniMap
            nodeColor={(n: any) => {
              if (String(n.data?.label || '').includes(currentStandard)) return '#0B2A5B';
              if (n.data?.node_type === 'TEST_METHOD') return '#14622B';
              if (n.data?.node_type === 'QCO') return '#A61B1B';
              return '#D3C6AB';
            }}
            maskColor="rgba(243, 235, 220, 0.7)"
            className="!border !border-border-default !rounded-xl !bg-bg-surface"
          />
        </ReactFlow>
      </div>
    </div>
  );
};
