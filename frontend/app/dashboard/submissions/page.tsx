'use client';

import React, { useState, useEffect } from 'react';
import { apiRequest } from '@/lib/api';
import { Submission, Competition } from '@/types';
import StatusBadge from '@/components/StatusBadge';
import {
  UploadCloud, Globe, FileSpreadsheet, CheckCircle2,
  AlertCircle, Clock, ArrowRight, History
} from 'lucide-react';

export default function SubmissionsPage() {
  const [stageTab, setStageTab] = useState<1 | 2>(1);
  const [submissions, setSubmissions] = useState<Submission[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [notes, setNotes] = useState('');
  const [appUrl, setAppUrl] = useState('');
  const [stage2Notes, setStage2Notes] = useState('');
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  const fetchSubmissions = () => {
    apiRequest<Submission[]>('/api/submissions/my')
      .then(setSubmissions)
      .catch(console.error);
  };

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const handleStage1Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setMessage({ type: 'error', text: 'Please select a CSV or XLSX file to upload.' });
      return;
    }

    setUploading(true);
    setMessage(null);

    const formData = new FormData();
    formData.append('file', file);
    if (notes) formData.append('notes', notes);

    try {
      const token = localStorage.getItem('agentscore_token');
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const res = await fetch(`${apiUrl}/api/submissions/stage-1`, {
        method: 'POST',
        headers: {
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Upload failed');
      }

      const resData = await res.json();
      setMessage({ type: 'success', text: `Stage 1 submission (v${resData.submission_version}) successfully evaluated!` });
      setFile(null);
      setNotes('');
      fetchSubmissions();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleStage2Submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!appUrl) {
      setMessage({ type: 'error', text: 'Please provide a valid deployed application URL.' });
      return;
    }

    setUploading(true);
    setMessage(null);

    try {
      const resData = await apiRequest<Submission>('/api/submissions/stage-2', {
        method: 'POST',
        body: JSON.stringify({ application_url: appUrl, notes: stage2Notes }),
      });
      setMessage({ type: 'success', text: `Stage 2 application URL (v${resData.submission_version}) submitted and evaluated!` });
      setAppUrl('');
      setStage2Notes('');
      fetchSubmissions();
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <UploadCloud className="w-6 h-6 text-purple-600" />
          <span>Submit Solution</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Upload Stage 1 prediction spreadsheets or submit your Stage 2 deployed AI agent endpoint.
        </p>
      </div>

      {message && (
        <div
          className={`p-4 rounded-2xl text-xs font-medium flex items-start space-x-2.5 border ${
            message.type === 'success'
              ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
              : 'bg-rose-50 text-rose-800 border-rose-200'
          }`}
        >
          {message.type === 'success' ? (
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
          ) : (
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          )}
          <span>{message.text}</span>
        </div>
      )}

      {/* Stage Selector Tabs */}
      <div className="flex border-b border-purple-100 space-x-4">
        <button
          onClick={() => setStageTab(1)}
          className={`pb-3 px-1 text-sm font-bold border-b-2 transition-all flex items-center space-x-2 ${
            stageTab === 1
              ? 'border-purple-600 text-purple-600'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          <span>Stage 1: Prediction File (CSV/XLSX)</span>
        </button>
        <button
          onClick={() => setStageTab(2)}
          className={`pb-3 px-1 text-sm font-bold border-b-2 transition-all flex items-center space-x-2 ${
            stageTab === 2
              ? 'border-purple-600 text-purple-600'
              : 'border-transparent text-slate-400 hover:text-slate-600'
          }`}
        >
          <Globe className="w-4 h-4" />
          <span>Stage 2: Deployed Agent API</span>
        </button>
      </div>

      {/* Stage 1 Form */}
      {stageTab === 1 && (
        <div className="p-6 md:p-8 rounded-3xl bg-white border border-purple-100 shadow-sm">
          <form onSubmit={handleStage1Submit} className="space-y-6">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-2">
                Prediction File (.csv or .xlsx)
              </label>
              <div className="border-2 border-dashed border-purple-200 hover:border-purple-400 rounded-2xl p-8 text-center bg-purple-50/30 transition-colors">
                <FileSpreadsheet className="w-10 h-10 text-purple-500 mx-auto mb-2" />
                <input
                  type="file"
                  accept=".csv,.xlsx,.xls"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="block w-full text-xs text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-purple-600 file:text-white hover:file:bg-purple-700 cursor-pointer"
                />
                <p className="text-[11px] text-slate-400 mt-2">
                  Required columns: <code className="text-purple-600 font-bold">task_id</code>, <code className="text-purple-600 font-bold">predicted_label</code>
                </p>
              </div>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Notes or Architecture Description (Optional)
              </label>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="e.g. Fine-tuned classifier with vector retrieval and constraint filter..."
                rows={3}
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-purple-500 text-slate-900"
              />
            </div>

            <button
              type="submit"
              disabled={uploading || !file}
              className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md shadow-purple-600/30 transition-all disabled:opacity-50 flex items-center space-x-2"
            >
              {uploading ? (
                <span>Validating & Evaluating...</span>
              ) : (
                <>
                  <span>Upload & Run Evaluation</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* Stage 2 Form */}
      {stageTab === 2 && (
        <div className="p-6 md:p-8 rounded-3xl bg-white border border-purple-100 shadow-sm">
          <form onSubmit={handleStage2Submit} className="space-y-6">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Deployed Application Base URL
              </label>
              <div className="relative">
                <Globe className="w-4 h-4 absolute left-3.5 top-3 text-slate-400" />
                <input
                  type="url"
                  required
                  value={appUrl}
                  onChange={(e) => setAppUrl(e.target.value)}
                  placeholder="https://agent.team01.cloud (or http://127.0.0.1:8080 in local dev)"
                  className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-purple-500 text-slate-900"
                />
              </div>
              <p className="text-[11px] text-slate-400 mt-1">
                Must implement <code className="text-purple-600">GET /health</code> and <code className="text-purple-600">POST /predict</code>.
              </p>
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1.5">
                Deployment Version / Notes (Optional)
              </label>
              <input
                type="text"
                value={stage2Notes}
                onChange={(e) => setStage2Notes(e.target.value)}
                placeholder="e.g. v2.1-production-agent"
                className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-purple-500 text-slate-900"
              />
            </div>

            <button
              type="submit"
              disabled={uploading || !appUrl}
              className="px-6 py-3 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold shadow-md shadow-purple-600/30 transition-all disabled:opacity-50 flex items-center space-x-2"
            >
              {uploading ? (
                <span>Probing & Testing Endpoints...</span>
              ) : (
                <>
                  <span>Submit Application & Test</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>
        </div>
      )}

      {/* Submission History */}
      <div className="space-y-4">
        <h2 className="text-base font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <History className="w-5 h-5 text-purple-600" />
          <span>Submission History</span>
        </h2>

        <div className="p-4 rounded-2xl bg-white border border-purple-100 shadow-sm overflow-x-auto">
          {submissions.length === 0 ? (
            <p className="text-xs text-slate-500 text-center py-6">No previous submissions found.</p>
          ) : (
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-purple-50 text-slate-400 font-semibold uppercase tracking-wider text-[10px]">
                  <th className="pb-3">Version</th>
                  <th className="pb-3">Stage</th>
                  <th className="pb-3">Type</th>
                  <th className="pb-3">Status</th>
                  <th className="pb-3">Submitted At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-purple-50">
                {submissions.map((s) => (
                  <tr key={s.id} className="text-slate-700">
                    <td className="py-3 font-bold text-purple-900">v{s.submission_version}</td>
                    <td className="py-3 font-semibold">Stage {s.stage}</td>
                    <td className="py-3 uppercase text-[10px]">{s.submission_type}</td>
                    <td className="py-3">
                      <StatusBadge status={s.status} />
                    </td>
                    <td className="py-3 text-slate-400">{new Date(s.submitted_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
