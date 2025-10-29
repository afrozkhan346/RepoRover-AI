"use client"

import { Button } from "@/components/ui/button"

interface CodeModalProps {
  step: number
  onClose: () => void
}

export default function CodeModal({ step, onClose }: CodeModalProps) {
  const mockCode = `// Step ${step} - Example Code
import React from 'react'

export const Component = () => {
  return (
    <div className="p-4">
      <h1>Step ${step} Implementation</h1>
      <p>This is example code for step ${step}</p>
    </div>
  )
}`

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="glass max-w-2xl w-full p-6 rounded-lg max-h-96 overflow-auto">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-bold">Step {step} Code</h2>
          <button onClick={onClose} className="text-2xl">
            ✕
          </button>
        </div>

        <pre className="bg-black/30 p-4 rounded mb-4 overflow-auto text-sm">
          <code>{mockCode}</code>
        </pre>

        <div className="flex gap-3">
          <Button
            onClick={() => {
              navigator.clipboard.writeText(mockCode)
            }}
            className="flex-1 bg-gradient-to-r from-purple-600 to-indigo-600"
          >
            Copy Code
          </Button>
          <Button onClick={onClose} variant="outline" className="flex-1 bg-transparent">
            Close
          </Button>
        </div>
      </div>
    </div>
  )
}
