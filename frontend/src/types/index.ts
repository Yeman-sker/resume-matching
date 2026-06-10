export interface Resume {
  resume_id: string
  name: string
  phone: string
  email: string
  education: string
  years_of_experience: number
  skills: string[]
  city: string
  expected_salary: string
  certificates: string[]
}

export interface Job {
  job_id: string
  company: string
  title: string
  education_required: string
  years_required: number
  skills_required: string[]
  city: string
  salary_range: string
  certificates_required: string[]
}

export interface Match {
  resume_id: string
  job_id: string
  resume_name: string
  job_title: string
  company: string
  total_score: number
  semantic_score: number
  rule_score: number
  skill_score: number
  education_score: number
  experience_score: number
  city_score: number
  salary_score: number
  cert_score: number
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
