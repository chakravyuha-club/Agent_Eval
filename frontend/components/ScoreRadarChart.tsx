'use client';

import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip
} from 'recharts';

interface MultiDimProps {
  metrics: {
    accuracy?: number | null;
    tool_accuracy?: number | null;
    constraint_compliance?: number | null;
    output_quality?: number | null;
    efficiency?: number | null;
    safety_score?: number | null;
    pass_cubed?: number | null;
    task_success_rate?: number | null;
  };
}

export default function ScoreRadarChart({ metrics }: MultiDimProps) {
  const data = [
    { dimension: 'Task Performance', score: metrics.task_success_rate ?? metrics.accuracy ?? 0, fullMark: 100 },
    { dimension: 'Agentic Tools', score: metrics.tool_accuracy ?? 0, fullMark: 100 },
    { dimension: 'Reliability', score: metrics.pass_cubed ?? 0, fullMark: 100 },
    { dimension: 'Output Quality', score: metrics.output_quality ?? 0, fullMark: 100 },
    { dimension: 'Safety', score: metrics.safety_score ?? 0, fullMark: 100 },
    { dimension: 'Efficiency', score: metrics.efficiency ?? 0, fullMark: 100 },
  ];

  return (
    <div className="w-full h-full min-h-[280px]">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid stroke="#e2e8f0" strokeDasharray="3 3" />
          <PolarAngleAxis
            dataKey="dimension"
            tick={{ fill: '#64748b', fontSize: 12, fontWeight: 500 }}
          />
          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#cbd5e1" />
          <Radar
            name="Dimension Score"
            dataKey="score"
            stroke="#7c3aed"
            fill="#8b5cf6"
            fillOpacity={0.4}
          />
          <Tooltip 
            formatter={(value: any) => [`${value} / 100`, 'Score']}
            contentStyle={{ backgroundColor: '#1e1b4b', borderRadius: '12px', border: 'none', color: '#fff' }}
            itemStyle={{ color: '#c4b5fd' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
