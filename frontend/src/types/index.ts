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
  standard_skills: string
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
  required_skills_standard: string
  preferred_skills_standard: string
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

export interface SystemStatus {
  data_generator_running: boolean
  streaming_running: boolean
  batch_running: boolean
  total_resumes: number
  total_jobs: number
  total_matches: number
  last_update: string
}
