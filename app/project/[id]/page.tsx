"use client"

import { useState, useEffect } from "react"
import { useParams } from "next/navigation"
import TopNav from "@/components/top-nav"
import { Button } from "@/components/ui/button"
import CodeModal from "@/components/code-modal"
import CodeDiff from "@/components/code-diff"
import ChatPanel from "@/components/chat-panel"

export default function ProjectDetailPage() {
  const params = useParams()
  const projectId = params.id as string
  const [project, setProject] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  const [selectedStep, setSelectedStep] = useState<number | null>(null)
  const [completed, setCompleted] = useState<Set<number>>(new Set())

  useEffect(() => {
    // Load mock project data
    const mockProject = {
      id: projectId,
      title: "Build a React Component Library",
      eta: "2-3 hours",
      difficulty: "Intermediate",
      description: "Learn how to structure and build a reusable component library",
      instructions: [
        { step: 1, title: "Setup Project Structure", description: "Create the base folder structure" },
        { step: 2, title: "Create Button Component", description: "Build a flexible button component" },
        { step: 3, title: "Add TypeScript Types", description: "Define proper TypeScript interfaces" },
        { step: 4, title: "Write Tests", description: "Add unit tests for components" },
        { step: 5, title: "Build Storybook", description: "Create interactive component documentation" },
      ],
      verificationCommand: "curl http://localhost:5000/health",
      patch: `--- a/src/Button.tsx
+++ b/src/Button.tsx
@@ -1,5 +1,10 @@
 import React from 'react'
 
+interface ButtonProps {
+  children: React.ReactNode
+  onClick?: () => void
+}
+
-export const Button = ({ children }) => {
+export const Button = ({ children, onClick }: ButtonProps) => {
   return (
-    <button>{children}</button>
+    <button onClick={onClick} className="px-4 py-2 bg-blue-500 text-white rounded">
+      {children}
+    </button>`,
    }

    setProject(mockProject)
    setLoading(false)
  }, [projectId])

  if (loading) {
    return (
      <div className="min-h-screen bg-background">
        <TopNav />
        <div className="pt-20 pb-12 px-4 flex items-center justify-center">
          <div className="text-muted-foreground">Loading project...</div>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-background">
        <TopNav />
        <div className="pt-20 pb-12 px-4 flex items-center justify-center">
          <div className="text-destructive">Project not found</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <TopNav />

      <div className="pt-20 pb-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          {/* Project Header */}
          <div className="mb-8">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-4xl font-bold mb-2">{project.title}</h1>
                <p className="text-muted-foreground">{project.description}</p>
              </div>
              <Button className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700">
                Mark as Done
              </Button>
            </div>

            <div className="flex gap-4 flex-wrap">
              <div className="glass px-4 py-2 rounded-lg">
                <span className="text-sm font-semibold">ETA: {project.eta}</span>
              </div>
              <div className="glass px-4 py-2 rounded-lg">
                <span className="text-sm font-semibold">Difficulty: {project.difficulty}</span>
              </div>
            </div>
          </div>

          {/* Instructions */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Instructions</h2>
            <div className="space-y-3">
              {project.instructions.map((instruction: any) => (
                <div
                  key={instruction.step}
                  className="glass p-4 rounded-lg cursor-pointer hover:bg-white/20 transition-colors"
                  onClick={() => setSelectedStep(instruction.step)}
                >
                  <div className="flex items-start gap-4">
                    <input
                      type="checkbox"
                      checked={completed.has(instruction.step)}
                      onChange={(e) => {
                        const newCompleted = new Set(completed)
                        if (e.target.checked) {
                          newCompleted.add(instruction.step)
                        } else {
                          newCompleted.delete(instruction.step)
                        }
                        setCompleted(newCompleted)
                      }}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <h3 className="font-semibold">{instruction.title}</h3>
                      <p className="text-sm text-muted-foreground">{instruction.description}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Verification Command */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Verification</h2>
            <div className="glass p-4 rounded-lg">
              <div className="flex items-center justify-between">
                <code className="text-sm font-mono">{project.verificationCommand}</code>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    navigator.clipboard.writeText(project.verificationCommand)
                  }}
                >
                  Copy
                </Button>
              </div>
            </div>
          </div>

          {/* Patch Preview */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Patch Preview</h2>
            <CodeDiff diff={project.patch} />
          </div>

          {/* Chat Panel */}
          <div className="mb-8">
            <h2 className="text-2xl font-bold mb-4">Ask Questions</h2>
            <ChatPanel projectId={projectId} />
          </div>
        </div>
      </div>

      {/* Code Modal */}
      {selectedStep !== null && <CodeModal step={selectedStep} onClose={() => setSelectedStep(null)} />}
    </div>
  )
}
