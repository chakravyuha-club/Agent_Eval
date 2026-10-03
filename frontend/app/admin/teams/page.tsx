'use client';

import React, { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import { Team } from '@/types';
import StatusBadge from '@/components/StatusBadge';
import { Users, Upload, Key, Search, CheckCircle2, AlertCircle } from 'lucide-react';

export default function AdminTeamsPage() {
  const [teams, setTeams] = useState<Team[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [importing, setImporting] = useState(false);
  const [modalMessage, setModalMessage] = useState<string | null>(null);

  const fetchTeams = () => {
    setLoading(true);
    apiRequest<Team[]>('/api/admin/teams')
      .then(setTeams)
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    fetchTeams();
  }, []);

  const handleResetPassword = async (teamId: string, teamCode: string) => {
    const newPass = prompt(`Enter new password for ${teamCode.toUpperCase()}:`, `${teamCode}NewPass2026!`);
    if (!newPass) return;

    try {
      await apiRequest(`/api/admin/teams/${teamId}/reset-credentials?new_password=${encodeURIComponent(newPass)}`, {
        method: 'POST',
      });
      alert(`Password for ${teamCode.toUpperCase()} reset to '${newPass}'!`);
    } catch (e: any) {
      alert(`Error: ${e.message}`);
    }
  };

  const handleCsvImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImporting(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      const token = localStorage.getItem('agentscore_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const res = await fetch(`${apiUrl}/api/admin/teams/import`, {
        method: 'POST',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });

      const data = await res.json();
      setModalMessage(`Imported ${data.imported_count} teams successfully! (Errors: ${data.error_count})`);
      fetchTeams();
    } catch (err: any) {
      setModalMessage(`Import failed: ${err.message}`);
    } finally {
      setImporting(false);
    }
  };

  const filteredTeams = teams.filter((t) =>
    t.team_name.toLowerCase().includes(search.toLowerCase()) ||
    t.team_code.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-8 max-w-6xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
            <Users className="w-6 h-6 text-purple-600" />
            <span>Team Management (50 Registered Teams)</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            View team rosters, qualification statuses, reset passwords, or bulk-import via CSV.
          </p>
        </div>

        <label className="px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-sm flex items-center space-x-2 cursor-pointer">
          <Upload className="w-4 h-4" />
          <span>{importing ? 'Importing CSV...' : 'Bulk Import CSV'}</span>
          <input type="file" accept=".csv" onChange={handleCsvImport} className="hidden" disabled={importing} />
        </label>
      </div>

      {modalMessage && (
        <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 text-purple-900 text-xs flex items-center justify-between">
          <span>{modalMessage}</span>
          <button onClick={() => setModalMessage(null)} className="font-bold text-purple-700">Dismiss</button>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter by team code or team name..."
          className="w-full pl-10 pr-4 py-2.5 bg-white border border-purple-100 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-purple-500 text-slate-900 shadow-sm"
        />
      </div>

      {/* Teams Table */}
      <div className="p-4 sm:p-6 rounded-3xl bg-white border border-purple-100 shadow-sm overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr className="border-b border-purple-50 text-slate-400 font-semibold uppercase text-[10px]">
              <th className="pb-3 px-2">Team Code</th>
              <th className="pb-3 px-2">Team Name</th>
              <th className="pb-3 px-2">Members</th>
              <th className="pb-3 px-2">Stage 1</th>
              <th className="pb-3 px-2">Stage 2</th>
              <th className="pb-3 px-2">Final</th>
              <th className="pb-3 px-2">Status</th>
              <th className="pb-3 px-2 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-purple-50">
            {filteredTeams.map((t) => (
              <tr key={t.id} className="text-slate-700 hover:bg-purple-50/30">
                <td className="py-3 px-2 font-mono font-bold text-purple-900 uppercase">{t.team_code}</td>
                <td className="py-3 px-2 font-bold text-slate-900">{t.team_name}</td>
                <td className="py-3 px-2 text-slate-500">
                  {t.members.map((m) => m.name).join(', ') || '1 Member'}
                </td>
                <td className="py-3 px-2 font-mono font-semibold">{t.stage1_score.toFixed(1)}</td>
                <td className="py-3 px-2 font-mono font-semibold">{t.stage2_score > 0 ? t.stage2_score.toFixed(1) : '-'}</td>
                <td className="py-3 px-2 font-mono font-bold text-purple-900">{t.final_score > 0 ? t.final_score.toFixed(1) : '-'}</td>
                <td className="py-3 px-2">
                  <StatusBadge status={t.qualification_status} />
                </td>
                <td className="py-3 px-2 text-right">
                  <button
                    onClick={() => handleResetPassword(t.id, t.team_code)}
                    className="p-1.5 rounded-lg text-slate-400 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                    title="Reset Password"
                  >
                    <Key className="w-4 h-4" />
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
