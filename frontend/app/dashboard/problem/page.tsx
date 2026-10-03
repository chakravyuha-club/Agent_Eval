'use client';

import React, { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import { FileText, Cpu, CheckCircle2, Shield, Layers, Gauge } from 'lucide-react';

export default function ProblemPage() {
  const [problem, setProblem] = useState<any>(null);

  useEffect(() => {
    apiRequest<any>('/api/competition/problem')
      .then(setProblem)
      .catch(console.error);
  }, []);

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <FileText className="w-6 h-6 text-purple-600" />
          <span>Competition Problem Statement</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Review the official task objectives, constraints, schemas, and scoring criteria.
        </p>
      </div>

      {/* Main Card */}
      <div className="p-6 md:p-8 rounded-3xl bg-white border border-purple-100 shadow-sm space-y-6">
        <div>
          <h2 className="text-lg font-bold text-purple-950">
            {problem?.title || '18-Hour AI Agent Building Competition'}
          </h2>
          <p className="text-sm text-slate-600 mt-2 leading-relaxed">
            {problem?.description || 'Build, evaluate, and deploy autonomous multi-step AI agents.'}
          </p>
        </div>

        <div className="p-4 rounded-2xl bg-purple-50/60 border border-purple-100">
          <h3 className="text-xs font-bold uppercase tracking-wider text-purple-900 mb-1">
            Primary Objective
          </h3>
          <p className="text-xs text-slate-700 leading-relaxed">
            {problem?.objective}
          </p>
        </div>

        {/* Evaluation Dimensions */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 mb-3 uppercase tracking-wider">
            Scored Dimensions
          </h3>
          <div className="grid sm:grid-cols-2 gap-4">
            {problem?.evaluation_dimensions?.map((dim: any) => (
              <div key={dim.dimension} className="p-4 rounded-xl border border-slate-200/80 bg-slate-50/50">
                <span className="text-[11px] font-bold text-purple-700">{dim.dimension}</span>
                <h4 className="text-xs font-bold text-slate-900 mt-0.5">{dim.name}</h4>
                <p className="text-[11px] text-slate-500 mt-1">{dim.metrics}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Stage 2 API Contract */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wider">
            Stage 2 API Specification
          </h3>
          <p className="text-xs text-slate-600 mb-3">
            If qualified for Stage 2, your deployed HTTP service must implement the following endpoints:
          </p>

          <div className="space-y-3 font-mono text-xs">
            <div className="p-3 bg-slate-900 text-slate-100 rounded-xl">
              <span className="text-emerald-400 font-bold">GET</span> /health → &#123; &quot;status&quot;: &quot;ok&quot; &#125;
            </div>
            <div className="p-3 bg-slate-900 text-slate-100 rounded-xl">
              <span className="text-purple-400 font-bold">POST</span> /predict
              <pre className="mt-2 text-[11px] text-slate-300 overflow-x-auto">
{`{
  "task_id": "priv_001",
  "stage": "stage_2",
  "input": { "query": "..." },
  "constraints": { "timeout_seconds": 10 }
}`}
              </pre>
            </div>
          </div>
        </div>

        {/* Rules */}
        <div>
          <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wider">
            Official Rules & Constraints
          </h3>
          <ul className="list-disc pl-5 space-y-1.5 text-xs text-slate-600">
            {problem?.rules?.map((r: string, idx: number) => (
              <li key={idx}>{r}</li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
}
