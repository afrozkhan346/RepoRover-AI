"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"

export default function TopNav() {
  const [isDark, setIsDark] = useState(false)

  const toggleTheme = () => {
    setIsDark(!isDark)
    if (isDark) {
      document.documentElement.classList.remove("dark")
    } else {
      document.documentElement.classList.add("dark")
    }
  }

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 glass border-b border-white/20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-8 h-8 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-lg"></div>
          <span className="font-bold text-lg">RepoRoverAI</span>
        </Link>

        <div className="flex items-center gap-4">
          <Button size="sm" variant="ghost" onClick={toggleTheme}>
            {isDark ? "☀️" : "🌙"}
          </Button>
          <Button size="sm" variant="outline">
            Sign In
          </Button>
        </div>
      </div>
    </nav>
  )
}
