'use client';

import React, { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import { Dataset } from '@/types';
import { Database, Download, FileSpreadsheet, Lock, AlertCircle } from 'lucide-react';

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<Dataset[]>('/api/competition/datasets')
      .then(setDatasets)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const handleDownload = (id: string, name: string) => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    window.open(`${apiUrl}/api/competition/datasets/${id}/download`, '_blank');
  };

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <Database className="w-6 h-6 text-purple-600" />
          <span>Competition Datasets</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Download authorized training datasets and sample test cases for your agent development.
        </p>
      </div>

      <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs flex items-start space-x-2.5">
        <Lock className="w-4 h-4 text-amber-700 shrink-0 mt-0.5" />
        <div>
          <span className="font-bold">Private Ground-Truth Isolation:</span> Hidden test datasets and ground-truth labels remain strictly isolated in secure server storage and are never exposed in public repositories, APIs, or client bundles.
        </div>
      </div>

      <div className="grid gap-4">
        {datasets.map((dataset) => (
          <div
            key={dataset.id}
            className="p-6 rounded-2xl bg-white border border-purple-100 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4"
          >
            <div className="flex items-center space-x-4">
              <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-100 shrink-0">
                <FileSpreadsheet className="w-6 h-6" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <h3 className="text-sm font-bold text-slate-900">{dataset.dataset_name}</h3>
                  <span className="px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider rounded-md bg-purple-100 text-purple-800">
                    {dataset.dataset_type.replace('_', ' ')}
                  </span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  Format: CSV / Tabular • Version {dataset.version} • Published by Organizers
                </p>
              </div>
            </div>

            <button
              onClick={() => handleDownload(dataset.id, dataset.dataset_name)}
              className="w-full sm:w-auto px-4 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold transition-all shadow-sm flex items-center justify-center space-x-1.5"
            >
              <Download className="w-4 h-4" />
              <span>Download Dataset</span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
