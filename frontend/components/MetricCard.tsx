import React from 'react';
import { LucideIcon } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: string;
  highlight?: boolean;
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  highlight = false,
}: MetricCardProps) {
  return (
    <div
      className={`p-5 rounded-2xl border transition-all ${
        highlight
          ? 'bg-gradient-to-br from-purple-700 via-purple-600 to-indigo-600 text-white shadow-lg shadow-purple-600/20 border-transparent'
          : 'bg-white border-purple-100 shadow-sm hover:border-purple-200'
      }`}
    >
      <div className="flex items-center justify-between">
        <p className={`text-xs font-semibold uppercase tracking-wider ${highlight ? 'text-purple-100' : 'text-slate-500'}`}>
          {title}
        </p>
        <div
          className={`p-2.5 rounded-xl ${
            highlight ? 'bg-white/15 text-white' : 'bg-purple-50 text-purple-600'
          }`}
        >
          <Icon className="w-5 h-5" />
        </div>
      </div>

      <div className="mt-4 flex items-baseline justify-between">
        <h3 className={`text-2xl font-black tracking-tight ${highlight ? 'text-white' : 'text-slate-900'}`}>
          {value}
        </h3>
        {trend && (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-md ${
            highlight ? 'bg-white/20 text-white' : 'bg-emerald-50 text-emerald-700'
          }`}>
            {trend}
          </span>
        )}
      </div>

      {subtitle && (
        <p className={`mt-1.5 text-xs ${highlight ? 'text-purple-200' : 'text-slate-500'}`}>
          {subtitle}
        </p>
      )}
    </div>
  );
}
