"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"

interface ProjectGridProps {
  projects: any[]
}

export default function ProjectGrid({ projects }: ProjectGridProps) {
  const mockProjects = projects || [
    { id: "1", title: "Build Components", eta: "2h", difficulty: "Beginner" },
    { id: "2", title: "Setup Testing", eta: "3h", difficulty: "Intermediate" },
    { id: "3", title: "Deploy App", eta: "1h", difficulty: "Beginner" },
  ]

  return (
    <div className="glass p-4 rounded-lg">
      <h3 className="font-bold mb-4">Learning Projects</h3>
      <div className="space-y-3">
        {mockProjects.map((project: any) => (
          <div key={project.id} className="border border-white/10 p-3 rounded hover:bg-white/10 transition-colors">
            <h4 className="font-semibold text-sm mb-2">{project.title}</h4>
            <div className="text-xs text-muted-foreground mb-3 space-y-1">
              <p>ETA: {project.eta}</p>
              <p>Level: {project.difficulty}</p>
            </div>
            <Link href={`/project/${project.id}`}>
              <Button size="sm" variant="outline" className="w-full bg-transparent">
                Open
              </Button>
            </Link>
          </div>
        ))}
      </div>
    </div>
  )
}
