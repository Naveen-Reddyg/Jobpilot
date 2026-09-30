import Link from 'next/link';
import { ReactNode } from 'react';

export function SiteShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-surface text-text">
      <header className="border-b border-border bg-white/80 backdrop-blur-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">AgenticJobSync</p>
            <h1 className="font-heading text-2xl font-bold text-text">Recommendation Portal</h1>
          </div>
          <nav className="flex items-center gap-3 text-sm font-medium text-muted">
            <Link href="/" className="rounded-full border border-border px-3 py-2 transition hover:border-primary hover:text-primary">
              Review Queue
            </Link>
            <Link href="/setup" className="rounded-full border border-border px-3 py-2 transition hover:border-primary hover:text-primary">
              Profile Setup
            </Link>
            <Link href="/history" className="rounded-full border border-border px-3 py-2 transition hover:border-primary hover:text-primary">
              Run History
            </Link>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 py-8">{children}</main>
    </div>
  );
}
