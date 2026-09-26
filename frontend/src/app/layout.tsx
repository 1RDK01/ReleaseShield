import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'ReleaseShield — Know what breaks before you ship.',
  description: 'AI-powered Change Impact & Release Readiness Engine powered by IBM Bob',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body style={{ background: '#0a0e1a', minHeight: '100vh' }}>{children}</body>
    </html>
  )
}
