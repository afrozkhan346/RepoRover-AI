"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import TopNav from "@/components/top-nav"
import RepoInputModal from "@/components/repo-input-modal"
import FeatureCard from "@/components/feature-card"
import Footer from "@/components/footer"

export default function Home() {
  const [showModal, setShowModal] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      <TopNav />

      {/* Hero Section */}
      <section className="relative overflow-hidden pt-20 pb-32 px-4 sm:px-6 lg:px-8">
        {/* Gradient background */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"></div>
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-indigo-500/20 rounded-full blur-3xl"></div>
        </div>

        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-5xl sm:text-6xl font-bold mb-6 gradient-text">
            Your AI-Powered GitHub Repository Analyst
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            Understand any repository instantly. Get AI-powered insights, learn best practices, and accelerate your
            development journey.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Button
              size="lg"
              className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white"
              onClick={() => setShowModal(true)}
            >
              Analyze a Repo
            </Button>
            <Button size="lg" variant="outline" onClick={() => (window.location.href = "/api/auth/github")}>
              Login with GitHub
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Powerful Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <FeatureCard
              title="AI Analysis"
              description="Get instant insights about code structure, patterns, and best practices"
              icon="🤖"
            />
            <FeatureCard
              title="Learn by Building"
              description="Step-by-step guides to understand and implement repository patterns"
              icon="📚"
            />
            <FeatureCard
              title="Quick Projects"
              description="Discover learning projects with estimated time and difficulty levels"
              icon="⚡"
            />
            <FeatureCard
              title="Snapshots"
              description="Export and share repository analysis snapshots with your team"
              icon="📸"
            />
          </div>
        </div>
      </section>

      {/* Sponsors Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <p className="text-center text-muted-foreground mb-8">Trusted by developers at</p>
          <div className="flex flex-wrap justify-center items-center gap-8">
            {["GitHub", "Vercel", "OpenAI", "Stripe"].map((sponsor) => (
              <div key={sponsor} className="glass px-6 py-3 rounded-lg hover:bg-white/20 transition-colors">
                <span className="font-semibold text-foreground">{sponsor}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <Footer />

      {/* Modal */}
      {showModal && <RepoInputModal onClose={() => setShowModal(false)} />}
    </div>
  )
}
