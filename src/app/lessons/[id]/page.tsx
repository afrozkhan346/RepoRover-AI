import Link from "next/link";

export default function LessonPage() {
  const links = [
    {
      href: "/lessons",
      title: "Return to lessons",
      description: "Browse the learning routes that remain in the migrated Next.js app.",
    },
    {
      href: "/dashboard",
      title: "Open dashboard",
      description: "Review summaries, graph output, risks, and priority signals.",
    },
    {
      href: "/analyze",
      title: "Run analysis",
      description: "Refresh the repository intelligence bundle from the analyzer workspace.",
    },
  ];

  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.16),_transparent_32%),linear-gradient(180deg,_#f8fbff_0%,_#eef6ff_100%)] px-6 py-16">
      <section className="mx-auto w-full max-w-4xl rounded-[2rem] border border-slate-200/80 bg-white/90 p-8 shadow-2xl backdrop-blur">
        <div className="space-y-4">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-sky-700">Lesson detail</p>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">Lesson details are handled in Next.js.</h1>
          <p className="max-w-2xl text-base leading-7 text-slate-600">
            This route now acts as a clean placeholder inside the migrated stack and stays within the Next.js frontend.
          </p>
        </div>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="group rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:-translate-y-0.5 hover:border-sky-300 hover:bg-sky-50"
            >
              <div className="space-y-2">
                <h2 className="text-lg font-semibold text-slate-900">{link.title}</h2>
                <p className="text-sm leading-6 text-slate-600">{link.description}</p>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}
