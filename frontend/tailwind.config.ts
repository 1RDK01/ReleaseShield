import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'rs-bg': '#0a0e1a',
        'rs-surface': '#0f1629',
        'rs-border': '#1e2d45',
        'rs-text': '#e2e8f0',
        'rs-muted': '#64748b',
        'rs-accent': '#3b82f6',
        'rs-success': '#10b981',
        'rs-warning': '#f59e0b',
        'rs-danger': '#ef4444',
        'rs-critical': '#dc2626',
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'Fira Code', 'Menlo', 'monospace'],
      },
    },
  },
  plugins: [],
}
export default config
