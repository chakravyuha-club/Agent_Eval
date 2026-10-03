'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { 
  Trophy, CheckCircle2, AlertCircle, RefreshCw, 
  BarChart3, Activity, Download, ArrowLeft,
  ChevronRight, Shield, Zap, Target, Cpu, Clock
} from 'lucide-react';
import ScoreRadarChart from '@/components/ScoreRadarChart';

interface TaskResult {
  task_id: string;
  passed: boolean;
  latency_ms: number;
  safe_error_category?: string;
}

interface EvaluationResult {
  id: string;
  submission_id: string;
  team_id: string;
  team_name?: string;
  stage: number;
  evaluator_version: string;
  rubric_version: string;
  total_score: number;
  task_success_rate: number;
  metrics: {
    accuracy?: number;
    macro_f1?: number;
    tool_accuracy?: number;
    constraint_compliance?: number;
    output_quality?: number;
    efficiency?: number;
    pass_at_1?: number;
    pass_cubed?: number;
    safety_score?: number;
    efficiency_score?: number;
    p50_latency_ms?: number;
    p95_latency_ms?: number;
    mean_latency_ms?: number;
  };
  score_breakdown: Record<string, number>;
  result_status: string;
  created_at: string;
  task_results?: TaskResult[];
  failure_summary?: Record<string, number>;
}

