'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/lib/auth-context';
import { apiRequest } from '@/lib/api';
import { Submission, Competition, Announcement } from '@/types';
import StatusBadge from '@/components/StatusBadge';
import MetricCard from '@/components/MetricCard';
import {
  Trophy, UploadCloud, FileText, Database,
  CheckCircle2, Clock, AlertCircle, ArrowRight, Bell
} from 'lucide-react';

export default function DashboardOverview() {
  const { user } = useAuth();
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [competition, setCompetition] = useState<Competition | null>(null);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [subsData, compData, annData] = await Promise.all([
          apiRequest<Submission[]>('/api/submissions/my').catch(() => []),
          apiRequest<Competition>('/api/competition').catch(() => null),
          apiRequest<Announcement[]>('/api/competition/announcements').catch(() => []),
        ]);
        setSubmissions(subsData);
        setCompetition(compData);
        setAnnouncements(annData);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const latestSub = submissions[0];

  return (
    <div className="space-y-8">
      {/* Header Banner */}
      <div className="p-6 md:p-8 rounded-3xl glass-panel border border-purple-100 bg-gradient-to-r from-purple-900 via-indigo-900 to-purple-950 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-white/10 text-purple-200 text-xs font-semibold mb-3">
            <span>Stage {competition?.current_stage || 1} Portal Active</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-black tracking-tight">
            Welcome, {user?.team_name || 'Competitor'}!
          </h1>
          <p className="text-sm text-purple-200 mt-1 max-w-xl">
            Track your evaluations, test cases, schema compliance, and leaderboard standing in real time.
          </p>

          <div className="mt-6 flex flex-wrap gap-3">
            <Link
              href="/dashboard/submissions"
              className="px-4 py-2.5 rounded-xl bg-purple-500 hover:bg-purple-600 text-white text-xs font-bold transition-all shadow-md flex items-center space-x-1.5"
            >
              <UploadCloud className="w-4 h-4" />
              <span>Submit Solution</span>
            </Link>
            <Link
              href="/dashboard/datasets"
              className="px-4 py-2.5 rounded-xl bg-white/15 hover:bg-white/20 text-white text-xs font-bold transition-all flex items-center space-x-1.5"
            >
              <Database className="w-4 h-4" />
              <span>Download Datasets</span>
            </Link>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <MetricCard
          title="Team Status"
          value={user?.team_code ? user.team_code.toUpperCase() : 'Active'}
          subtitle="Pre-Registered Team"
          icon={CheckCircle2}
        />
        <MetricCard
          title="Current Stage"
          value={`Stage ${competition?.current_stage || 1}`}
          subtitle={competition?.current_stage === 1 ? 'Tabular Predictions' : 'Deployed Agent Prober'}
          icon={Clock}
        />
        <MetricCard
          title="Submissions Made"
          value={submissions.length}
          subtitle={`Latest: ${latestSub ? `v${latestSub.submission_version}` : 'None'}`}
          icon={UploadCloud}
        />
        <MetricCard
          title="Evaluation Status"
          value={latestSub ? latestSub.status.toUpperCase() : 'NOT SUBMITTED'}
          subtitle="Deterministic Evaluator"
          icon={Trophy}
          highlight={latestSub?.status === 'completed'}
        />
      </div>

      {/* Main Grid: Submissions & Announcements */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Recent Submissions */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-black text-slate-900 tracking-tight flex items-center space-x-2">
              <UploadCloud className="w-5 h-5 text-purple-600" />
              <span>Recent Submissions</span>
            </h2>
            <Link href="/dashboard/submissions" className="text-xs font-bold text-purple-600 hover:text-purple-800">
              View All
            </Link>
          </div>

          <div className="p-4 rounded-2xl bg-white border border-purple-100 shadow-sm">
            {submissions.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-10 h-10 text-slate-300 mx-auto mb-2" />
                <p className="text-xs font-semibold text-slate-500">No submissions uploaded yet.</p>
                <Link
                  href="/dashboard/submissions"
                  className="mt-3 inline-block text-xs font-bold text-purple-600 hover:underline"
                >
                  Upload your first Stage 1 file →
                </Link>
              </div>
            ) : (
              <div className="divide-y divide-purple-50">
                {submissions.slice(0, 4).map((sub) => (
                  <div key={sub.id} className="py-3 flex items-center justify-between">
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="text-xs font-bold text-slate-800">
                          Stage {sub.stage} (v{sub.submission_version})
                        </span>
                        <StatusBadge status={sub.status} />
                      </div>
                      <p className="text-[11px] text-slate-400 mt-0.5">
                        {new Date(sub.submitted_at).toLocaleString()}
                      </p>
                    </div>
                    <Link
                      href={`/dashboard/results`}
                      className="px-3 py-1.5 rounded-lg bg-purple-50 text-purple-700 hover:bg-purple-100 text-xs font-bold transition-colors"
                    >
                      View Report
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right: Announcements */}
        <div className="space-y-4">
          <h2 className="text-base font-black text-slate-900 tracking-tight flex items-center space-x-2">
            <Bell className="w-5 h-5 text-purple-600" />
            <span>Announcements</span>
          </h2>

          <div className="space-y-3">
            {announcements.map((ann) => (
              <div key={ann.id} className="p-4 rounded-2xl bg-white border border-purple-100 shadow-sm">
                <h3 className="text-xs font-bold text-slate-900">{ann.title}</h3>
                <p className="text-xs text-slate-600 mt-1 leading-relaxed">{ann.body}</p>
                <p className="text-[10px] text-purple-600 font-semibold mt-2">
                  {new Date(ann.published_at).toLocaleDateString()} • {ann.created_by}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
