'use client';

import React, { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import { Sliders, Lock, CheckCircle2, AlertCircle } from 'lucide-react';

export default function AdminRubricsPage() {
  const [rubrics, setRubrics] = useState<any[]>([]);
  const [accuracyWeight, setAccuracyWeight] = useState(40);
  const [toolWeight, setToolWeight] = useState(20);
  const [constraintWeight, setConstraintWeight] = useState(15);
  const [qualityWeight, setQualityWeight] = useState(15);
  const [efficiencyWeight, setEfficiencyWeight] = useState(10);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const totalSum = accuracyWeight + toolWeight + constraintWeight + qualityWeight + efficiencyWeight;

  const fetchRubrics = () => {
    apiRequest<any[]>('/api/admin/rubrics')
      .then(setRubrics)
      .catch(console.error);
  };

  useEffect(() => {
    fetchRubrics();
  }, []);

  const handleSaveRubric = async (e: React.FormEvent) => {
    e.preventDefault();
    if (totalSum !== 100) {
      setMessage('Error: Rubric component weights must sum exactly to 100%.');
      return;
    }

    setSaving(true);
    setMessage(null);

    try {
      const payload = {
        stage: 1,
        version: `v1.${rubrics.length}.0`,
        weight_accuracy: accuracyWeight / 100,
        weight_tool: toolWeight / 100,
        weight_constraint: constraintWeight / 100,
        weight_quality: qualityWeight / 100,
        weight_efficiency: efficiencyWeight / 100,
        weight_stage2_tsr: 0.35,
        weight_stage2_outcome: 0.20,
        weight_stage2_reliability: 0.15,
        weight_stage2_tool: 0.10,
        weight_stage2_safety: 0.10,
        weight_stage2_efficiency: 0.10,
        stage_1_ratio: 0.60,
        stage_2_ratio: 0.40,
      };

      await apiRequest('/api/admin/rubrics', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setMessage('New versioned scoring rubric successfully locked and activated!');
      fetchRubrics();
    } catch (err: any) {
      setMessage(`Save failed: ${err.message}`);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <Sliders className="w-6 h-6 text-purple-600" />
          <span>Configurable Scoring Rubrics</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Adjust dimension weights with strict normalization to 100% and version locking.
        </p>
      </div>

      {message && (
        <div className="p-4 rounded-2xl bg-purple-50 border border-purple-200 text-purple-900 text-xs flex items-center justify-between">
          <span>{message}</span>
          <button onClick={() => setMessage(null)} className="font-bold text-purple-700">Dismiss</button>
        </div>
      )}

      {/* Editor Card */}
      <div className="p-6 md:p-8 rounded-3xl bg-white border border-purple-100 shadow-sm space-y-6">
        <div className="flex items-center justify-between border-b border-purple-50 pb-4">
          <div>
            <h2 className="text-sm font-bold text-slate-900">Stage 1 Dimension Weights</h2>
            <p className="text-xs text-slate-500">Configure proportional importance before freezing</p>
          </div>
          <div className="flex items-center space-x-2">
            <span className="text-xs font-semibold text-slate-500">Total Weight:</span>
            <span className={`px-3 py-1 rounded-xl text-xs font-black ${
              totalSum === 100 ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
            }`}>
              {totalSum}% {totalSum === 100 ? '(Valid)' : '(Must equal 100%)'}
            </span>
          </div>
        </div>

        <form onSubmit={handleSaveRubric} className="space-y-5">
          <div className="grid sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Outcome Accuracy / TSR Weight (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={accuracyWeight}
                onChange={(e) => setAccuracyWeight(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 font-bold"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Tool Selection Accuracy (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={toolWeight}
                onChange={(e) => setToolWeight(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 font-bold"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Constraint Compliance (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={constraintWeight}
                onChange={(e) => setConstraintWeight(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 font-bold"
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Output Quality & Groundedness (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={qualityWeight}
                onChange={(e) => setQualityWeight(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 font-bold"
              />
            </div>
            <div className="sm:col-span-2">
              <label className="block text-xs font-bold text-slate-700 mb-1">
                Operational Latency & Efficiency (%)
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={efficiencyWeight}
                onChange={(e) => setEfficiencyWeight(Number(e.target.value))}
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 font-bold"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={saving || totalSum !== 100}
            className="px-6 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-md shadow-purple-600/20 disabled:opacity-50 flex items-center space-x-2"
          >
            <Lock className="w-4 h-4" />
            <span>{saving ? 'Locking Rubric...' : 'Lock & Save Versioned Rubric'}</span>
          </button>
        </form>
      </div>

      {/* History */}
      <div className="p-6 rounded-3xl bg-white border border-purple-100 shadow-sm space-y-4">
        <h3 className="text-xs font-bold uppercase tracking-wider text-slate-700">Active & Historical Rubrics</h3>
        <div className="divide-y divide-purple-50 text-xs">
          {rubrics.map((r) => (
            <div key={r.id} className="py-3 flex items-center justify-between">
              <div>
                <p className="font-bold text-slate-900">Stage {r.stage} ({r.version})</p>
                <p className="text-[11px] text-slate-400 mt-0.5">
                  Accuracy: {(r.rubric_json.weight_accuracy * 100).toFixed(0)}% • Tool: {(r.rubric_json.weight_tool * 100).toFixed(0)}% • Quality: {(r.rubric_json.weight_quality * 100).toFixed(0)}%
                </p>
              </div>
              <span className="px-2.5 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200 text-[10px] font-bold">
                LOCKED
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
