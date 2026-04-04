'use client'

import { useState } from 'react'
import { Youtube, Cpu, Mic2, ImageIcon, Video } from 'lucide-react'
import VideoForm from '@/components/VideoForm'
import JobProgress from '@/components/JobProgress'
import VideoResult from '@/components/VideoResult'
import { Job } from '@/lib/api'

type Screen = 'form' | 'progress' | 'result'

export default function Home() {
  const [screen, setScreen] = useState<Screen>('form')
  const [jobId, setJobId] = useState<string | null>(null)
  const [completedJob, setCompletedJob] = useState<Job | null>(null)

  const handleJobCreated = (id: string) => {
    setJobId(id)
    setScreen('progress')
  }

  const handleCompleted = (job: Job) => {
    setCompletedJob(job)
    setScreen('result')
  }

  const handleNewVideo = () => {
    setJobId(null)
    setCompletedJob(null)
    setScreen('form')
  }

  return (
    <main className="min-h-screen bg-yt-dark">
      {/* Header */}
      <header className="border-b border-yt-border bg-yt-surface/50 sticky top-0 z-10 backdrop-blur-sm">
        <div className="max-w-2xl mx-auto px-4 h-14 flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Youtube className="w-6 h-6 text-yt-red" />
            <span className="font-bold text-white">VideoAgent</span>
          </div>
          <span className="text-yt-border">|</span>
          <span className="text-sm text-yt-muted">AI-powered YouTube video generator</span>
          <div className="ml-auto flex items-center gap-1.5 text-xs text-green-400 bg-green-900/20 border border-green-800/40 px-2 py-1 rounded-full">
            <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse" />
            Free & Local
          </div>
        </div>
      </header>

      {/* Main */}
      <div className="max-w-2xl mx-auto px-4 py-8">

        {/* Hero (only on form screen) */}
        {screen === 'form' && (
          <div className="mb-8 text-center">
            <h1 className="text-3xl font-bold text-white mb-3">
              Generate YouTube Videos with AI
            </h1>
            <p className="text-yt-muted mb-6">
              Type a topic → get a ready-to-upload MP4 with narration, visuals, and metadata
            </p>
            <div className="flex items-center justify-center gap-6 text-xs text-yt-muted">
              {[
                { icon: Cpu, label: 'Ollama LLM' },
                { icon: Mic2, label: 'Edge TTS' },
                { icon: ImageIcon, label: 'Free Images' },
                { icon: Video, label: 'MoviePy' },
              ].map(({ icon: Icon, label }) => (
                <div key={label} className="flex items-center gap-1.5">
                  <Icon className="w-3.5 h-3.5 text-blue-400" />
                  <span>{label}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Card */}
        <div className="bg-yt-surface border border-yt-border rounded-2xl p-6 shadow-xl">
          {screen === 'form' && (
            <VideoForm onJobCreated={handleJobCreated} />
          )}

          {screen === 'progress' && jobId && (
            <div>
              <div className="flex items-center gap-2 mb-6">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                <h2 className="font-semibold text-white">Generating your video...</h2>
              </div>
              <JobProgress
                jobId={jobId}
                onCompleted={handleCompleted}
              />
            </div>
          )}

          {screen === 'result' && completedJob && (
            <VideoResult
              job={completedJob}
              onNewVideo={handleNewVideo}
            />
          )}
        </div>

        {/* How it works */}
        {screen === 'form' && (
          <div className="mt-10">
            <h2 className="text-sm font-semibold text-yt-muted uppercase tracking-wide text-center mb-5">
              How It Works
            </h2>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { step: '1', title: 'Write topic', desc: 'Enter your video idea', color: 'text-purple-400 bg-purple-900/20 border-purple-800/40' },
                { step: '2', title: 'AI scripts it', desc: 'Ollama generates full script', color: 'text-blue-400 bg-blue-900/20 border-blue-800/40' },
                { step: '3', title: 'Auto narrate', desc: 'Edge TTS voices the script', color: 'text-green-400 bg-green-900/20 border-green-800/40' },
                { step: '4', title: 'Export MP4', desc: 'Download & upload to YouTube', color: 'text-orange-400 bg-orange-900/20 border-orange-800/40' },
              ].map(({ step, title, desc, color }) => (
                <div key={step} className={`rounded-xl border p-4 text-center ${color}`}>
                  <div className="text-2xl font-bold mb-1">{step}</div>
                  <div className="text-sm font-medium text-white">{title}</div>
                  <div className="text-xs mt-1 opacity-70">{desc}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
