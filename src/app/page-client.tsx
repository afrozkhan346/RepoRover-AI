export default function HomePageClient() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.14),_transparent_35%),linear-gradient(180deg,_rgba(2,6,23,0.04),_transparent_40%)] p-6">
      <section className="max-w-2xl rounded-3xl border bg-white/85 p-8 shadow-2xl backdrop-blur">
        <div className="space-y-4 text-left">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-sky-700">Migration notice</p>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">Next.js is no longer the active frontend.</h1>
          <p className="text-base leading-7 text-slate-600">
            The product UI has moved to the Vite app in <span className="font-semibold">frontend/</span>. That is now
            the primary interface for upload, clone, analysis, dashboard, learning paths, and AI tutor flows.
          </p>
          <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900">
            Use <span className="font-semibold">npm run dev</span> from the repo root to start the Vite frontend.
          </div>
          <div className="flex flex-wrap gap-3 pt-2">
            <a className="rounded-xl bg-sky-600 px-4 py-3 font-semibold text-white shadow-lg shadow-sky-600/20" href="/analyze">
              Open legacy Next page
            </a>
          </div>
        </div>
      </section>
    </main>
  );
}
