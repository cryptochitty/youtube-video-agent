'use client'

import { useEffect, useState, useCallback } from 'react'
import { CheckCircle, XCircle, Loader2, Clock, FileText, Mic, Image, Film } from 'lucide-react'
import { getJob, Job } from '@/lib/api'

interface Props {
  jobId: string
  onCompleted: (job: Job) => void
}

const STEP_ICONS = [FileText, Mic, Image, Film]
const STEP_COLORS = ['text-purple-400', 'text-blue-400', 'text-green-400', 'text-orange-400']
const POLL_INTERVAL = 1500

export default function JobProgress({ jobId, onCompleted }: Props) {
  const [job, setJob] = useState<Job | null>(null)
  const [error, setError] = useState('')

  const poll = useCallback(async () => {
    try {
      const j = await getJob(jobId)
      setJob(j)
      if (j.status === 'completed') {
        onCompleted(j)
      }
    } catch {
      setError('Failed to fetch job status')
    }
  }, [jobId, onCompleted])

  useEffect(() => {
    poll()
    const id = setInterval(() => {
      setJob(j => {
        if (j?.status === 'completed' || j?.status === 'failed') {
          clearInterval(id)
        }
        return j
      })
      poll()
    }, POLL_INTERVAL)
    return () => clearInterval(id)
  }, [poll])

  if (error) return (
    <div className="text-red-400 text-center py-8">{error}</div>
  )

  if (!job) return (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="w-8 h-8 animate-spin text-blue-400" />
    </div>
  )

  const isFailed = job.status === 'failed'
  const isCompleted = job.status === 'completed'

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="text-center">
        <h3 className="text-lg font-semibold text-white mb-1 truncate">{job.topic}</h3>
        <div className="flex items-center justify-center gap-2 text-sm text-yt-muted">
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            isCompleted ? 'bg-green-900/50 text-green-400' :
            isFailed ? 'bg-red-900/50 text-red-400' :
            'bg-blue-900/50 text-blue-400'
          }`}>
            {job.status.replace(/_/g, ' ')}
          </span>
          <span>{job.overall_progress}%</span>
        </div>
      </div>

      {/* Overall progress bar */}
      <div className="w-full bg-yt-border rounded-full h-2 overflow-hidden">
        <div
          className={`h-2 rounded-full transition-all duration-500 ${
            isFailed ? 'bg-red-500' :
            isCompleted ? 'bg-green-500' :
            'progress-shimmer'
          }`}
          style={{ width: `${job.overall_progress}%` }}
        />
      </div>

      {/* Steps */}
      {job.steps && (
        <div className="space-y-3">
          {job.steps.map((step, i) => {
            const Icon = STEP_ICONS[i]
            const colorClass = STEP_COLORS[i]
            const isDone = step.status === 'done'
            const isRunning = step.status === 'running'
            const isError = step.status === 'error'
            const isPending = step.status === 'pending'

            return (
              <div
                key={i}
                className={`flex items-start gap-3 p-3 rounded-lg border transition-all ${
                  isRunning ? 'bg-blue-900/20 border-blue-700/50 pulsing-border' :
                  isDone ? 'bg-green-900/10 border-green-800/30' :
                  isError ? 'bg-red-900/20 border-red-700/50' :
                  'bg-yt-surface border-yt-border opacity-50'
                }`}
              >
                <div className="flex-shrink-0 mt-0.5">
                  {isDone ? (
                    <CheckCircle className="w-5 h-5 text-green-400" />
                  ) : isError ? (
                    <XCircle className="w-5 h-5 text-red-400" />
                  ) : isRunning ? (
                    <Loader2 className={`w-5 h-5 animate-spin ${colorClass}`} />
                  ) : (
                    <Clock className="w-5 h-5 text-gray-600" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <Icon className={`w-4 h-4 ${isPending ? 'text-gray-600' : colorClass}`} />
                    <span className={`text-sm font-medium ${isPending ? 'text-gray-600' : 'text-white'}`}>
                      {step.name}
                    </span>
                  </div>
                  {step.message && (
                    <p className="text-xs text-yt-muted mt-0.5 truncate">{step.message}</p>
                  )}
                  {isRunning && (
                    <div className="mt-2 w-full bg-yt-border rounded-full h-1">
                      <div
                        className="h-1 rounded-full bg-blue-500 transition-all duration-300"
                        style={{ width: `${step.progress}%` }}
                      />
                    </div>
                  )}
                </div>
                {isDone && (
                  <span className="text-xs text-green-400 flex-shrink-0">Done</span>
                )}
              </div>
            )
          })}
        </div>
      )}

      {/* Error */}
      {isFailed && job.error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-4 text-sm text-red-300">
          <strong className="block mb-1">Generation failed:</strong>
          {job.error}
        </div>
      )}
    </div>
  )
}
