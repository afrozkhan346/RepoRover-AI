"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"

interface RepoInputModalProps {
  onClose: () => void
}

export default function RepoInputModal({ onClose }: RepoInputModalProps) {
  const [repoUrl, setRepoUrl] = useState("")

  const handleAnalyze = () => {
    if (repoUrl.trim()) {
      // Navigate to analyze page with repo URL
      window.location.href = `/analyze?repo=${encodeURIComponent(repoUrl)}`
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass max-w-md w-full p-8 rounded-lg">
        <h2 className="text-2xl font-bold mb-4">Analyze a Repository</h2>
        <p className="text-muted-foreground mb-6">Enter a GitHub repository URL to get started</p>

        <input
          type="text"
          placeholder="https://github.com/user/repo"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
          className="w-full px-4 py-2 bg-white/10 border border-white/20 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-purple-500"
        />

        <div className="flex gap-3">
          <Button
            onClick={handleAnalyze}
            className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
          >
            Analyze
          </Button>
          <Button onClick={onClose} variant="outline" className="flex-1 bg-transparent">
            Cancel
          </Button>
        </div>
      </div>
    </div>
  )
}
