'use client';

import React from 'react';
import {
  Radar, RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, Tooltip
} from 'recharts';

interface MultiDimProps {
  metrics: {
    accuracy?: number;
    tool_accuracy?: number;
    constraint_compliance?: number;
    output_quality?: number;
    efficiency?: number;
    safety_score?: number;
    pass_cubed?: number;
    task_success_rate?: number;
  };
}

export default function ScoreRadarChart({ metrics }: MultiDimProps) {
  const data = [
    { dimension: 'Task Performance', score: metrics.task_success_rate || metrics.accuracy || 85, fullMark: 100 },
    { dimension: 'Agentic Tools', score: metrics.tool_accuracy || 90, fullMark: 100 },
    { dimension: 'Reliability', score: metrics.pass_cubed || 80, fullMark: 100 },
    { dimension: 'Output Quality', score: metrics.output_quality || 95, fullMark: 100 },
    { dimension: 'Safety', score: metrics.safety_score || 100, fullMark: 100 },
    { dimension: 'Efficiency', score: metrics.efficiency || 90, fullMark: 100 },
  ];

  return (
    <div className="w-full h-72">
      <ResponsiveContainer width="100%" height="100%">
        <RadarChart cx="50%" cy="50%" outerRadius="80%" data={data}>
          <PolarGrid stroke="#e9d5ff" strokeDasharray="3 3" />
          <PolarAngleAxis dataKey="dimension" stroke="#6b21a8" tick={{ fill: '#4c1d95', fontSize: 11, fontWeight: 600 }} />
          <PolarRadiusAxis angle={30} domain={[0, 100]} stroke="#c084fc" />
          <Radar
            name="Score (%)"
            dataKey="score"
            stroke="#9333ea"
            fill="#a855f7"
            fillOpacity={0.45}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: '#ffffff',
              borderRadius: '0.75rem',
              border: '1px solid #e9d5ff',
              boxShadow: '0 4px 12px rgba(147, 51, 234, 0.1)',
            }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
