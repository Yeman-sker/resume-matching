export interface Resume {
  resume_id: string
  name: string
  gender: string
  age: number
  education: string
  school: string
  major: string
  years_experience: string
  skills: string
  certifications: string
  work_history: string
  expected_salary: number
  location: string
  contact: string
  education_level: number
  experience_years_num: number
  standard_location: string
  skill_items_raw: string
  certification_items: string
}

export interface Job {
  job_id: string
  job_title: string
  department: string
  location: string
  education_required: string
  experience_required: string
  skills_required: string
  skills_preferred: string
  salary_range: string
  job_description: string
  responsibilities: string
  requirements: string
  education_required_level: number
  experience_required_num: number
  standard_location: string
  required_skill_items_raw: string
  preferred_skill_items_raw: string
  salary_min: number
  salary_max: number
}

export interface Match {
  resume_id: string
  job_id: string
  resume_name: string
  job_title: string
  department: string
  tfidf_score: number
  word2vec_score: number
  total_score: number
  semantic_score: number
  rule_score: number
  skill_score: number
  education_score: number
  experience_score: number
  city_score: number
  salary_score: number
  certificate_score: number
  matched_skills: string
  missing_skills: string
  reason: string
}

export interface MatchDetail {
  resume: Resume
  job: Job
  scores: {
    total_score: number
    semantic_score: number
    tfidf_score: number
    word2vec_score: number
    rule_score: number
    skill_score: number
    education_score: number
    experience_score: number
    city_score: number
    salary_score: number
    certificate_score: number
  }
  matched_skills: string[]
  missing_skills: string[]
  reason: string
}

export interface SystemStatus {
  data_generator_running: boolean
  streaming_running: boolean
  batch_running: boolean
  total_resumes: number
  total_jobs: number
  total_matches: number
  last_update: string
}

export interface Stats {
  total_resumes: number
  total_jobs: number
  total_matches: number
  avg_total_score: number
  max_total_score: number
  score_distribution: {
    semantic_score_avg: number
    skill_score_avg: number
    education_score_avg: number
    experience_score_avg: number
    city_score_avg: number
    salary_score_avg: number
    certificate_score_avg: number
  }
  departments: string[]
}

export interface PaginatedResponse<T> {
  total: number
  page: number
  page_size: number
  items: T[]
}

export interface JobsResponse {
  total: number
  page: number
  page_size: number
  jobs: Job[]
}

export interface ResumesResponse {
  total: number
  page: number
  page_size: number
  resumes: Resume[]
}

export interface JobMatchesResponse {
  job_id: string
  job_title: string
  total_matches: number
  matches: Match[]
}

export interface ResumeRecommendationsResponse {
  resume_id: string
  resume_name: string
  total_matches: number
  matches: Match[]
}

export interface GeneratorStatus {
  running: boolean
  total_resumes: number
  total_jobs: number
  buffer_size: { resumes: number; jobs: number }
  last_flush_time: string
  generation_rate: { resumes_per_minute: number; jobs_per_minute: number }
  recent_resumes?: Resume[]
  recent_jobs?: Job[]
}

export interface GeneratorConfig {
  resume_interval_seconds: number
  job_interval_seconds: number
  flush_interval_seconds: number
}

export interface BatchRunRecord {
  trigger: 'manual' | 'scheduled'
  started_at: string
  finished_at: string
  duration_seconds: number
  result: 'success' | 'failed' | 'skipped'
  error: string
}

export interface BatchStatus {
  running: boolean
  current_run: { trigger: 'manual' | 'scheduled'; started_at: string } | null
  last_run: BatchRunRecord | null
  last_run_log: string
  schedule_paused: boolean
  next_scheduled_run: string | null
}
