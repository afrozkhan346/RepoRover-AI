"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"

interface RepoInputBarProps {
  onAnalyze: (url: string, type: "quick" | "deep") => void
  loading: boolean
}

export default function RepoInputBar({ onAnalyze, loading }: RepoInputBarProps) {
  const [repoUrl, setRepoUrl] = useState("")
  const [analysisType, setAnalysisType] = useState<"quick" | "deep">("quick")

  const handleAnalyze = () => {
    if (repoUrl.trim()) {
      onAnalyze(repoUrl, analysisType)
    }
  }

  return (
    <div className="glass p-6 rounded-lg mb-8">
      <div className="flex flex-col sm:flex-row gap-4">
        <input
          type="text"
          placeholder="Enter GitHub repository URL..."
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          disabled={loading}
          className="flex-1 px-4 py-2 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
        />

        <select
          value={analysisType}
          onChange={(e) => setAnalysisType(e.target.value as "quick" | "deep")}
          disabled={loading}
          className="px-4 py-2 bg-white/10 border border-white/20 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50"
        >
          <option value="quick">Quick Analysis</option>
          <option value="deep">Deep Analysis</option>
        </select>

        <Button
          onClick={handleAnalyze}
          disabled={loading || !repoUrl.trim()}
          className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 disabled:opacity-50"
        >
          {loading ? "Analyzing..." : "Analyze"}
        </Button>
      </div>
    </div>
  )
}
