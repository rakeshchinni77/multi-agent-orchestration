import React, { useState } from 'react';
import { CloudSun, Search, Calculator, Wrench, CheckCircle, AlertTriangle, ChevronDown, ChevronUp } from 'lucide-react';

interface ToolEventProps {
  tool: string;
  argumentsData?: Record<string, any>;
  resultData?: Record<string, any>;
  error?: string | null;
  timestamp?: string;
}

export const ToolEvent: React.FC<ToolEventProps> = ({
  tool,
  argumentsData,
  resultData,
  error,
  timestamp,
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const getToolIcon = () => {
    switch (tool.toLowerCase()) {
      case 'weather':
        return <CloudSun className="w-4 h-4 text-sky-400" />;
      case 'web_search':
        return <Search className="w-4 h-4 text-emerald-400" />;
      case 'calculator':
        return <Calculator className="w-4 h-4 text-amber-400" />;
      default:
        return <Wrench className="w-4 h-4 text-purple-400" />;
    }
  };

  const isSuccess = !error && resultData !== undefined;

  return (
    <div className={`tool-event-box ${error ? 'tool-event-error' : 'tool-event-success'}`}>
      <div
        className="tool-event-header cursor-pointer select-none"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-2">
          <div className="tool-icon-wrapper">{getToolIcon()}</div>
          <span className="font-semibold text-slate-200 capitalize">
            {tool.replace('_', ' ')} Tool Execution
          </span>
          {isSuccess ? (
            <span className="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 flex items-center gap-1 font-mono">
              <CheckCircle className="w-3 h-3" /> success
            </span>
          ) : (
            <span className="text-xs px-2 py-0.5 rounded-full bg-rose-500/10 text-rose-400 flex items-center gap-1 font-mono">
              <AlertTriangle className="w-3 h-3" /> error handled
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2 text-xs text-slate-400">
          {timestamp && <span>{new Date(timestamp).toLocaleTimeString()}</span>}
          {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </div>
      </div>

      {isExpanded && (
        <div className="tool-event-body">
          {argumentsData && (
            <div className="mb-2">
              <span className="text-xs uppercase font-mono tracking-wider text-slate-400">
                Input Parameters:
              </span>
              <pre className="code-block text-xs mt-1">
                {JSON.stringify(argumentsData, null, 2)}
              </pre>
            </div>
          )}

          {resultData && (
            <div>
              <span className="text-xs uppercase font-mono tracking-wider text-emerald-400">
                Celery Tool Result:
              </span>
              <pre className="code-block code-block-result text-xs mt-1">
                {JSON.stringify(resultData, null, 2)}
              </pre>
            </div>
          )}

          {error && (
            <div className="error-banner">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <div className="text-xs text-rose-200">
                <span className="font-semibold">Graceful Tool Recovery: </span>
                {error}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
