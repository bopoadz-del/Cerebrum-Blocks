import { memo, useState, useCallback } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import { Trash2, ChevronDown, ChevronUp } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import type { WorkflowNodeData } from '@/lib/workflowEngine';

// Color mapping based on layer or tags
function getNodeColor(blockName: string, tags: string[] = []): string {
  const tagColors: Record<string, string> = {
    ai: '#8b5cf6',
    core: '#3b82f6',
    llm: '#8b5cf6',
    chat: '#8b5cf6',
    vision: '#f59e0b',
    document: '#10b981',
    pdf: '#10b981',
    ocr: '#10b981',
    storage: '#06b6d4',
    integration: '#f97316',
    infrastructure: '#64748b',
    security: '#ef4444',
    construction: '#14b8a6',
    medical: '#ec4899',
    legal: '#6366f1',
    finance: '#84cc16',
    utility: '#a855f7',
  };

  for (const tag of tags) {
    if (tagColors[tag]) return tagColors[tag];
  }

  const nameColors: Record<string, string> = {
    chat: '#8b5cf6',
    pdf: '#10b981',
    ocr: '#10b981',
    image: '#f59e0b',
    code: '#3b82f6',
    search: '#06b6d4',
    web: '#f97316',
    voice: '#ec4899',
    translate: '#14b8a6',
    construction: '#14b8a6',
    bim: '#a855f7',
    memory: '#64748b',
    auth: '#ef4444',
    monitoring: '#6366f1',
  };

  return nameColors[blockName] || '#6366f1';
}

const CerebrumNode = memo(function CerebrumNode(props: NodeProps) {
  const { data, selected } = props;
  const nodeData = data as WorkflowNodeData;
  const [isExpanded, setIsExpanded] = useState(true);
  const [params, setParams] = useState<Record<string, unknown>>(() => (nodeData.params || {}) as Record<string, unknown>);

  const color = getNodeColor(nodeData.block as string, []);

  const updateParam = useCallback((key: string, value: unknown) => {
    const next = { ...params, [key]: value };
    setParams(next);
    nodeData.params = next;
  }, [params, nodeData]);

  const removeParam = useCallback((key: string) => {
    const next = { ...params };
    delete next[key];
    setParams(next);
    nodeData.params = next;
  }, [params, nodeData]);

  const addParam = useCallback(() => {
    const key = `param${Object.keys(params).length + 1}`;
    updateParam(key, '');
  }, [params, updateParam]);

  return (
    <div
      className={`
        min-w-[220px] max-w-[320px] rounded-lg border bg-white shadow-sm
        transition-shadow duration-200
        ${selected ? 'ring-2 ring-offset-1' : ''}
      `}
      style={{ borderColor: color, '--tw-ring-color': color } as React.CSSProperties}
    >
      {/* Header */}
      <div
        className="flex items-center justify-between px-3 py-2 rounded-t-lg"
        style={{ backgroundColor: color + '15' }}
      >
        <div className="flex items-center gap-2 min-w-0">
          <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: color }} />
          <span className="text-sm font-semibold truncate" style={{ color }}>
            {nodeData.block as string}
          </span>
        </div>
        <div className="flex items-center gap-0.5">
          <button
            onClick={() => setIsExpanded(v => !v)}
            className="p-1 rounded hover:bg-black/5 text-gray-500"
          >
            {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        </div>
      </div>

      {/* Params Editor */}
      {isExpanded && (
        <div className="px-3 py-2 space-y-2">
          {Object.entries(params).length === 0 && (
            <p className="text-xs text-gray-400 italic">No parameters set</p>
          )}
          {Object.entries(params).map(([key, value]) => (
            <div key={key} className="flex items-start gap-1.5">
              <div className="flex-1 min-w-0">
                <Label className="text-[10px] uppercase tracking-wide text-gray-500 font-medium">
                  {key}
                </Label>
                {typeof value === 'boolean' ? (
                  <div className="flex items-center gap-2 mt-0.5">
                    <Switch
                      checked={value}
                    onCheckedChange={v => updateParam(key, v)}
                    />
                    <span className="text-xs text-gray-600">
                      {value ? 'true' : 'false'}
                    </span>
                  </div>
                ) : (
                  <Input
                    value={String(value ?? '')}
                    onChange={e => updateParam(key, e.target.value)}
                    className="h-7 text-xs mt-0.5"
                    placeholder="Value..."
                  />
                )}
              </div>
              <button
                onClick={() => removeParam(key)}
                className="mt-5 p-0.5 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
          <Button
            variant="ghost"
            size="sm"
            onClick={addParam}
            className="w-full h-7 text-xs text-gray-500 hover:text-gray-700"
          >
            + Add parameter
          </Button>
        </div>
      )}

      {/* Handles */}
      <Handle
        type="target"
        position={Position.Left}
        className="!w-2.5 !h-2.5 !bg-white !border-2"
        style={{ borderColor: color }}
      />
      <Handle
        type="source"
        position={Position.Right}
        className="!w-2.5 !h-2.5 !bg-white !border-2"
        style={{ borderColor: color }}
      />
    </div>
  );
});

export default CerebrumNode;
