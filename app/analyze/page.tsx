"use client"

import { useState } from "react"
import TopNav from "@/components/top-nav"
import RepoInputBar from "@/components/repo-input-bar"
import DashboardCards from "@/components/dashboard-cards"
import FileTree from "@/components/file-tree"
import RepoOverview from "@/components/repo-overview"
import ProjectGrid from "@/components/project-grid"
import { Button } from "@/components/ui/button"

export default function AnalyzePage() {
  const [repoData, setRepoData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleAnalyze = async (repoUrl: string, analysisType: "quick" | "deep") => {
    setLoading(true)
    setError(null)

    try {
      const endpoint = process.env.NEXT_PUBLIC_ANALYZE_ENDPOINT

      if (endpoint) {
        const response = await fetch(endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ repoUrl, analysisType }),
        })

        if (!response.ok) throw new Error("Analysis failed")
        const data = await response.json()
        setRepoData(data)
      } else {
        // Load mock data
        const mockResponse = await fetch("/mock_data/demo_repo_response.json")
        const data = await mockResponse.json()
        setRepoData(data)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
    } finally {
      setLoading(false)
    }
  }

  const handleExportSnapshot = () => {
    if (!repoData) return

    const dataStr = JSON.stringify(repoData, null, 2)
    const dataBlob = new Blob([dataStr], { type: "application/json" })
    const url = URL.createObjectURL(dataBlob)
    const link = document.createElement("a")
    link.href = url
    link.download = `repo-snapshot-${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="min-h-screen bg-background">
      <TopNav />

      <div className="pt-20 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <RepoInputBar onAnalyze={handleAnalyze} loading={loading} />

          {error && (
            <div className="mt-4 p-4 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive">
              {error}
            </div>
          )}

          {repoData && (
            <>
              <DashboardCards data={repoData} />

              <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-8">
                {/* Left Column - File Tree */}
                <div className="lg:col-span-1">
                  <FileTree files={repoData.fileTree} />
                </div>

                {/* Center Column - Repo Overview */}
                <div className="lg:col-span-2">
                  <RepoOverview data={repoData} />
                </div>

                {/* Right Column - Projects */}
                <div className="lg:col-span-1">
                  <ProjectGrid projects={repoData.projects} />
                </div>
              </div>

              <div className="mt-8 flex justify-center">
                <Button
                  onClick={handleExportSnapshot}
                  className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
                >
                  Export Snapshot
                </Button>
              </div>
            </>
          )}

          {!repoData && !loading && (
            <div className="mt-12 text-center">
              <p className="text-muted-foreground text-lg">Enter a repository URL to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
