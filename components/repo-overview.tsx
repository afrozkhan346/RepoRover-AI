"use client"

interface RepoOverviewProps {
  data: any
}

export default function RepoOverview({ data }: RepoOverviewProps) {
  return (
    <div className="glass p-6 rounded-lg">
      <h3 className="font-bold text-lg mb-4">Repository Overview</h3>

      <div className="mb-6">
        <h4 className="font-semibold mb-2">AI Summary</h4>
        <p className="text-sm text-muted-foreground leading-relaxed">
          {data.summary ||
            "This is a well-structured repository with clear separation of concerns. The codebase follows modern best practices with TypeScript, comprehensive testing, and good documentation. Key strengths include modular architecture and clear naming conventions."}
        </p>
      </div>

      <div>
        <h4 className="font-semibold mb-3">Architecture Highlights</h4>
        <ul className="space-y-2 text-sm">
          {(
            data.architecturePoints || [
              "Modular component structure",
              "TypeScript for type safety",
              "Comprehensive test coverage",
              "Clear API design",
            ]
          ).map((point: string, idx: number) => (
            <li key={idx} className="flex items-start gap-2">
              <span className="text-purple-400 mt-1">✓</span>
              <span>{point}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
