'use client';

import React, { useEffect, useState } from 'react';
import { apiRequest } from '@/lib/api';
import { FileText, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function AdminAuditLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    apiRequest<any[]>('/api/admin/audit-logs')
      .then(setLogs)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-8 max-w-5xl">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center space-x-2">
          <FileText className="w-6 h-6 text-purple-600" />
          <span>Security & Administrative Audit Logs</span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Immutable audit trail capturing administrative freezes, credential resets, and rubric modifications.
        </p>
      </div>

      <div className="p-4 sm:p-6 rounded-3xl bg-white border border-purple-100 shadow-sm overflow-x-auto">
        {logs.length === 0 ? (
          <p className="text-xs text-slate-400 text-center py-6">No administrative actions logged yet.</p>
        ) : (
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-purple-50 text-slate-400 font-semibold uppercase text-[10px]">
                <th className="pb-3 px-2">Timestamp</th>
                <th className="pb-3 px-2">Actor</th>
                <th className="pb-3 px-2">Action</th>
                <th className="pb-3 px-2">Entity</th>
                <th className="pb-3 px-2">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-purple-50">
              {logs.map((l) => (
                <tr key={l.id} className="text-slate-700 hover:bg-purple-50/20">
                  <td className="py-3 px-2 text-slate-400 font-mono text-[11px]">
                    {new Date(l.created_at).toLocaleString()}
                  </td>
                  <td className="py-3 px-2 font-bold text-slate-900">{l.actor_email}</td>
                  <td className="py-3 px-2">
                    <span className="px-2 py-0.5 rounded bg-purple-100 text-purple-800 font-mono font-bold text-[10px]">
                      {l.action}
                    </span>
                  </td>
                  <td className="py-3 px-2 text-slate-500">{l.entity_type}</td>
                  <td className="py-3 px-2 text-slate-500 font-mono text-[11px] truncate max-w-xs">
                    {JSON.stringify(l.details || {})}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
