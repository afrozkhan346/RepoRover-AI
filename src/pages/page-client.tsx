import { Link } from "react-router-dom";

export default function HomePageClient() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.14),_transparent_35%),linear-gradient(180deg,_rgba(2,6,23,0.04),_transparent_40%)] px-6 py-16">
      <section className="mx-auto w-full max-w-4xl rounded-[2rem] border border-slate-200/80 bg-white/90 p-8 shadow-2xl backdrop-blur">
        <div className="space-y-5 text-left">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-sky-700">Reponium</p>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">Repository intelligence in one workspace.</h1>
          <p className="max-w-2xl text-base leading-7 text-slate-600">
            Analyze local projects, inspect dependency and call graphs, review explainability traces, and explore the
            AI-assisted summaries that the backend generates from your codebase.
          </p>
          <div className="flex flex-wrap gap-3 pt-2">
            <Link className="rounded-xl bg-sky-600 px-4 py-3 font-semibold text-white shadow-lg shadow-sky-600/20" to="/analyze">
              Open analyzer
            </Link>
            <Link className="rounded-xl border border-slate-300 px-4 py-3 font-semibold text-slate-900 transition hover:border-sky-300 hover:bg-sky-50" to="/dashboard">
              View dashboard
            </Link>
          </div>
        </div>
      </section>
    </main>
  );
}
