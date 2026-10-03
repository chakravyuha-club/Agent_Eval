'use client';

import React, { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import { LeaderboardResponse, LeaderboardEntry } from '@/types';
import StatusBadge from '@/components/StatusBadge';
import { Trophy, Medal, Search, RefreshCw, CheckCircle2, Lock } from 'lucide-react';

export default function LeaderboardPage() {
  const [stage, setStage] = useState<number>(1);
  const [data, setData] = useState<LeaderboardResponse | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchLeaderboard = (s: number) => {
    setLoading(true);
    apiRequest<LeaderboardResponse>(`/api/leaderboard/public?stage=${s}`)
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchLeaderboard(stage);
  }, [stage]);

  const filteredEntries = data?.entries.filter((e) =>
    e.team_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.team_code.toLowerCase().includes(searchQuery.toLowerCase())
  ) || [];

  return (
    <div className="space-y-8 max-w-5xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
            <Trophy className="w-6 h-6 text-purple-600" />
            <span>Public Leaderboard</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Official rankings calculated through multi-dimensional deterministic scoring.
          </p>
        </div>

        <button
          onClick={() => fetchLeaderboard(stage)}
          className="px-3.5 py-2 rounded-xl bg-white border border-purple-100 hover:bg-purple-50 text-slate-700 text-xs font-bold transition-colors flex items-center space-x-1.5 shadow-sm"
        >
          <RefreshCw className="w-3.5 h-3.5 text-purple-600" />
          <span>Refresh Rankings</span>
        </button>
      </div>

      {/* Stage Selector & Status Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded-2xl bg-white border border-purple-100 shadow-sm">
        <div className="flex space-x-2">
          <button
            onClick={() => setStage(1)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              stage === 1
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/20'
                : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
            }`}
          >
            Stage 1: Prediction File
          </button>
          <button
            onClick={() => setStage(2)}
            className={`px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              stage === 2
                ? 'bg-purple-600 text-white shadow-md shadow-purple-600/20'
                : 'bg-purple-50 text-purple-700 hover:bg-purple-100'
            }`}
          >
            Stage 2: Final Composite
          </button>
        </div>

        <div className="flex items-center space-x-2 text-xs">
          <span className="font-semibold text-slate-500">Status:</span>
          {data?.is_published ? (
            <span className="px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold">
              Official Snapshot (Locked)
            </span>
          ) : (
            <span className="px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200 font-bold">
              Provisional Real-Time
            </span>
          )}
        </div>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search team name or ID..."
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-purple-100 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-purple-500 text-slate-900 shadow-sm"
        />
      </div>

      {/* Leaderboard Table */}
      <div className="p-4 sm:p-6 rounded-3xl bg-white border border-purple-100 shadow-sm overflow-x-auto">
        {loading ? (
          <div className="py-12 text-center text-xs text-slate-400">Loading rankings...</div>
        ) : filteredEntries.length === 0 ? (
          <div className="py-12 text-center text-xs text-slate-400">No teams found matching search.</div>
        ) : (
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-purple-50 text-slate-400 font-semibold uppercase text-[10px]">
                <th className="pb-3 px-2">Rank</th>
                <th className="pb-3 px-2">Team Name</th>
                <th className="pb-3 px-2">Team ID</th>
                <th className="pb-3 px-2 text-right">Stage 1 Score</th>
                {stage === 2 && <th className="pb-3 px-2 text-right">Stage 2 Score</th>}
                {stage === 2 && <th className="pb-3 px-2 text-right">Final Score</th>}
                <th className="pb-3 px-2 text-center">Qualification</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-50">
              {filteredEntries.map((entry) => {
                const isTop3 = entry.rank <= 3;
                return (
                  <tr
                    key={entry.team_id}
                    className={`text-slate-700 transition-colors ${
                      isTop3 ? 'bg-purple-50/40 font-medium' : 'hover:bg-slate-50/50'
                    }`}
                  >
                    <td className="py-3 px-2">
                      <div className="flex items-center space-x-1.5 font-black">
                        {entry.rank === 1 ? (
                          <span className="w-6 h-6 rounded-full bg-amber-400 text-white flex items-center justify-center text-xs shadow-sm">
                            1
                          </span>
                        ) : entry.rank === 2 ? (
                          <span className="w-6 h-6 rounded-full bg-slate-300 text-slate-800 flex items-center justify-center text-xs shadow-sm">
                            2
                          </span>
                        ) : entry.rank === 3 ? (
                          <span className="w-6 h-6 rounded-full bg-amber-600 text-white flex items-center justify-center text-xs shadow-sm">
                            3
                          </span>
                        ) : (
                          <span className="text-slate-500 pl-1.5">{entry.rank}</span>
                        )}
                      </div>
                    </td>
                    <td className="py-3 px-2 font-bold text-slate-900">{entry.team_name}</td>
                    <td className="py-3 px-2 font-mono text-[11px] text-purple-700 uppercase">{entry.team_code}</td>
                    <td className="py-3 px-2 text-right font-mono font-bold text-slate-800">
                      {entry.stage1_score.toFixed(2)}
                    </td>
                    {stage === 2 && (
                      <td className="py-3 px-2 text-right font-mono font-bold text-slate-800">
                        {entry.stage2_score !== undefined && entry.stage2_score !== null ? entry.stage2_score.toFixed(2) : '-'}
                      </td>
                    )}
                    {stage === 2 && (
                      <td className="py-3 px-2 text-right font-mono font-black text-purple-900">
                        {entry.final_score !== undefined && entry.final_score !== null ? entry.final_score.toFixed(2) : '-'}
                      </td>
                    )}
                    <td className="py-3 px-2 text-center">
                      <StatusBadge status={entry.qualification_status} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
