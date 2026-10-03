'use client';

import React, { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import StatusBadge from '@/components/StatusBadge';
import { History, Play, RotateCcw, CheckCircle2, AlertCircle } from 'lucide-react';

export default function AdminEvaluationsPage() {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const fetchJobs = () => {
    setLoading(true);
    apiRequest<any[]>('/api/admin/evaluations')
      .then(setJobs)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchJobs();
  }, []);

  const handleStartAll = async () => {
    try {
      const res = await apiRequest<any>('/api/admin/evaluations/start', { method: 'POST' });
      setActionMessage(`Processed ${res.processed_jobs} queued evaluation jobs!`);
      fetchJobs();
    } catch (e: any) {
      setActionMessage(`Error: ${e.message}`);
    }
  };

  const handleRetry = async (jobId: string) => {
    try {
      await apiRequest(`/api/admin/evaluations/${jobId}/retry`, { method: 'POST' });
      setActionMessage(`Job ${jobId.slice(0, 8)} re-queued and executed.`);
      fetchJobs();
    } catch (e: any) {
      setActionMessage(`Error: ${e.message}`);
    }
  };

  return (
    <div className="space-y-8 max-w-6xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
            <History className="w-6 h-6 text-purple-600" />
            <span>Evaluation Queue & Job Runner</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Inspect background worker jobs, retry transient failures, and trigger batch evaluations.
          </p>
        </div>

        <button
          onClick={handleStartAll}
          className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-sm flex items-center space-x-1.5"
        >
          <Play className="w-4 h-4" />
          <span>Process All Queued Jobs</span>
        </button>
      </div>

      {actionMessage && (
        <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 text-purple-900 text-xs flex items-center justify-between">
          <span>{actionMessage}</span>
          <button onClick={() => setActionMessage(null)} className="font-bold text-purple-700">Dismiss</button>
        </div>
      )}

      {/* Jobs Table */}
      <div className="p-4 sm:p-6 rounded-3xl bg-white border border-purple-100 shadow-sm overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-purple-50 text-slate-400 font-semibold uppercase text-[10px]">
              <th className="pb-3 px-2">Job ID</th>
              <th className="pb-3 px-2">Team</th>
              <th className="pb-3 px-2">Stage</th>
              <th className="pb-3 px-2">Status</th>
              <th className="pb-3 px-2">Attempts</th>
              <th className="pb-3 px-2">Queued At</th>
              <th className="pb-3 px-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-purple-50">
            {jobs.map((j) => (
              <tr key={j.id} className="text-slate-700 hover:bg-purple-50/30">
                <td className="py-3 px-2 font-mono text-[11px] text-purple-900">{j.id.slice(0, 8)}...</td>
                <td className="py-3 px-2 font-bold text-slate-900">{j.team_name} ({j.team_code})</td>
                <td className="py-3 px-2 font-semibold">Stage {j.stage}</td>
                <td className="py-3 px-2">
                  <StatusBadge status={j.status} />
                </td>
                <td className="py-3 px-2 font-mono">{j.attempt_count}</td>
                <td className="py-3 px-2 text-slate-400">{new Date(j.queued_at).toLocaleTimeString()}</td>
                <td className="py-3 px-2 text-right">
                  <button
                    onClick={() => handleRetry(j.id)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                    title="Retry Evaluation"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
