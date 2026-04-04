const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export interface VideoRequest {
  topic: string
  style: 'educational' | 'entertainment' | 'motivational' | 'news' | 'tutorial' | 'documentary'
  duration: '60' | '180' | '300'
  language: string
  voice?: string
  extra_instructions?: string
}

export interface JobStep {
  name: string
  status: 'pending' | 'running' | 'done' | 'error'
  message?: string
  progress: number
}

export interface ScriptSection {
  id: number
  heading: string
  narration: string
  visual_description: string
  search_query: string
  duration_seconds: number
}

export interface VideoScript {
  title: string
  description: string
  tags: string[]
  hook: string
  sections: ScriptSection[]
  call_to_action: string
  total_duration_seconds: number
}

export interface Job {
  id: string
  status: string
  topic: string
  style: string
  duration: string
  overall_progress: number
  created_at: number
  steps?: JobStep[]
  script?: VideoScript
  error?: string
  has_video?: boolean
}

export async function createJob(request: VideoRequest): Promise<{ job_id: string }> {
  const res = await fetch(`${API_URL}/api/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || 'Failed to create job')
  }
  return res.json()
}

export async function getJob(jobId: string): Promise<Job> {
  const res = await fetch(`${API_URL}/api/jobs/${jobId}`)
  if (!res.ok) throw new Error('Job not found')
  return res.json()
}

export async function listJobs(): Promise<Job[]> {
  const res = await fetch(`${API_URL}/api/jobs`)
  if (!res.ok) return []
  return res.json()
}

export async function deleteJob(jobId: string): Promise<void> {
  await fetch(`${API_URL}/api/jobs/${jobId}`, { method: 'DELETE' })
}

export function getDownloadUrl(jobId: string): string {
  return `${API_URL}/api/jobs/${jobId}/download`
}

export function getStreamUrl(jobId: string): string {
  return `${API_URL}/outputs/${jobId}.mp4`
}

export async function getVoices(): Promise<{ name: string; gender: string; locale: string }[]> {
  const res = await fetch(`${API_URL}/api/voices`)
  if (!res.ok) return []
  return res.json()
}
