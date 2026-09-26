'use client'

import type { FullState, ImpactedFile, Severity } from '@/lib/types'

const SEVERITY_COLORS: Record<Severity, string> = {
  critical: '#dc2626',
  high: '#ef4444',
  medium: '#f59e0b',
  low: '#3b82f6',
  info: '#64748b',
}

interface Props {
  state: FullState | null
}

function FileNode({
  path,
  changeType,
  severity,
  reason,
  x,
  y,
}: {
  path: string
  changeType: string
  severity: Severity
  reason: string
  x: number
  y: number
}) {
  const color =
    changeType === 'developer_changed'
      ? '#ef4444'
      : changeType === 'bob_remediated'
      ? '#10b981'
      : changeType === 'bob_discovered'
      ? SEVERITY_COLORS[severity]
      : '#64748b'

  const short = path.split('/').pop() || path

  return (
    <g transform={`translate(${x}, ${y})`}>
      <rect
        x={-70}
        y={-22}
        width={140}
        height={44}
        rx={6}
        fill="rgba(15,22,41,0.95)"
        stroke={color}
        strokeWidth={changeType === 'developer_changed' ? 2 : 1}
      />
      <text
        textAnchor="middle"
        dy={-5}
        fontSize={10}
        fontFamily="monospace"
        fill={color}
        fontWeight={changeType === 'developer_changed' ? 'bold' : 'normal'}
      >
        {short.length > 18 ? short.slice(0, 16) + '…' : short}
      </text>
      <text
        textAnchor="middle"
        dy={10}
        fontSize={8}
        fill="#64748b"
      >
        {changeType === 'developer_changed' ? 'Dev changed' : `Bob: ${severity}`}
      </text>
    </g>
  )
}

export function ImpactGraph({ state }: Props) {
  const ig = state?.impact_graph

  if (!ig) {
    return (
      <div
        className="rounded-xl p-8 border flex items-center justify-center"
        style={{ background: '#0f1629', borderColor: '#1e2d45', minHeight: 300 }}
      >
        <p style={{ color: '#64748b' }}>Run Analysis to see the impact graph</p>
      </div>
    )
  }

  // Layout: source at top, branching down
  const devFiles = ig.developer_changed_files.map((f, i) => ({ path: f, type: 'developer_changed', severity: 'critical' as Severity, reason: 'Developer-changed file', x: 400, y: 80 + i * 60 }))
  const bobFiles = ig.bob_discovered_files.map((f, i) => ({
    path: f.path,
    type: f.change_type,
    severity: f.risk_level,
    reason: f.reason,
    x: 120 + (i % 4) * 200,
    y: 220 + Math.floor(i / 4) * 100,
  }))

  const allNodes = [...devFiles, ...bobFiles]
  const svgH = Math.max(480, 300 + Math.ceil(bobFiles.length / 4) * 100)

  return (
    <div className="space-y-4">
      {/* Summary bar */}
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-lg p-4 border" style={{ background: 'rgba(239,68,68,0.07)', borderColor: 'rgba(239,68,68,0.3)' }}>
          <div className="text-2xl font-bold" style={{ color: '#ef4444' }}>{ig.developer_changed_files.length}</div>
          <div className="text-xs mt-1" style={{ color: '#94a3b8' }}>Developer-changed files</div>
        </div>
        <div className="rounded-lg p-4 border" style={{ background: 'rgba(245,158,11,0.07)', borderColor: 'rgba(245,158,11,0.3)' }}>
          <div className="text-2xl font-bold" style={{ color: '#f59e0b' }}>{ig.bob_discovered_files.length}</div>
          <div className="text-xs mt-1" style={{ color: '#94a3b8' }}>Additional files discovered by Bob</div>
        </div>
        <div className="rounded-lg p-4 border" style={{ background: 'rgba(59,130,246,0.07)', borderColor: 'rgba(59,130,246,0.3)' }}>
          <div className="text-2xl font-bold" style={{ color: '#3b82f6' }}>{ig.changed_symbols.length}</div>
          <div className="text-xs mt-1" style={{ color: '#94a3b8' }}>Changed symbols</div>
        </div>
      </div>

      {/* Source change */}
      <div className="rounded-lg px-4 py-2 border text-sm" style={{ background: '#0f1629', borderColor: '#1e2d45' }}>
        <span style={{ color: '#64748b' }}>Source change: </span>
        <span className="font-mono font-medium" style={{ color: '#a78bfa' }}>{ig.source_change}</span>
      </div>

      {/* SVG graph */}
      <div
        className="rounded-xl border overflow-x-auto"
        style={{ background: '#060b16', borderColor: '#1e2d45' }}
      >
        <svg width="800" height={svgH} style={{ display: 'block' }}>
          {/* Grid */}
          {Array.from({ length: 20 }, (_, i) => (
            <line key={`h${i}`} x1={0} y1={i * 40} x2={800} y2={i * 40} stroke="#0f1629" strokeWidth={1} />
          ))}

          {/* Edges from dev files to bob files */}
          {devFiles.map(dev =>
            bobFiles.map(bob => (
              <line
                key={`${dev.path}-${bob.path}`}
                x1={dev.x}
                y1={dev.y + 22}
                x2={bob.x}
                y2={bob.y - 22}
                stroke="rgba(100,116,139,0.2)"
                strokeWidth={1}
                strokeDasharray="4 3"
              />
            ))
          )}

          {/* Legend */}
          <g transform="translate(10, 10)">
            <rect x={0} y={0} width={200} height={70} rx={6} fill="rgba(15,22,41,0.9)" stroke="#1e2d45" strokeWidth={1} />
            <circle cx={16} cy={18} r={5} fill="#ef4444" />
            <text x={26} y={22} fontSize={9} fill="#94a3b8">Developer-changed (1)</text>
            <circle cx={16} cy={35} r={5} fill="#f59e0b" />
            <text x={26} y={39} fontSize={9} fill="#94a3b8">Bob-discovered ({ig.bob_discovered_files.length})</text>
            <circle cx={16} cy={52} r={5} fill="#10b981" />
            <text x={26} y={56} fontSize={9} fill="#94a3b8">Bob-remediated</text>
          </g>

          {/* Nodes */}
          {allNodes.map(n => (
            <FileNode
              key={n.path}
              path={n.path}
              changeType={n.type}
              severity={n.severity as Severity}
              reason={n.reason}
              x={n.x}
              y={n.y}
            />
          ))}
        </svg>
      </div>

      {/* File list */}
      <div className="rounded-xl border" style={{ background: '#0f1629', borderColor: '#1e2d45' }}>
        <div className="px-4 py-3 border-b text-sm font-medium" style={{ borderColor: '#1e2d45', color: '#94a3b8' }}>
          Impacted Files
        </div>
        {ig.bob_discovered_files.map(f => (
          <div
            key={f.path}
            className="px-4 py-3 border-b flex items-start gap-3"
            style={{ borderColor: '#0f1629' }}
          >
            <div
              className="w-2 h-2 rounded-full mt-1.5 flex-shrink-0"
              style={{ background: SEVERITY_COLORS[f.risk_level] }}
            />
            <div className="flex-1 min-w-0">
              <div className="font-mono text-sm" style={{ color: '#e2e8f0' }}>{f.path}</div>
              <div className="text-xs mt-0.5" style={{ color: '#64748b' }}>{f.reason}</div>
            </div>
            <span
              className="text-xs px-2 py-0.5 rounded-full flex-shrink-0"
              style={{
                color: SEVERITY_COLORS[f.risk_level],
                background: `${SEVERITY_COLORS[f.risk_level]}18`,
              }}
            >
              {f.risk_level.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
