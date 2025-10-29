"use client"

import { useState } from "react"

interface FileTreeProps {
  files: any[]
}

export default function FileTree({ files }: FileTreeProps) {
  const [expanded, setExpanded] = useState<Set<string>>(new Set(["root"]))

  const toggleExpand = (path: string) => {
    const newExpanded = new Set(expanded)
    if (newExpanded.has(path)) {
      newExpanded.delete(path)
    } else {
      newExpanded.add(path)
    }
    setExpanded(newExpanded)
  }

  const mockFiles = [
    {
      name: "src",
      type: "folder",
      children: [
        { name: "components", type: "folder" },
        { name: "utils", type: "folder" },
        { name: "index.ts", type: "file" },
      ],
    },
    { name: "package.json", type: "file" },
    { name: "README.md", type: "file" },
  ]

  return (
    <div className="glass p-4 rounded-lg">
      <h3 className="font-bold mb-4">File Structure</h3>
      <div className="space-y-1 text-sm">
        {mockFiles.map((file, idx) => (
          <div key={idx} className="flex items-center gap-2 cursor-pointer hover:text-purple-400">
            {file.type === "folder" ? (
              <>
                <span onClick={() => toggleExpand(file.name)}>{expanded.has(file.name) ? "📂" : "📁"}</span>
                <span>{file.name}</span>
              </>
            ) : (
              <>
                <span>📄</span>
                <span>{file.name}</span>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
