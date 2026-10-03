import React, { useState } from 'react';
import { Send, Sparkles, Compass, Search, Calculator, CloudSun } from 'lucide-react';

interface TaskFormProps {
  onSubmit: (prompt: string) => Promise<void>;
  isLoading: boolean;
}

const EXAMPLE_PROMPTS = [
  {
    icon: CloudSun,
    label: 'Tokyo Weather & Packing Guide',
    prompt: 'What is the current weather in Tokyo, and based on that, what should I pack for a 3-day trip?',
  },
  {
    icon: Search,
    label: 'Electric Vehicles Market Brief',
    prompt: 'Search the web for recent advances in electric vehicles in 2026 and summarize key battery breakthroughs.',
  },
  {
    icon: Calculator,
    label: 'London Temp & Metric Conversion',
    prompt: 'What is the current weather in London and calculate the temperature conversion to Fahrenheit using (C * 9/5) + 32?',
  },
];

export const TaskForm: React.FC<TaskFormProps> = ({ onSubmit, isLoading }) => {
  const [prompt, setPrompt] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim() || isLoading) return;
    await onSubmit(prompt.trim());
  };

  const handleSelectExample = (examplePrompt: string) => {
    setPrompt(examplePrompt);
  };

  return (
    <div className="card task-form-card">
      <div className="card-header">
        <div className="flex items-center space-x-2">
          <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-100">Initiate Multi-Agent Workflow</h2>
            <p className="text-xs text-slate-400">
              Submit a goal. The Planner, Researcher, and Synthesizer will collaborate autonomously.
            </p>
          </div>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="task-form">
        <div className="form-group">
          <textarea
            id="prompt-input"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="E.g., What is the weather in Tokyo and calculate conversion from Celsius to Fahrenheit..."
            rows={3}
            disabled={isLoading}
            className="prompt-textarea"
          />
        </div>

        <div className="example-chips-container">
          <span className="text-xs text-slate-400 flex items-center gap-1 font-medium">
            <Compass className="w-3.5 h-3.5 text-indigo-400" />
            Quick Examples:
          </span>
          <div className="example-chips">
            {EXAMPLE_PROMPTS.map((ex, idx) => {
              const Icon = ex.icon;
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSelectExample(ex.prompt)}
                  disabled={isLoading}
                  className="chip-btn"
                >
                  <Icon className="w-3 h-3 text-indigo-400" />
                  <span>{ex.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={!prompt.trim() || isLoading}
            className="submit-btn"
            id="start-workflow-btn"
          >
            {isLoading ? (
              <>
                <span className="spinner-border mr-2" />
                <span>Dispatching Swarm...</span>
              </>
            ) : (
              <>
                <span>Start Workflow</span>
                <Send className="w-4 h-4 ml-2" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
