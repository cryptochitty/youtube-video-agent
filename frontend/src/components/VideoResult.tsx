'use client'

import { useState } from 'react'
import { Download, Copy, CheckCheck, Tag, FileText, Play, ChevronDown, ChevronUp } from 'lucide-react'
import { Job, getDownloadUrl, getStreamUrl } from '@/lib/api'

interface Props {
  job: Job
  onNewVideo: () => void
}

export default function VideoResult({ job, onNewVideo }: Props) {
  const [copied, setCopied] = useState<string | null>(null)
  const [descOpen, setDescOpen] = useState(false)
  const [scriptOpen, setScriptOpen] = useState(false)

  const script = job.script

  const copyText = async (text: string, key: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(key)
    setTimeout(() => setCopied(null), 2000)
  }

  const CopyBtn = ({ text, id, label }: { text: string; id: string; label?: string }) => (
    <button
      onClick={() => copyText(text, id)}
      className="flex items-center gap-1.5 text-xs text-blue-400 hover:text-blue-300 transition-colors px-2 py-1 rounded border border-blue-800/50 hover:border-blue-600"
    >
      {copied === id ? <CheckCheck className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
      {copied === id ? 'Copied!' : (label || 'Copy')}
    </button>
  )

  return (
    <div className="space-y-6">
      {/* Success header */}
      <div className="flex items-center gap-3 bg-green-900/20 border border-green-700/50 rounded-lg p-4">
        <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center flex-shrink-0">
          <Play className="w-5 h-5 text-white fill-white" />
        </div>
        <div>
          <div className="font-semibold text-green-400">Video Ready!</div>
          <div className="text-sm text-yt-muted">Download it and upload directly to YouTube</div>
        </div>
      </div>

      {/* Video preview */}
      {job.has_video && (
        <div className="rounded-xl overflow-hidden bg-black border border-yt-border">
          <video
            src={getStreamUrl(job.id)}
            controls
            className="w-full aspect-video"
            preload="metadata"
          />
        </div>
      )}

      {/* Download */}
      <a
        href={getDownloadUrl(job.id)}
        download
        className="flex items-center justify-center gap-2 w-full bg-yt-red hover:bg-red-600 text-white font-semibold py-3.5 rounded-lg transition-colors"
      >
        <Download className="w-5 h-5" />
        Download MP4
      </a>

      {script && (
        <div className="space-y-4">
          {/* Title */}
          <div className="bg-yt-surface border border-yt-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium text-yt-muted uppercase tracking-wide">Video Title</span>
              <CopyBtn text={script.title} id="title" />
            </div>
            <p className="text-white font-medium">{script.title}</p>
          </div>

          {/* Tags */}
          <div className="bg-yt-surface border border-yt-border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Tag className="w-4 h-4 text-yt-muted" />
                <span className="text-xs font-medium text-yt-muted uppercase tracking-wide">Tags</span>
              </div>
              <CopyBtn text={script.tags.join(', ')} id="tags" label="Copy all" />
            </div>
            <div className="flex flex-wrap gap-2">
              {script.tags.map((tag, i) => (
                <span
                  key={i}
                  className="text-xs bg-yt-dark border border-yt-border rounded px-2 py-1 text-gray-300"
                >
                  #{tag}
                </span>
              ))}
            </div>
          </div>

          {/* Description */}
          <div className="bg-yt-surface border border-yt-border rounded-lg p-4">
            <button
              onClick={() => setDescOpen(!descOpen)}
              className="flex items-center justify-between w-full"
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-yt-muted" />
                <span className="text-xs font-medium text-yt-muted uppercase tracking-wide">Description</span>
              </div>
              <div className="flex items-center gap-2">
                <CopyBtn text={script.description} id="desc" />
                {descOpen ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
              </div>
            </button>
            {descOpen && (
              <pre className="mt-3 text-sm text-gray-300 whitespace-pre-wrap font-sans">{script.description}</pre>
            )}
          </div>

          {/* Script sections */}
          <div className="bg-yt-surface border border-yt-border rounded-lg p-4">
            <button
              onClick={() => setScriptOpen(!scriptOpen)}
              className="flex items-center justify-between w-full"
            >
              <span className="text-xs font-medium text-yt-muted uppercase tracking-wide">
                Script ({script.sections.length} sections)
              </span>
              {scriptOpen ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
            </button>
            {scriptOpen && (
              <div className="mt-4 space-y-4">
                {script.sections.map((section, i) => (
                  <div key={i} className="border border-yt-border rounded-lg p-3">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div>
                        <span className="text-xs text-blue-400 font-medium">Section {section.id}</span>
                        <h4 className="text-sm font-semibold text-white">{section.heading}</h4>
                      </div>
                      <span className="text-xs text-yt-muted flex-shrink-0">{section.duration_seconds}s</span>
                    </div>
                    <p className="text-sm text-gray-300">{section.narration}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* New video button */}
      <button
        onClick={onNewVideo}
        className="w-full py-3 rounded-lg border border-yt-border text-gray-400 hover:text-white hover:border-gray-500 transition-colors text-sm"
      >
        Generate Another Video
      </button>
    </div>
  )
}
