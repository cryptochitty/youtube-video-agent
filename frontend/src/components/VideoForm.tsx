'use client'

import { useState, useRef } from 'react'
import { Sparkles, ChevronDown, Upload, X, Check, Loader2, FileText, Mic, User } from 'lucide-react'
import { VideoRequest, createJob, uploadContextFile, uploadVoiceSample, uploadPresenterPhoto } from '@/lib/api'

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

type UploadState = { status: 'idle' | 'uploading' | 'done' | 'error'; filename?: string; error?: string }

function UploadField({
  label, hint, accept, icon: Icon, state, onFile, onClear,
}: {
  label: string; hint: string; accept: string
  icon: React.ElementType; state: UploadState
  onFile: (f: File) => void; onClear: () => void
}) {
  const ref = useRef<HTMLInputElement>(null)
  return (
    <div>
      <label className="block text-sm font-medium text-gray-300 mb-1.5 flex items-center gap-1.5">
        <Icon className="w-3.5 h-3.5 text-blue-400" />
        {label} <span className="text-yt-muted text-xs font-normal">(optional)</span>
      </label>
      {state.status === 'done' ? (
        <div className="flex items-center gap-2 bg-green-900/20 border border-green-700/40 rounded-lg px-3 py-2 text-sm">
          <Check className="w-4 h-4 text-green-400 flex-shrink-0" />
          <span className="text-green-300 truncate flex-1">{state.filename}</span>
          <button type="button" onClick={onClear} className="text-gray-500 hover:text-white">
            <X className="w-4 h-4" />
          </button>
        </div>
      ) : state.status === 'uploading' ? (
        <div className="flex items-center gap-2 bg-blue-900/20 border border-blue-700/40 rounded-lg px-3 py-2 text-sm text-blue-300">
          <Loader2 className="w-4 h-4 animate-spin" />
          Uploading…
        </div>
      ) : (
        <button
          type="button"
          onClick={() => ref.current?.click()}
          className={`w-full flex items-center gap-2 px-3 py-2.5 rounded-lg border text-sm transition-all
            ${state.status === 'error'
              ? 'border-red-700/60 text-red-400 bg-red-900/10'
              : 'border-yt-border text-gray-400 hover:border-gray-500 hover:text-white bg-yt-surface'
            }`}
        >
          <Upload className="w-4 h-4 flex-shrink-0" />
          <span>{state.status === 'error' ? state.error : hint}</span>
        </button>
      )}
      <input ref={ref} type="file" accept={accept} className="hidden"
        onChange={e => e.target.files?.[0] && onFile(e.target.files[0])} />
    </div>
  )
}

