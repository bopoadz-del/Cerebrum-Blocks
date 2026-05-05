import React, { useState, useRef } from 'react';
import {
  ChevronRight,
  ChevronDown,
  Plus,
  Cloud,
  Folder,
  FileText,
  HardDrive,
  Server,
  Smartphone,
  ExternalLink,
} from 'lucide-react';
import type { Project, DriveSource, FileNode } from '@/types';

interface LeftSidebarProps {
  projects: Project[];
  drives: DriveSource[];
  onNewChat: () => void;
  onConnectDrive: () => void;
  onSelectProject: (project: Project) => void;
  onSelectFile: (file: FileNode, drive: DriveSource) => void;
  isOpen: boolean;
  onToggle: () => void;
  width: number;
  onResize: (width: number) => void;
}

const fileIcons: Record<string, React.ReactNode> = {
  folder: <Folder className="w-4 h-4" />,
  file: <FileText className="w-4 h-4" />,
};

const driveIcons: Record<string, React.ReactNode> = {
  local: <HardDrive className="w-4 h-4" />,
  server: <Server className="w-4 h-4" />,
  google: <ExternalLink className="w-4 h-4" />,
  onedrive: <Cloud className="w-4 h-4" />,
  android: <Smartphone className="w-4 h-4" />,
  dropbox: <Cloud className="w-4 h-4" />,
};

