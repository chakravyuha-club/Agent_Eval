import React from 'react';

interface StatusBadgeProps {
  status: string;
}

export default function StatusBadge({ status }: StatusBadgeProps) {
  const normalized = status.toLowerCase();

  let styles = 'bg-slate-100 text-slate-700 border-slate-200';

  if (['passed', 'qualified', 'completed', 'success', 'valid'].includes(normalized)) {
    styles = 'bg-emerald-50 text-emerald-700 border-emerald-200';
  } else if (['evaluating', 'running', 'queued'].includes(normalized)) {
    styles = 'bg-amber-50 text-amber-700 border-amber-200 animate-pulse';
  } else if (['failed', 'eliminated', 'rejected', 'error'].includes(normalized)) {
    styles = 'bg-rose-50 text-rose-700 border-rose-200';
  } else if (['pending', 'submitted', 'provisional'].includes(normalized)) {
    styles = 'bg-purple-50 text-purple-700 border-purple-200';
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${styles} capitalize`}>
      {status}
    </span>
  );
}