export default function VideoForm({ onJobCreated }: Props) {
  const [form, setForm] = useState<VideoRequest>({
    topic: '', style: 'educational', duration: '180', language: 'en', extra_instructions: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const [contextState, setContextState] = useState<UploadState>({ status: 'idle' })
  const [voiceState, setVoiceState] = useState<UploadState>({ status: 'idle' })
  const [photoState, setPhotoState] = useState<UploadState>({ status: 'idle' })

  const handleUpload = async (
    file: File,
    uploader: (f: File) => Promise<{ file_id: string; filename: string }>,
    setState: React.Dispatch<React.SetStateAction<UploadState>>,
    field: 'context_file_id' | 'voice_sample_id' | 'presenter_photo_id',
  ) => {
    setState({ status: 'uploading' })
    try {
      const { file_id, filename } = await uploader(file)
      setState({ status: 'done', filename })
      setForm(f => ({ ...f, [field]: file_id }))
    } catch (e: any) {
      setState({ status: 'error', error: e.message || 'Upload failed' })
    }
  }

  const clearUpload = (
    setState: React.Dispatch<React.SetStateAction<UploadState>>,
    field: 'context_file_id' | 'voice_sample_id' | 'presenter_photo_id',
  ) => {
    setState({ status: 'idle' })
    setForm(f => { const n = { ...f }; delete n[field]; return n })
  }

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
          type="text" value={form.topic}
          onChange={e => setForm(f => ({ ...f, topic: e.target.value }))}
          placeholder="e.g. How black holes bend space and time"
          className="w-full bg-yt-surface border border-yt-border rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors"
          required maxLength={500}
        />
        <p className="text-xs text-yt-muted mt-1">{form.topic.length}/500 chars</p>
      </div>

      {/* Style */}
      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Video Style</label>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {STYLES.map(s => (
            <button key={s.value} type="button"
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
            <select value={form.duration}
              onChange={e => setForm(f => ({ ...f, duration: e.target.value as VideoRequest['duration'] }))}
              className="w-full bg-yt-surface border border-yt-border rounded-lg px-4 py-3 text-white appearance-none focus:outline-none focus:border-blue-500 transition-colors"
            >
              {DURATIONS.map(d => <option key={d.value} value={d.value}>{d.label}</option>)}
            </select>
            <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Language</label>
          <div className="relative">
            <select value={form.language}
              onChange={e => setForm(f => ({ ...f, language: e.target.value }))}
              className="w-full bg-yt-surface border border-yt-border rounded-lg px-4 py-3 text-white appearance-none focus:outline-none focus:border-blue-500 transition-colors"
            >
              {LANGUAGES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
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
        <textarea value={form.extra_instructions}
          onChange={e => setForm(f => ({ ...f, extra_instructions: e.target.value }))}
          placeholder="e.g. Target audience: beginners. Include real-world examples."
          rows={3} maxLength={500}
          className="w-full bg-yt-surface border border-yt-border rounded-lg px-4 py-3 text-white placeholder-gray-600 focus:outline-none focus:border-blue-500 transition-colors resize-none"
        />
      </div>

      {/* Enhancements */}
      <div className="border border-yt-border rounded-xl p-4 space-y-3 bg-yt-dark/40">
        <p className="text-xs font-semibold text-yt-muted uppercase tracking-wide mb-3">Optional Enhancements</p>

        <UploadField
          label="Content File" hint="Upload a .pptx or video to base the script on"
          accept=".pptx,.mp4,.mov,.avi,.webm" icon={FileText}
          state={contextState}
          onFile={f => handleUpload(f, uploadContextFile, setContextState, 'context_file_id')}
          onClear={() => clearUpload(setContextState, 'context_file_id')}
        />

        <UploadField
          label="Your Voice Sample" hint="Upload an mp3/wav to narrate in your voice (needs ElevenLabs key)"
          accept=".mp3,.wav,.ogg,.m4a,audio/*" icon={Mic}
          state={voiceState}
          onFile={f => handleUpload(f, uploadVoiceSample, setVoiceState, 'voice_sample_id')}
          onClear={() => clearUpload(setVoiceState, 'voice_sample_id')}
        />

        <UploadField
          label="Presenter Photo" hint="Upload a photo to appear as a presenter overlay"
          accept=".jpg,.jpeg,.png,.webp,image/*" icon={User}
          state={photoState}
          onFile={f => handleUpload(f, uploadPresenterPhoto, setPhotoState, 'presenter_photo_id')}
          onClear={() => clearUpload(setPhotoState, 'presenter_photo_id')}
        />
      </div>

      {error && (
        <div className="bg-red-900/40 border border-red-700 rounded-lg px-4 py-3 text-red-300 text-sm">{error}</div>
      )}

      <button type="submit" disabled={loading || !form.topic.trim()}
        className="w-full flex items-center justify-center gap-2 bg-yt-red hover:bg-red-600 disabled:bg-gray-700 disabled:text-gray-500 text-white font-semibold py-3.5 px-6 rounded-lg transition-all"
      >
        {loading ? (
          <><div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />Starting…</>
        ) : (
          <><Sparkles className="w-5 h-5" />Generate Video</>
        )}
      </button>
    </form>
  )
}
