import React, { useState, useEffect } from 'react';
import { submitTask, listRecentTasks } from './services/api';
import { useAgentWebSocket } from './hooks/useAgentWebSocket';
import { TaskForm } from './components/TaskForm';
import { AgentTimeline } from './components/AgentTimeline';
import { FinalResult } from './components/FinalResult';
import { StatusBadge } from './components/StatusBadge';
import { TaskRun } from './types/events';
import {
  Layers,
  Cpu,
  Database,
  Radio,
  History,
  AlertCircle,
  RefreshCw,
} from 'lucide-react';

export const App: React.FC = () => {
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const [currentPrompt, setCurrentPrompt] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState<boolean>(false);
  const [recentTasks, setRecentTasks] = useState<TaskRun[]>([]);
  const [showHistory, setShowHistory] = useState<boolean>(false);

  const {
    events,
    connectionStatus,
    taskStatus,
    finalResult,
    errorMessage,
    clearEvents,
  } = useAgentWebSocket(currentTaskId);

  // Fetch recent tasks on mount
  useEffect(() => {
    loadRecentTasks();
  }, []);

  const loadRecentTasks = async () => {
    try {
      const tasks = await listRecentTasks();
      setRecentTasks(tasks);
    } catch (err) {
      console.warn('Could not load recent tasks:', err);
    }
  };

  const handleTaskSubmit = async (prompt: string) => {
    setIsSubmitting(true);
    clearEvents();
    setCurrentPrompt(prompt);

    try {
      const response = await submitTask(prompt);
      setCurrentTaskId(response.task_id);
      loadRecentTasks();
    } catch (err: any) {
      console.error('Task submission failed:', err);
      alert(`Submission error: ${err.message || err}`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSelectRecentTask = (task: TaskRun) => {
    setCurrentTaskId(task.id);
    setCurrentPrompt(task.prompt);
    setShowHistory(false);
  };

  return (
    <div className="app-layout min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation Bar */}
      <header className="navbar border-b border-slate-800 bg-slate-900/60 backdrop-blur-md sticky top-0 z-50 px-6 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-lg shadow-indigo-500/20">
              <Layers className="w-5 h-5" />
            </div>
            <div>
              <h1 className="text-base font-extrabold tracking-tight text-white flex items-center gap-2">
                Multi-Agent AI Orchestration
                <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-mono">
                  LangGraph + Celery
                </span>
              </h1>
              <p className="text-xs text-slate-400">
                Autonomous collaboration between Planner, Researcher, and Synthesizer
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-4">
            {/* Tech Badges */}
            <div className="hidden lg:flex items-center space-x-2 text-xs font-mono text-slate-400">
              <span className="tech-badge">
                <Cpu className="w-3 h-3 text-sky-400 inline mr-1" />
                FastAPI 8000
              </span>
              <span className="tech-badge">
                <Database className="w-3 h-3 text-emerald-400 inline mr-1" />
                Postgres & Redis
              </span>
            </div>

            {/* WebSocket Connection Indicator */}
            <div className="flex items-center space-x-2 text-xs font-mono px-2.5 py-1 rounded-full bg-slate-800/80 border border-slate-700">
              <Radio
                className={`w-3.5 h-3.5 ${
                  connectionStatus === 'connected'
                    ? 'text-emerald-400 animate-pulse'
                    : connectionStatus === 'connecting'
                    ? 'text-amber-400 animate-spin'
                    : 'text-slate-500'
                }`}
              />
              <span className="capitalize">{connectionStatus}</span>
            </div>

            {/* History Toggle */}
            <button
              onClick={() => setShowHistory(!showHistory)}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors border border-slate-700 relative"
              title="Recent Executions"
            >
              <History className="w-4 h-4" />
              {recentTasks.length > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-indigo-500 text-white text-[10px] flex items-center justify-center font-bold">
                  {recentTasks.length}
                </span>
              )}
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Body */}
      <main className="max-w-7xl mx-auto w-full px-6 py-6 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Input Form & Task Details */}
        <div className="lg:col-span-5 space-y-6">
          <TaskForm onSubmit={handleTaskSubmit} isLoading={isSubmitting} />

          {/* Active Task Info Card */}
          {currentTaskId && (
            <div className="card active-task-meta-card">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <span className="text-xs uppercase font-mono tracking-wider text-slate-400 font-semibold">
                  Active Task Session
                </span>
                <StatusBadge status={taskStatus} />
              </div>
              <div className="mt-3 space-y-2 text-xs">
                <div>
                  <span className="text-slate-500 font-mono">Task ID: </span>
                  <span className="font-mono text-indigo-300 select-all">{currentTaskId}</span>
                </div>
                {currentPrompt && (
                  <div>
                    <span className="text-slate-500">Prompt: </span>
                    <span className="text-slate-300 font-medium">{currentPrompt}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Error Banner */}
          {errorMessage && (
            <div className="error-card p-4 rounded-xl bg-rose-950/30 border border-rose-500/40 flex items-start space-x-3">
              <AlertCircle className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-rose-300">Workflow Error</h4>
                <p className="text-xs text-rose-200 mt-1">{errorMessage}</p>
              </div>
            </div>
          )}

          {/* Synthesized Output Display */}
          {finalResult && (
            <FinalResult content={finalResult} prompt={currentPrompt} />
          )}
        </div>

        {/* Right Column: Live Agent Timeline */}
        <div className="lg:col-span-7">
          <div className="card timeline-card h-full min-h-[500px] flex flex-col">
            <AgentTimeline events={events} taskStatus={taskStatus} />
          </div>
        </div>
      </main>

      {/* History Slide-over Drawer */}
      {showHistory && (
        <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm">
          <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 p-6 flex flex-col h-full shadow-2xl">
            <div className="flex items-center justify-between pb-4 border-b border-slate-800">
              <div className="flex items-center space-x-2">
                <History className="w-5 h-5 text-indigo-400" />
                <h3 className="font-bold text-slate-100">Workflow History</h3>
              </div>
              <div className="flex items-center space-x-2">
                <button
                  onClick={loadRecentTasks}
                  className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-slate-200"
                  title="Refresh"
                >
                  <RefreshCw className="w-4 h-4" />
                </button>
                <button
                  onClick={() => setShowHistory(false)}
                  className="text-xs px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  Close
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto divide-y divide-slate-800/60 mt-3 space-y-1">
              {recentTasks.length === 0 ? (
                <p className="text-xs text-slate-500 py-6 text-center">No tasks recorded yet.</p>
              ) : (
                recentTasks.map((t) => (
                  <div
                    key={t.id}
                    onClick={() => handleSelectRecentTask(t)}
                    className="py-3 px-2 rounded-lg hover:bg-slate-800/50 cursor-pointer transition-colors"
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[11px] font-mono text-indigo-400">
                        {t.id.slice(0, 8)}...
                      </span>
                      <StatusBadge status={t.status} />
                    </div>
                    <p className="text-xs text-slate-200 line-clamp-2">{t.prompt}</p>
                    <span className="text-[10px] text-slate-500 font-mono mt-1 block">
                      {new Date(t.created_at).toLocaleString()}
                    </span>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
