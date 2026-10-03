import React from 'react';
import { AgentEvent, TaskStatus } from '../types/events';
import { AgentCard } from './AgentCard';
import { ToolEvent } from './ToolEvent';
import { Activity, Radio, CheckCircle, AlertCircle } from 'lucide-react';

interface AgentTimelineProps {
  events: AgentEvent[];
  taskStatus: TaskStatus;
}

export const AgentTimeline: React.FC<AgentTimelineProps> = ({ events, taskStatus }) => {
  if (events.length === 0) {
    return (
      <div className="empty-timeline-state">
        <Radio className="w-8 h-8 text-indigo-400 mb-2 animate-pulse" />
        <h3 className="text-sm font-semibold text-slate-300">Ready for Execution</h3>
        <p className="text-xs text-slate-400 max-w-sm mt-1">
          Submit a task above to watch the Planner, Researcher, and Synthesizer stream their actions in real time over WebSockets.
        </p>
      </div>
    );
  }

  // Preprocess events to pair tool invocations with tool results
  const renderedElements: React.ReactNode[] = [];
  const processedIndices = new Set<number>();

  for (let i = 0; i < events.length; i++) {
    if (processedIndices.has(i)) continue;

    const event = events[i];

    // If this is a tool invocation, check if next event is its tool result or error
    if (event.event_type === 'TOOL_INVOCATION') {
      const toolName = event.payload.tool || 'Unknown Tool';
      const args = event.payload.arguments || {};
      let resultData = undefined;
      let error = undefined;
      let resTimestamp = event.timestamp;

      // Look ahead for matching tool result
      for (let j = i + 1; j < events.length; j++) {
        if (
          events[j].event_type === 'TOOL_RESULT' ||
          events[j].event_type === 'TOOL_ERROR'
        ) {
          if (events[j].payload.tool === toolName) {
            resultData = events[j].payload.data;
            error = events[j].payload.error;
            resTimestamp = events[j].timestamp;
            processedIndices.add(j);
            break;
          }
        }
      }

      renderedElements.push(
        <div key={`tool-${i}`} className="timeline-item">
          <div className="timeline-marker marker-tool" />
          <div className="timeline-content">
            <ToolEvent
              tool={toolName}
              argumentsData={args}
              resultData={resultData}
              error={error}
              timestamp={resTimestamp}
            />
          </div>
        </div>
      );
      processedIndices.add(i);
      continue;
    }

    // Skip standalone tool results if already paired
    if (event.event_type === 'TOOL_RESULT' || event.event_type === 'TOOL_ERROR') {
      continue;
    }

    // Render general agent or system lifecycle cards
    renderedElements.push(
      <div key={`event-${i}`} className="timeline-item">
        <div
          className={`timeline-marker ${
            event.agent.toLowerCase() === 'planner'
              ? 'marker-planner'
              : event.agent.toLowerCase() === 'researcher'
              ? 'marker-researcher'
              : event.agent.toLowerCase() === 'synthesizer'
              ? 'marker-synthesizer'
              : 'marker-system'
          }`}
        />
        <div className="timeline-content">
          <AgentCard
            agentName={event.agent}
            eventType={event.event_type}
            payload={event.payload}
            timestamp={event.timestamp}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="timeline-container">
      <div className="timeline-header flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
        <div className="flex items-center space-x-2">
          <Activity className="w-4 h-4 text-indigo-400" />
          <h3 className="text-sm font-bold uppercase tracking-wider text-slate-200">
            Live Multi-Agent Execution Trace
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-400">
          {events.length} events streamed
        </span>
      </div>

      <div className="timeline-track relative pl-6 space-y-6">
        <div className="timeline-line absolute left-2.5 top-2 bottom-2 w-0.5 bg-slate-800" />
        {renderedElements}

        {taskStatus === 'RUNNING' && (
          <div className="timeline-item flex items-center space-x-3 text-xs text-indigo-400 font-mono animate-pulse pt-2">
            <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-ping" />
            <span>Agent node in progress...</span>
          </div>
        )}

        {taskStatus === 'COMPLETED' && (
          <div className="timeline-item flex items-center space-x-2 text-xs text-emerald-400 font-mono pt-2">
            <CheckCircle className="w-4 h-4 text-emerald-400" />
            <span>State machine execution finalized.</span>
          </div>
        )}

        {taskStatus === 'FAILED' && (
          <div className="timeline-item flex items-center space-x-2 text-xs text-rose-400 font-mono pt-2">
            <AlertCircle className="w-4 h-4 text-rose-400" />
            <span>Execution stopped due to failure.</span>
          </div>
        )}
      </div>
    </div>
  );
};
