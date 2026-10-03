export interface User {
  id: string;
  email: string;
  role: 'admin' | 'team_leader';
  is_active: boolean;
  created_at: string;
  team_id?: string;
  team_code?: string;
  team_name?: string;
}

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  is_leader: boolean;
}

export interface Team {
  id: string;
  team_code: string;
  team_name: string;
  qualification_status: 'pending' | 'qualified' | 'eliminated';
  stage1_score: number;
  stage2_score: number;
  final_score: number;
  stage1_rank?: number;
  final_rank?: number;
  members: TeamMember[];
  created_at: string;
}

export interface Competition {
  id: string;
  name: string;
  description: string;
  status: 'active' | 'frozen_stage1' | 'stage2_open' | 'completed';
  start_time: string;
  stage_1_deadline?: string;
  stage_2_deadline?: string;
  current_stage: number;
}

export interface Dataset {
  id: string;
  dataset_name: string;
  dataset_type: 'training' | 'public_test' | 'schema';
  storage_path: string;
  schema_json?: any;
  version: number;
  created_at: string;
}

export interface Announcement {
  id: string;
  title: string;
  body: string;
  created_by: string;
  published_at: string;
}

export interface Submission {
  id: string;
  team_id: string;
  team_name?: string;
  stage: number;
  submission_type: 'file' | 'url';
  application_url?: string;
  submission_version: number;
  status: 'submitted' | 'evaluating' | 'completed' | 'failed';
  submitted_at: string;
  selected_for_evaluation: boolean;
}

export interface TaskResult {
  task_id: string;
  passed: boolean;
  latency_ms: number;
  safe_error_category?: string;
}

export interface EvaluationResult {
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
    task_success_rate?: number;
    outcome_correctness?: number;
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
}

export interface LeaderboardEntry {
  rank: number;
  team_id: string;
  team_code: string;
  team_name: string;
  stage1_score: number;
  stage2_score?: number;
  final_score?: number;
  qualification_status: string;
  is_provisional: boolean;
}

export interface LeaderboardResponse {
  stage: number;
  is_published: boolean;
  last_updated: string;
  entries: LeaderboardEntry[];
}

export interface AdminStats {
  total_teams: number;
  teams_submitted_stage1: number;
  teams_submitted_stage2: number;
  pending_evaluations: number;
  completed_evaluations: number;
  failed_evaluations: number;
  qualified_teams_count: number;
  competition_stage: number;
  competition_status: string;
}
