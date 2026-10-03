'use client';

import React, { useState } from 'react';
import { apiRequest } from '@/lib/api';
import { ShieldCheck, Trophy, Lock, Play, Download, AlertTriangle, CheckCircle2 } from 'lucide-react';

export default function AdminControlsPage() {
  const [loading, setLoading] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);

  const handleFreezeStage1 = async () => {
    if (!confirm('Are you sure you want to FREEZE Stage 1 and automatically QUALIFY the Top 20 teams?')) return;
    setLoading(true);
    setResultMessage(null);
    try {
      const res = await apiRequest<any>('/api/admin/stage-1/freeze', { method: 'POST' });
      setResultMessage(`Stage 1 Frozen! ${res.qualified_teams_count} teams successfully qualified for Stage 2.`);
    } catch (e: any) {
      setResultMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleOpenStage2 = async () => {
    setLoading(true);
    try {
      await apiRequest<any>('/api/admin/stage-2/open', { method: 'POST' });
      setResultMessage('Stage 2 submission portal is now OPEN for qualified teams.');
    } catch (e: any) {
      setResultMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFreezeFinal = async () => {
    if (!confirm('Are you sure you want to FREEZE Final Results and determine the Top 3 Winners?')) return;
    setLoading(true);
    setResultMessage(null);
    try {
      const res = await apiRequest<any>('/api/admin/final-results/freeze', { method: 'POST' });
      const winners = res.top3_winners?.map((w: any) => `#${w.rank} ${w.team_name} (${w.final_score.toFixed(1)} pts)`).join(', ');
      setResultMessage(`Final Results Locked! Top 3 Winners: ${winners}`);
    } catch (e: any) {
      setResultMessage(`Error: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <ShieldCheck className="w-6 h-6 text-purple-600" />
          <span>Competition Lifecycle & Winner Selection</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Execute immutable stage transitions, qualify the top 20 teams, and crown the top 3 winners.
        </p>
      </div>

      {resultMessage && (
        <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 text-purple-900 text-xs font-semibold flex items-center justify-between">
          <span>{resultMessage}</span>
          <button onClick={() => setResultMessage(null)} className="text-purple-700">Dismiss</button>
        </div>
      )}

      {/* Stage 1 Freeze Section */}
      <div className="p-6 md:p-8 rounded-3xl bg-white border border-purple-100 shadow-sm space-y-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center font-bold text-sm">
            1
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Freeze Stage 1 & Qualify Top 20 Teams</h2>
            <p className="text-xs text-slate-500">Locks Stage 1 leaderboard, marks top 20 teams as qualified, and creates immutable snapshot.</p>
          </div>
        </div>

        <div className="pt-2 flex flex-wrap gap-3">
          <button
            onClick={handleFreezeStage1}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-md shadow-purple-600/20 disabled:opacity-50 flex items-center space-x-1.5"
          >
            <Lock className="w-4 h-4" />
            <span>Freeze Stage 1 & Qualify Top 20</span>
          </button>
          <button
            onClick={handleOpenStage2}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-bold transition-all border border-purple-200 flex items-center space-x-1.5"
          >
            <Play className="w-4 h-4" />
            <span>Open Stage 2 Portal</span>
          </button>
        </div>
      </div>

      {/* Stage 2 & Final Winner Selection */}
      <div className="p-6 md:p-8 rounded-3xl bg-white border border-purple-100 shadow-sm space-y-4">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center font-bold text-sm">
            2
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Freeze Final Results & Select Top 3 Winners</h2>
            <p className="text-xs text-slate-500">Calculates composite scores (60% Stage 1 + 40% Stage 2), locks final rankings, and publishes winners.</p>
          </div>
        </div>

        <div className="pt-2 flex flex-wrap gap-3">
          <button
            onClick={handleFreezeFinal}
            disabled={loading}
            className="px-5 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-white text-xs font-bold transition-all shadow-md shadow-amber-500/20 disabled:opacity-50 flex items-center space-x-1.5"
          >
            <Trophy className="w-4 h-4" />
            <span>Freeze Final Results & Crown Top 3</span>
          </button>
          <a
            href={`${process.env.NEXT_PUBLIC_API_URL || ''}/api/admin/export/results.csv`}
            target="_blank"
            className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-900 text-white text-xs font-bold transition-all flex items-center space-x-1.5"
          >
            <Download className="w-4 h-4" />
            <span>Export Official CSV Results</span>
          </a>
        </div>
      </div>
    </div>
  );
}
