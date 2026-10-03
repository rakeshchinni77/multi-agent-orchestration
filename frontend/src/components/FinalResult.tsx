import React, { useState } from 'react';
import { Award, Copy, Check } from 'lucide-react';

interface FinalResultProps {
  content: string;
  prompt?: string;
}

export const FinalResult: React.FC<FinalResultProps> = ({ content, prompt }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="card final-result-card border-emerald-500/30">
      <div className="card-header bg-emerald-950/20 border-b border-emerald-500/20 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
            <Award className="w-5 h-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-emerald-300">Final Synthesized Solution</h2>
            <p className="text-xs text-emerald-400/70">
              Coordinated and verified output drafted by the Synthesizer Agent.
            </p>
          </div>
        </div>

        <button
          onClick={handleCopy}
          className="copy-btn flex items-center space-x-1.5 text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 px-3 py-1.5 rounded-lg transition-colors border border-slate-700"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span>Copied!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy Output</span>
            </>
          )}
        </button>
      </div>

      <div className="card-body p-5">
        {prompt && (
          <div className="mb-4 pb-3 border-b border-slate-800 text-xs text-slate-400">
            <span className="font-semibold text-slate-300">Target Objective: </span>
            <span className="italic">{prompt}</span>
          </div>
        )}
        <div className="markdown-prose whitespace-pre-wrap text-sm text-slate-200 leading-relaxed font-sans">
          {content}
        </div>
      </div>
    </div>
  );
};
