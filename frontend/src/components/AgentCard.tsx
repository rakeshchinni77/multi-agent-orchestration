import React from 'react';
import { ListChecks, Microscope, FileText, Bot, Clock } from 'lucide-react';

interface AgentCardProps {
  agentName: string;
  eventType: string;
  payload: Record<string, any>;
  timestamp?: string;
}

export const AgentCard: React.FC<AgentCardProps> = ({
  agentName,
  eventType,
  payload,
  timestamp,
}) => {
  const getAgentTheme = () => {
    switch (agentName.toLowerCase()) {
      case 'planner':
        return {
          icon: ListChecks,
          border: 'border-indigo-500/30',
          bg: 'bg-indigo-500/10',
          text: 'text-indigo-400',
          badge: 'bg-indigo-500/20 text-indigo-300',
        };
      case 'researcher':
        return {
          icon: Microscope,
          border: 'border-cyan-500/30',
          bg: 'bg-cyan-500/10',
          text: 'text-cyan-400',
          badge: 'bg-cyan-500/20 text-cyan-300',
        };
      case 'synthesizer':
        return {
          icon: FileText,
          border: 'border-emerald-500/30',
          bg: 'bg-emerald-500/10',
          text: 'text-emerald-400',
          badge: 'bg-emerald-500/20 text-emerald-300',
        };
      default:
        return {
          icon: Bot,
          border: 'border-slate-500/30',
          bg: 'bg-slate-500/10',
          text: 'text-slate-400',
          badge: 'bg-slate-500/20 text-slate-300',
        };
    }
  };

  const theme = getAgentTheme();
  const Icon = theme.icon;

  return (
    <div className={`agent-card border ${theme.border}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center space-x-2">
          <div className={`p-1.5 rounded-md ${theme.bg} ${theme.text}`}>
            <Icon className="w-4 h-4" />
          </div>
          <span className="font-bold text-slate-200">{agentName}</span>
          <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${theme.badge}`}>
            {eventType.replace('_', ' ')}
          </span>
        </div>
        {timestamp && (
          <span className="text-xs text-slate-400 flex items-center gap-1 font-mono">
            <Clock className="w-3 h-3" />
            {new Date(timestamp).toLocaleTimeString()}
          </span>
        )}
      </div>

      {payload.message && (
        <p className="text-sm text-slate-300 mb-2 leading-relaxed">{payload.message}</p>
      )}

      {payload.steps && Array.isArray(payload.steps) && (
        <div className="mt-3 bg-slate-900/60 p-3 rounded-lg border border-slate-800">
          <span className="text-xs font-mono uppercase tracking-wider text-indigo-400 font-semibold mb-2 block">
            Decomposed Execution Plan ({payload.steps.length} Steps):
          </span>
          <ol className="list-decimal list-inside space-y-1.5 text-xs text-slate-300">
            {payload.steps.map((step: string, idx: number) => (
              <li key={idx} className="pl-1">
                <span className="font-medium text-slate-200">{step}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
};
