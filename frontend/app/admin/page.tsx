'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { apiRequest } from '@/lib/api';
import { AdminStats } from '@/types';
import MetricCard from '@/components/MetricCard';
import {
  Users, UploadCloud, CheckCircle2, AlertTriangle,
  Trophy, ShieldCheck, Sliders, History, Download, Play
} from 'lucide-react';

export default function AdminOverviewPage() {
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<AdminStats>('/api/admin/dashboard')
      .then(setStats)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 max-w-6xl">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <ShieldCheck className="w-6 h-6 text-purple-600" />
          <span>Competition Administration Suite</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Monitor evaluations, manage 50 registered teams, configure scoring rubrics, and freeze qualification stages.
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Total Registered Teams"
          value={stats?.total_teams || 50}
          subtitle="Pre-Approved Participants"
          icon={Users}
        />
        <MetricCard
          title="Stage 1 Submissions"
          value={stats?.teams_submitted_stage1 || 0}
          subtitle="Tabular Predictions"
          icon={UploadCloud}
        />
        <MetricCard
          title="Evaluations Completed"
          value={stats?.completed_evaluations || 0}
          subtitle={`${stats?.pending_evaluations || 0} in queue`}
          icon={CheckCircle2}
        />
        <MetricCard
          title="Stage 1 Qualified"
          value={stats?.qualified_teams_count || 0}
          subtitle="Top 20 Slots"
          icon={Trophy}
          highlight={stats?.qualified_teams_count === 20}
        />
      </div>

      {/* Quick Action Control Center */}
      <div className="p-6 md:p-8 rounded-3xl bg-white border border-purple-100 shadow-sm space-y-6">
        <h2 className="text-base font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <Sliders className="w-5 h-5 text-purple-600" />
          <span>Organizer Actions & Workflow Control</span>
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          <Link
            href="/admin/teams"
            className="p-4 rounded-2xl bg-purple-50/70 hover:bg-purple-100/70 border border-purple-100 transition-all flex items-center space-x-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-purple-600 text-white flex items-center justify-center shadow-md">
              <Users className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 group-hover:text-purple-700">Manage 50 Teams</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Bulk CSV import, reset passwords</p>
            </div>
          </Link>

          <Link
            href="/admin/evaluations"
            className="p-4 rounded-2xl bg-purple-50/70 hover:bg-purple-100/70 border border-purple-100 transition-all flex items-center space-x-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-purple-600 text-white flex items-center justify-center shadow-md">
              <History className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 group-hover:text-purple-700">Evaluation Queue</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Run batch jobs, retry failed items</p>
            </div>
          </Link>

          <Link
            href="/admin/rubrics"
            className="p-4 rounded-2xl bg-purple-50/70 hover:bg-purple-100/70 border border-purple-100 transition-all flex items-center space-x-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-purple-600 text-white flex items-center justify-center shadow-md">
              <Sliders className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 group-hover:text-purple-700">Scoring Rubrics</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Configure weights & versions</p>
            </div>
          </Link>

          <Link
            href="/admin/controls"
            className="p-4 rounded-2xl bg-indigo-50/70 hover:bg-indigo-100/70 border border-indigo-100 transition-all flex items-center space-x-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-indigo-600 text-white flex items-center justify-center shadow-md">
              <Trophy className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 group-hover:text-indigo-700">Freeze & Qualify Top 20</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Stage 1 lock & Stage 2 runner</p>
            </div>
          </Link>

          <Link
            href="/admin/controls"
            className="p-4 rounded-2xl bg-emerald-50/70 hover:bg-emerald-100/70 border border-emerald-100 transition-all flex items-center space-x-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-emerald-600 text-white flex items-center justify-center shadow-md">
              <ShieldCheck className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900 group-hover:text-emerald-700">Publish Final Winners</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Top 3 winner selection & export</p>
            </div>
          </Link>

          <a
            href={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/admin/exports/results`}
            target="_blank"
            className="p-4 rounded-2xl bg-slate-50 hover:bg-slate-100 border border-slate-200 transition-all flex items-center space-x-3 group"
          >
            <div className="w-10 h-10 rounded-xl bg-slate-800 text-white flex items-center justify-center shadow-md">
              <Download className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-xs font-bold text-slate-900">Export Results CSV</h3>
              <p className="text-[11px] text-slate-500 mt-0.5">Formula-sanitized official file</p>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
