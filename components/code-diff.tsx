"use client"

import { Button } from "@/components/ui/button"

interface CodeDiffProps {
  diff: string
}

export default function CodeDiff({ diff }: CodeDiffProps) {
  return (
    <div className="glass p-4 rounded-lg">
      <pre className="bg-black/30 p-4 rounded mb-4 overflow-auto text-sm font-mono">
        <code>{diff}</code>
      </pre>

      <Button
        onClick={() => navigator.clipboard.writeText(diff)}
        className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
      >
        Copy Patch
      </Button>
    </div>
  )
}