export default function SubmissionResultsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submissionId, setSubmissionId] = useState<string | null>(null);
  const [result, setResult] = useState<EvaluationResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Read submission id from query string if available
    const urlParams = new URLSearchParams(window.location.search);
    const subId = urlParams.get('id');
    
    if (subId) {
      setSubmissionId(subId);
      fetchResults(subId);
    } else {
      // Fetch latest submission
      fetchLatestSubmission();
    }
  }, []);

  const fetchLatestSubmission = async () => {
    const token = localStorage.getItem('token');
    if (!token) {
      router.push('/login');
      return;
    }

    try {
      const res = await fetch('http://localhost:8000/api/submissions/my', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const subs = await res.json();
        if (subs && subs.length > 0) {
          const latest = subs[0];
          setSubmissionId(latest.id);
          fetchResults(latest.id);
        } else {
          setLoading(false);
          setError('No submissions found. Submit your Stage 1 predictions or Stage 2 agent to view evaluation results.');
        }
      } else {
        setLoading(false);
        setError('Failed to load your submissions.');
      }
    } catch (err) {
      setLoading(false);
      setError('Connection error while fetching submissions.');
    }
  };

  const fetchResults = async (subId: string) => {
    setLoading(true);
    setError(null);
    const token = localStorage.getItem('token');

    try {
      const res = await fetch(`http://localhost:8000/api/submissions/${subId}/results`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (res.ok) {
        const data = await res.json();
        setResult(data);
      } else if (res.status === 404) {
        setError('Evaluation results are still queued or evaluating. Please refresh in a few moments.');
      } else {
        const errData = await res.json().catch(() => ({}));
        setError(errData.detail || 'Could not load evaluation score breakdown.');
      }
    } catch (err) {
      setError('Failed to connect to evaluation API server.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <RefreshCw className="w-10 h-10 text-purple-600 animate-spin mb-4" />
        <p className="text-slate-600 font-medium text-lg">Loading Multi-Dimensional Evaluation Results...</p>
        <p className="text-slate-400 text-sm mt-1">Benchmarking metrics across task success, safety, and efficiency</p>
      </div>
    );
  }

  if (error || !result) {
    return (
      <div className="max-w-3xl mx-auto py-12 px-4">
        <div className="bg-white rounded-3xl p-8 border border-slate-200 text-center shadow-sm">
          <AlertCircle className="w-12 h-12 text-amber-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-slate-900 mb-2">Evaluation Results Pending</h2>
          <p className="text-slate-600 mb-6">{error || 'No evaluation score found.'}</p>
          <div className="flex justify-center gap-4">
            <Link 
              href="/dashboard/submissions"
              className="px-6 py-3 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold transition"
            >
              Back to Submissions
            </Link>
            {submissionId && (
              <button
                onClick={() => fetchResults(submissionId)}
                className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold flex items-center gap-2 transition"
              >
                <RefreshCw className="w-4 h-4" /> Refresh Status
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-sm">
        <div>
          <div className="flex items-center gap-3">
            <Link href="/dashboard/submissions" className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-600 transition">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                Evaluation Report — Stage {result.stage}
              </h1>
              <p className="text-slate-500 text-sm">
                Submission ID: <code className="bg-slate-100 px-2 py-0.5 rounded text-purple-700 font-mono text-xs">{result.submission_id}</code>
              </p>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button 
            onClick={() => fetchResults(result.submission_id)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl border border-slate-200 hover:bg-slate-50 text-slate-700 text-sm font-semibold transition"
          >
            <RefreshCw className="w-4 h-4" /> Refresh
          </button>
          <Link
            href="/leaderboard"
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white text-sm font-semibold shadow-md shadow-purple-200 hover:opacity-95 transition"
          >
            <Trophy className="w-4 h-4" /> View Leaderboard
          </Link>
        </div>
      </div>

      {/* Hero Score Highlight */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-1 bg-gradient-to-br from-purple-900 via-indigo-900 to-slate-900 text-white rounded-3xl p-8 flex flex-col justify-between shadow-xl relative overflow-hidden">
          <div className="relative z-10">
            <span className="px-3 py-1 rounded-full bg-purple-500/20 text-purple-300 text-xs font-semibold border border-purple-400/30">
              Composite Official Score
            </span>
            <div className="mt-6 flex items-baseline gap-2">
              <span className="text-6xl font-extrabold tracking-tight bg-gradient-to-r from-white via-purple-100 to-indigo-200 bg-clip-text text-transparent">
                {result.total_score}
              </span>
              <span className="text-slate-400 text-lg">/ 100</span>
            </div>
            <p className="text-purple-200/80 text-sm mt-2">
              Status: <strong className="text-white uppercase">{result.result_status}</strong>
            </p>
          </div>

          <div className="mt-8 pt-6 border-t border-white/10 flex justify-between items-center text-xs text-slate-300 relative z-10">
            <span>Evaluator: {result.evaluator_version}</span>
            <span>Rubric: {result.rubric_version}</span>
          </div>

          {/* Background Glow */}
          <div className="absolute -top-24 -right-24 w-64 h-64 bg-purple-500/20 rounded-full blur-3xl pointer-events-none" />
        </div>

        {/* Primary Benchmark Dimensions */}
        <div className="md:col-span-2 bg-white rounded-3xl p-8 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-purple-600" /> Dimension Performance Summary
            </h3>
            <span className="text-xs font-medium text-slate-500">
              Evaluated on {new Date(result.created_at).toLocaleString()}
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-purple-50/60 border border-purple-100">
              <span className="text-xs font-semibold text-purple-600">Task Success Rate</span>
              <p className="text-2xl font-black text-slate-900 mt-1">
                {result.task_success_rate}%
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-indigo-50/60 border border-indigo-100">
              <span className="text-xs font-semibold text-indigo-600">
                {result.stage === 1 ? 'Classification Acc.' : 'Reliability (Pass³)'}
              </span>
              <p className="text-2xl font-black text-slate-900 mt-1">
                {result.stage === 1 
                  ? `${result.metrics?.accuracy ?? result.task_success_rate}%` 
                  : (result.metrics?.pass_cubed != null ? `${result.metrics.pass_cubed}%` : 'N/A')}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-emerald-50/60 border border-emerald-100">
              <span className="text-xs font-semibold text-emerald-600">Safety & Guardrails</span>
              <p className="text-2xl font-black text-slate-900 mt-1">
                {result.metrics?.safety_score != null ? `${result.metrics.safety_score}%` : '100%'}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-amber-50/60 border border-amber-100">
              <span className="text-xs font-semibold text-amber-600">Tool Accuracy</span>
              <p className="text-2xl font-black text-slate-900 mt-1">
                {result.metrics?.tool_accuracy != null ? `${result.metrics.tool_accuracy}%` : 'N/A'}
              </p>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-4 rounded-2xl bg-white border border-purple-100 shadow-sm">
              <span className="text-xs font-semibold text-slate-400">Safety & Constraints</span>
              <p className="text-xl font-bold text-slate-900 mt-1">
                {result.metrics?.safety_score != null ? `${result.metrics.safety_score}%` : 'N/A'}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-purple-100 shadow-sm">
              <span className="text-xs font-semibold text-slate-400">Tool Selection Accuracy</span>
              <p className="text-xl font-bold text-slate-900 mt-1">
                {result.metrics?.tool_accuracy != null ? `${result.metrics.tool_accuracy}%` : 'N/A'}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-purple-100 shadow-sm">
              <span className="text-xs font-semibold text-slate-400">P95 Latency</span>
              <p className="text-xl font-bold text-slate-900 mt-1">
                {result.metrics?.p95_latency_ms != null ? `${result.metrics.p95_latency_ms} ms` : 'N/A'}
              </p>
            </div>
            <div className="p-4 rounded-2xl bg-white border border-purple-100 shadow-sm">
              <span className="text-xs font-semibold text-slate-400">Instruction Compliance</span>
              <p className="text-xl font-bold text-slate-900 mt-1">
                {result.metrics?.constraint_compliance != null ? `${result.metrics.constraint_compliance}%` : 'N/A'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Radar Chart & Score Weights Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Radar Visualization */}
        <div className="lg:col-span-6 bg-white rounded-3xl p-8 border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
            <Activity className="w-5 h-5 text-purple-600" /> Multi-Dimensional Capability Radar
          </h3>
          <p className="text-slate-500 text-sm mb-6">
            Visual profile across correctness, tool choice, resilience, safety, and latency
          </p>
          <div className="h-80 w-full flex items-center justify-center">
            <ScoreRadarChart metrics={result.metrics} />
          </div>
        </div>

        {/* Detailed Rubric Weights Breakdown */}
        <div className="lg:col-span-6 bg-white rounded-3xl p-8 border border-slate-200 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-900 mb-2 flex items-center gap-2">
              <Target className="w-5 h-5 text-indigo-600" /> Configured Rubric Weight Allocation
            </h3>
            <p className="text-slate-500 text-sm mb-6">
              Official points earned per evaluation dimension
            </p>

            <div className="space-y-4">
              {Object.entries(result.score_breakdown || {}).map(([dim, score]) => {
                const label = dim.replace(/_/g, ' ').replace('weighted', '').trim();
                return (
                  <div key={dim} className="space-y-1.5">
                    <div className="flex justify-between text-sm">
                      <span className="font-semibold text-slate-700 capitalize">{label}</span>
                      <span className="font-mono text-purple-700 font-bold">{score} pts</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                      <div 
                        className="bg-gradient-to-r from-purple-600 to-indigo-600 h-2.5 rounded-full transition-all duration-500" 
                        style={{ width: `${Math.min(100, (score / 40) * 100)}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="mt-6 p-4 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 flex items-start gap-2">
            <Shield className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
            <span>
              All evaluations are executed inside sandboxed evaluators with cryptographic verification of private ground truth.
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
