import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'YouTube Video Agent',
  description: 'AI-powered YouTube video generator — free, local models',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-yt-dark text-yt-text">
        {children}
      </body>
    </html>
  )
}
