'use client'

import { useState } from 'react'
import { Sparkles, ChevronDown } from 'lucide-react'
import { VideoRequest, createJob } from '@/lib/api'

interface Props {
  onJobCreated: (jobId: string) => void
}

const STYLES = [
  { value: 'educational', label: 'Educational', emoji: '📚' },
  { value: 'tutorial', label: 'Tutorial', emoji: '🎯' },
  { value: 'entertainment', label: 'Entertainment', emoji: '🎬' },
  { value: 'motivational', label: 'Motivational', emoji: '🔥' },
  { value: 'documentary', label: 'Documentary', emoji: '🎥' },
  { value: 'news', label: 'News / Explainer', emoji: '📰' },
]

const DURATIONS = [
  { value: '60', label: '~1 minute (Short)' },
  { value: '180', label: '~3 minutes (Medium)' },
  { value: '300', label: '~5 minutes (Long)' },
]

const LANGUAGES = [
  { value: 'en', label: 'English' },
  { value: 'es', label: 'Spanish' },
  { value: 'fr', label: 'French' },
  { value: 'de', label: 'German' },
  { value: 'it', label: 'Italian' },
  { value: 'pt', label: 'Portuguese' },
  { value: 'ja', label: 'Japanese' },
  { value: 'zh', label: 'Chinese' },
  { value: 'ko', label: 'Korean' },
  { value: 'hi', label: 'Hindi' },
  { value: 'ar', label: 'Arabic' },
  { value: 'ru', label: 'Russian' },
]

export default function VideoForm({ onJobCreated }: Props) {
  const [form, setForm] = useState<VideoRequest>({
    topic: '',
    style: 'educational',
    duration: '180',
    language: 'en',
    extra_instructions: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.topic.trim()) return

    setLoading(true)
    setError('')
    try {
      const { job_id } = await createJob(form)
      onJobCreated(job_id)
    } catch (err: any) {
      setError(err.message || 'Failed to start generation')
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {/* Topic */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Video Topic <span className="text-yt-red">*</span>
        </label>
        <input
          type="text"
          value={form.topic}
          onChange={e => setForm(f => ({ ...f, topic: e.target.value }))}
          placeholder="e.g. How black holes bend space and time"
          className="w-full bg-yt-surface border border-yt-border rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
          required
          maxLength={500}
        />
        <p className="text-xs text-yt-muted mt-1">{form.topic.length}/500 chars</p>
      </div>

      {/* Style */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Video Style</label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {STYLES.map(s => (
            <button
              key={s.value}
              type="button"
              onClick={() => setForm(f => ({ ...f, style: s.value as VideoRequest['style'] }))}
              className={`flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm font-medium transition-all ${
                form.style === s.value
                  ? 'bg-blue-600 border-blue-500 text-white'
                  : 'bg-yt-surface border-yt-border text-gray-300 hover:border-gray-500'
              }`}
            >
              <span>{s.emoji}</span> {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Duration + Language */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Duration</label>
          <div className="relative">
            <select
              value={form.duration}
              onChange={e => setForm(f => ({ ...f, duration: e.target.value as VideoRequest['duration'] }))}
              className="w-full bg-yt-surface border border-yt-border rounded-lg px-4 py-3 text-white appearance-none focus:outline-none focus:border-blue-500 transition-colors"
            >
              {DURATIONS.map(d => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Language</label>
          <div className="relative">
            <select
              value={form.language}
              onChange={e => setForm(f => ({ ...f, language: e.target.value }))}
              className="w-full bg-yt-surface border border-yt-border rounded-lg px-4 py-3 text-white appearance-none focus:outline-none focus:border-blue-500 transition-colors"
            >
              {LANGUAGES.map(l => (
                <option key={l.value} value={l.value}>{l.label}</option>
              ))}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
      </div>

      {/* Extra instructions */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">
          Extra Instructions <span className="text-yt-muted text-xs">(optional)</span>
        </label>
        <textarea
          value={form.extra_instructions}
          onChange={e => setForm(f => ({ ...f, extra_instructions: e.target.value }))}
          placeholder="e.g. Target audience: beginners. Include real-world examples. Keep tone casual."
          rows={3}
          maxLength={500}
          className="w-full bg-yt-surface border border-yt-border rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors resize-none"
        />
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      <button
        type="submit"
        disabled={loading || !form.topic.trim()}
        className="w-full flex items-center justify-center gap-2 bg-yt-red hover:bg-red-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold py-3.5 px-6 rounded-lg transition-all"
      >
        {loading ? (
          <>
            <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            Starting...
          </>
        ) : (
          <>
            <Sparkles className="w-5 h-5" />
            Generate Video
          </>
        )}
      </button>
    </form>
  )
}