function FileTree({
  node,
  drive,
  onSelect,
  depth = 0
}: {
  node: FileNode;
  drive: DriveSource;
  onSelect: (file: FileNode, drive: DriveSource) => void;
  depth?: number;
}) {
  const [expanded, setExpanded] = useState(node.expanded || false);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <div>
      <button
        onClick={() => {
          if (hasChildren) {
            setExpanded(!expanded);
          } else {
            onSelect(node, drive);
          }
        }}
        className={`w-full flex items-center gap-1.5 px-2 py-1 text-sm rounded-lg transition-colors hover:bg-[hsl(var(--muted))] ${
          node.selected ? 'bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]' : 'text-[hsl(var(--sidebar-fg))]'
        }`}
        style={{ paddingLeft: `${12 + depth * 16}px` }}
      >
        {hasChildren ? (
          expanded ? <ChevronDown className="w-3 h-3 shrink-0" /> : <ChevronRight className="w-3 h-3 shrink-0" />
        ) : (
          <span className="w-3 h-3 shrink-0" />
        )}
        <span className="shrink-0 opacity-60">
          {node.type === 'folder' ? fileIcons.folder : fileIcons.file}
        </span>
        <span className="truncate">{node.name}</span>
      </button>
      {hasChildren && expanded && (
        <div>
          {node.children!.map(child => (
            <FileTree
              key={child.id}
              node={child}
              drive={drive}
              onSelect={onSelect}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default function LeftSidebar({
  projects,
  drives,
  onNewChat,
  onConnectDrive,
  onSelectProject,
  onSelectFile,
  isOpen,
  onToggle,
  width,
  onResize
}: LeftSidebarProps) {
  const [expandedDrives, setExpandedDrives] = useState<Set<string>>(new Set());
  const [isResizing, setIsResizing] = useState(false);
  const sidebarRef = useRef<HTMLDivElement>(null);

  const toggleDrive = (driveId: string) => {
    setExpandedDrives(prev => {
      const next = new Set(prev);
      if (next.has(driveId)) {
        next.delete(driveId);
      } else {
        next.add(driveId);
      }
      return next;
    });
  };

  const handleResizeStart = () => {
    setIsResizing(true);
  };

  React.useEffect(() => {
    if (!isResizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const newWidth = Math.max(220, Math.min(400, e.clientX));
      onResize(newWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isResizing, onResize]);

  if (!isOpen) {
    return (
      <button
        onClick={onToggle}
        className="fixed left-0 top-1/2 -translate-y-1/2 z-40 p-2 bg-[hsl(var(--sidebar-bg))] border border-[hsl(var(--border))] rounded-r-xl shadow-lg hover:bg-[hsl(var(--muted))] transition-colors"
      >
        <ChevronRight className="w-4 h-4" />
      </button>
    );
  }

  return (
    <div
      ref={sidebarRef}
      className="relative flex flex-col h-full bg-[hsl(var(--sidebar-bg))] border-r border-[hsl(var(--border))] shrink-0 transition-all rounded-r-2xl"
      style={{ width: `${width}px` }}
    >
      {/* Resize Handle */}
      <div
        className="absolute right-0 top-0 bottom-0 w-1 cursor-col-resize hover:bg-[hsl(var(--primary))] transition-colors z-10"
        onMouseDown={handleResizeStart}
      />

      {/* Header */}
      <div className="flex items-center gap-2 p-4 border-b border-[hsl(var(--border))]">
        <button
          onClick={onToggle}
          className="p-1 hover:bg-[hsl(var(--muted))] rounded-lg transition-colors"
        >
          <ChevronDown className="w-4 h-4 rotate-90" />
        </button>
        <div className="flex items-center gap-2 flex-1">
          <img src="/cerebrum-logo.png" alt="Cerebrum" className="w-6 h-6 object-contain" />
          <span className="font-semibold text-sm tracking-tight">Cerebrum</span>
        </div>
      </div>

      {/* Actions */}
      <div className="p-3 space-y-2">
        <button
          onClick={onNewChat}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm bg-[hsl(var(--primary))] text-[hsl(var(--primary-foreground))] rounded-xl hover:opacity-90 transition-opacity"
        >
          <Plus className="w-4 h-4" />
          New Chat
        </button>
        <button
          onClick={onConnectDrive}
          className="w-full flex items-center gap-2 px-3 py-2 text-sm border border-[hsl(var(--border))] rounded-xl hover:bg-[hsl(var(--muted))] transition-colors text-[hsl(var(--sidebar-fg))]"
        >
          <Cloud className="w-4 h-4" />
          Connect Drive
        </button>
      </div>

      {/* Projects Section */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        <div className="px-3 py-2">
          <div className="text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider mb-2 px-2">
            Projects
          </div>
          <div className="space-y-0.5">
            {projects.map(project => (
              <button
                key={project.id}
                onClick={() => onSelectProject(project)}
                className={`w-full text-left px-2 py-1.5 text-sm rounded-lg transition-colors truncate ${
                  project.active
                    ? 'bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]'
                    : 'hover:bg-[hsl(var(--muted))] text-[hsl(var(--sidebar-fg))]'
                }`}
              >
                {project.name}
              </button>
            ))}
          </div>
        </div>

        {/* Connected Drives */}
        <div className="px-3 py-2">
          <div className="text-xs font-medium text-[hsl(var(--muted-foreground))] uppercase tracking-wider mb-2 px-2">
            Connected Drives
          </div>
          <div className="space-y-1">
            {drives.map(drive => (
              <div key={drive.id}>
                <button
                  onClick={() => toggleDrive(drive.id)}
                  className="w-full flex items-center gap-2 px-2 py-1.5 text-sm rounded-lg hover:bg-[hsl(var(--muted))] transition-colors text-[hsl(var(--sidebar-fg))]"
                >
                  {expandedDrives.has(drive.id) ? (
                    <ChevronDown className="w-3 h-3 shrink-0" />
                  ) : (
                    <ChevronRight className="w-3 h-3 shrink-0" />
                  )}
                  <span className="shrink-0 opacity-60">{driveIcons[drive.type]}</span>
                  <span className="truncate flex-1">{drive.name}</span>
                  {drive.connected && (
                    <span className="w-2 h-2 rounded-full bg-[hsl(var(--success))] shrink-0" />
                  )}
                </button>
                {expandedDrives.has(drive.id) && drive.files && (
                  <div className="mt-0.5">
                    {drive.files.map(file => (
                      <FileTree
                        key={file.id}
                        node={file}
                        drive={drive}
                        onSelect={onSelectFile}
                      />
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="p-3 border-t border-[hsl(var(--border))]">
        <div className="flex items-center gap-2 px-2 py-1.5 text-xs text-[hsl(var(--muted-foreground))]">
          <span>ZVec Intelligence</span>
        </div>
      </div>
    </div>
  );
}
