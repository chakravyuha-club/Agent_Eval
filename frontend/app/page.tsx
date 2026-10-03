'use client';

import React from 'react';
import Link from 'next/link';
import Navbar from '@/components/Navbar';
import {
  Shield, Trophy, Cpu, Zap, ArrowRight,
  CheckCircle2, Gauge, Lock, Users, Clock, Layers
} from 'lucide-react';

export default function LandingPage() {
  const dimensions = [
    {
      id: 'dim_a',
      title: 'Dimension A — Task Performance',
      desc: 'Measures Task Success Rate (TSR), target classification F1/Accuracy, assertion satisfaction, and regression error bounds.',
      icon: Cpu,
      color: 'from-purple-500 to-indigo-600',
    },
    {
      id: 'dim_b',
      title: 'Dimension B — Agentic Behavior',
      desc: 'Evaluates observable tool selection accuracy, argument schemas, trajectory efficiency, and self-healing recovery loops.',
      icon: Layers,
      color: 'from-indigo-500 to-blue-600',
    },
    {
      id: 'dim_c',
      title: 'Dimension C — Reliability & pass^3',
      desc: 'Calculates pass@1 and rigorous pass^3 consistency (success across all three repeated stochastic runs).',
      icon: CheckCircle2,
      color: 'from-emerald-500 to-teal-600',
    },
    {
      id: 'dim_d',
      title: 'Dimension D — Output Quality',
      desc: 'Deterministic evaluation of schema compliance, negative constraint adherence, groundedness, and hallucination bounds.',
      icon: Shield,
      color: 'from-amber-500 to-orange-600',
    },
    {
      id: 'dim_e',
      title: 'Dimension E — Safety & Constraints',
      desc: 'Adversarial probe resistance against prompt injection, unauthorized action attempts, and private data exfiltration.',
      icon: Lock,
      color: 'from-rose-500 to-red-600',
    },
    {
      id: 'dim_f',
      title: 'Dimension F — Latency & Efficiency',
      desc: 'Measures P50/P95 latency percentiles, payload compute overhead, and strict timeout compliance.',
      icon: Gauge,
      color: 'from-violet-500 to-purple-600',
    },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-[#faf8ff]">
      <Navbar />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-28 gradient-hero-bg border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <div className="inline-flex items-center space-x-2 px-3.5 py-1.5 rounded-full bg-purple-100/80 border border-purple-200 text-purple-800 text-xs font-semibold mb-6 shadow-sm">
            <span className="flex h-2 w-2 rounded-full bg-purple-600 animate-ping" />
            <span>18-Hour AI Agent Building Competition</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-slate-900 max-w-4xl mx-auto leading-[1.15]">
            Build Intelligent Agents.{' '}
            <span className="gradient-purple-text block sm:inline">Prove Their Performance.</span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            The multi-dimensional evaluation platform for AI agents. Automated two-stage scoring across task success, reliability ($pass^3$), tool usage, safety guardrails, and operational latency.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/login"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-purple-600 hover:bg-purple-700 text-white font-semibold text-base shadow-lg shadow-purple-600/30 hover:shadow-purple-600/40 transition-all flex items-center justify-center space-x-2"
            >
              <span>Team Login Portal</span>
              <ArrowRight className="w-5 h-5" />
            </Link>
            <Link
              href="/dashboard/leaderboard"
              className="w-full sm:w-auto px-8 py-4 rounded-xl bg-white hover:bg-purple-50/50 text-slate-800 font-semibold text-base border border-purple-200 shadow-sm transition-all flex items-center justify-center space-x-2"
            >
              <Trophy className="w-5 h-5 text-purple-600" />
              <span>Live Leaderboard</span>
            </Link>
          </div>

          {/* Stats Badges */}
          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-4 max-w-4xl mx-auto">
            <div className="p-4 rounded-2xl glass-panel text-center">
              <p className="text-3xl font-black text-purple-900">50</p>
              <p className="text-xs font-medium text-slate-500 mt-1 uppercase tracking-wider">Registered Teams</p>
            </div>
            <div className="p-4 rounded-2xl glass-panel text-center">
              <p className="text-3xl font-black text-purple-900">18h</p>
              <p className="text-xs font-medium text-slate-500 mt-1 uppercase tracking-wider">Hackathon Duration</p>
            </div>
            <div className="p-4 rounded-2xl glass-panel text-center">
              <p className="text-3xl font-black text-purple-900">Top 20</p>
              <p className="text-xs font-medium text-slate-500 mt-1 uppercase tracking-wider">Stage 1 Qualification</p>
            </div>
            <div className="p-4 rounded-2xl glass-panel text-center">
              <p className="text-3xl font-black text-purple-900">Top 3</p>
              <p className="text-xs font-medium text-slate-500 mt-1 uppercase tracking-wider">Final Winners</p>
            </div>
          </div>
        </div>
      </section>

      {/* Two-Stage Timeline */}
      <section className="py-20 bg-white border-b border-purple-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">Competition Structure & Workflow</h2>
            <p className="mt-3 text-slate-600">A rigorous two-stage evaluation pipeline combining tabular benchmark predictions and live agent probing.</p>
          </div>

          <div className="mt-12 grid md:grid-cols-2 gap-8">
            <div className="p-8 rounded-2xl border border-purple-100 bg-purple-50/40 relative">
              <span className="px-3 py-1 text-xs font-bold uppercase rounded-full bg-purple-600 text-white">Stage 1</span>
              <h3 className="text-xl font-bold text-slate-900 mt-4">Prediction-File Evaluation</h3>
              <p className="text-sm text-slate-600 mt-2">
                Teams download the problem statement and public dataset, build their agent system, and upload CSV/XLSX predictions. The server deterministically scores against hidden test cases.
              </p>
              <div className="mt-6 flex items-center space-x-2 text-xs font-semibold text-purple-700 bg-purple-100/70 p-3 rounded-xl">
                <CheckCircle2 className="w-4 h-4 text-purple-600" />
                <span>Automatic Qualification: Top 20 teams advance to Stage 2.</span>
              </div>
            </div>

            <div className="p-8 rounded-2xl border border-purple-100 bg-indigo-50/40 relative">
              <span className="px-3 py-1 text-xs font-bold uppercase rounded-full bg-indigo-600 text-white">Stage 2</span>
              <h3 className="text-xl font-bold text-slate-900 mt-4">Live Deployed Agent Testing</h3>
              <p className="text-sm text-slate-600 mt-2">
                Qualified teams submit their deployed HTTP application URL. The evaluator safely connects to /health and /predict across hidden multi-run test suites to verify reliability, tool accuracy, and safety.
              </p>
              <div className="mt-6 flex items-center space-x-2 text-xs font-semibold text-indigo-700 bg-indigo-100/70 p-3 rounded-xl">
                <Trophy className="w-4 h-4 text-indigo-600" />
                <span>Final Output: Top 3 Winners crowned from composite scores.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* 6 Dimensions Grid */}
      <section className="py-20 bg-[#faf8ff]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <h2 className="text-3xl font-black text-slate-900 tracking-tight">The 6 Evaluation Dimensions</h2>
            <p className="mt-3 text-slate-600">
              AgentScore evaluates holistic agent intelligence rather than superficial text outputs.
            </p>
          </div>

          <div className="mt-12 grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {dimensions.map((dim) => {
              const Icon = dim.icon;
              return (
                <div key={dim.id} className="p-6 rounded-2xl bg-white border border-purple-100 shadow-sm hover:shadow-md transition-all">
                  <div className={`w-12 h-12 rounded-xl bg-gradient-to-tr ${dim.color} flex items-center justify-center text-white shadow-md mb-4`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-base font-bold text-slate-900">{dim.title}</h3>
                  <p className="text-xs text-slate-600 mt-2 leading-relaxed">{dim.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="mt-auto border-t border-purple-100 bg-white py-8 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p>© 2026 AgentScore — University Technical Club AI Competition. All rights reserved.</p>
          <div className="flex space-x-6 text-slate-400">
            <Link href="/login" className="hover:text-purple-600">Leader Portal</Link>
            <Link href="/dashboard/leaderboard" className="hover:text-purple-600">Rankings</Link>
            <Link href="/dashboard/problem" className="hover:text-purple-600">Documentation</Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
