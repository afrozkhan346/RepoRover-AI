"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";
import { Navigation } from "@/components/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Code2, Sparkles, Trophy, BarChart3, BookOpen, GitBranch, Zap, Target } from "lucide-react";

export default function Home() {
  const router = useRouter();
  const { data: session } = useSession();

  const handleGetStarted = () => {
    if (session?.user) {
      router.push("/dashboard");
    } else {
      router.push("/register");
    }
  };

  const features = [
    {
      icon: BookOpen,
      title: "Interactive Learning Paths",
      description: "Follow structured courses from JavaScript basics to advanced React, with hands-on lessons and real-world examples."
    },
    {
      icon: Sparkles,
      title: "AI-Powered Explanations",
      description: "Get instant AI-generated explanations for code snippets, making complex concepts easy to understand."
    },
    {
      icon: Trophy,
      title: "Gamified Experience",
      description: "Earn XP, level up, and unlock achievements as you progress through lessons and master new skills."
    },
    {
      icon: GitBranch,
      title: "GitHub Integration",
      description: "Analyze public repositories to understand real-world codebases and learn from open-source projects."
    },
    {
      icon: Target,
      title: "Interactive Quizzes",
      description: "Test your knowledge with coding challenges and multiple-choice questions after each lesson."
    },
    {
      icon: BarChart3,
      title: "Progress Tracking",
      description: "Monitor your learning journey with detailed statistics, streaks, and personalized insights."
    }
  ];

  const learningPaths = [
    {
      icon: "🟨",
      title: "JavaScript Basics",
      description: "Master the fundamentals of JavaScript programming",
      difficulty: "Beginner",
      hours: 12
    },
    {
      icon: "🐍",
      title: "Python Fundamentals",
      description: "Learn Python from scratch with hands-on exercises",
      difficulty: "Beginner",
      hours: 15
    },
    {
      icon: "⚛️",
      title: "React Mastery",
      description: "Build modern web applications with React",
      difficulty: "Intermediate",
      hours: 20
    }
  ];

  return (
    <>
      <Navigation />
      <main className="flex-1">
        {/* Hero Section */}
        <section className="relative py-20 lg:py-32 overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-muted/30 -z-10" />
          <div className="container mx-auto px-4">
            <div className="max-w-4xl mx-auto text-center space-y-8">
              <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-primary/10 text-primary text-sm font-medium">
                <Sparkles className="h-4 w-4" />
                AI-Powered Learning Platform
              </div>
              
              <h1 className="text-4xl md:text-6xl font-bold tracking-tight">
                Master Coding with{" "}
                <span className="bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                  AI Assistance
                </span>
              </h1>
              
              <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
                Learn to code through interactive lessons, AI-powered explanations, and gamified challenges. 
                Track your progress and become a better developer.
              </p>

              <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
                <Button size="lg" className="text-lg px-8" onClick={handleGetStarted}>
                  {session?.user ? "Go to Dashboard" : "Start Learning Free"}
                </Button>
                <Button size="lg" variant="outline" asChild className="text-lg px-8">
                  <Link href="/lessons">Browse Lessons</Link>
                </Button>
              </div>

              <div className="flex items-center justify-center gap-8 text-sm text-muted-foreground pt-8">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-green-500" />
                  <span>20+ Lessons</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-blue-500" />
                  <span>60+ Quizzes</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-purple-500" />
                  <span>10 Achievements</span>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section className="py-20 bg-muted/30">
          <div className="container mx-auto px-4">
            <div className="text-center space-y-4 mb-12">
              <h2 className="text-3xl md:text-4xl font-bold">Why Choose RepoRoverAI?</h2>
              <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                Experience a modern learning platform designed to accelerate your coding journey
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {features.map((feature, index) => (
                <Card key={index} className="border-2 hover:border-primary/50 transition-colors">
                  <CardHeader>
                    <div className="p-3 bg-primary/10 rounded-xl w-fit mb-2">
                      <feature.icon className="h-6 w-6 text-primary" />
                    </div>
                    <CardTitle className="text-xl">{feature.title}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <CardDescription className="text-base">{feature.description}</CardDescription>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        </section>

        {/* Learning Paths Section */}
        <section className="py-20">
          <div className="container mx-auto px-4">
            <div className="text-center space-y-4 mb-12">
              <h2 className="text-3xl md:text-4xl font-bold">Popular Learning Paths</h2>
              <p className="text-muted-foreground text-lg max-w-2xl mx-auto">
                Start your journey with our carefully crafted courses
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto">
              {learningPaths.map((path, index) => (
                <Card key={index} className="border-2 hover:shadow-lg transition-all cursor-pointer group">
                  <CardHeader>
                    <div className="text-5xl mb-4">{path.icon}</div>
                    <CardTitle className="text-2xl group-hover:text-primary transition-colors">
                      {path.title}
                    </CardTitle>
                    <CardDescription className="text-base">{path.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="px-3 py-1 rounded-full bg-primary/10 text-primary font-medium">
                        {path.difficulty}
                      </span>
                      <span className="text-muted-foreground">{path.hours} hours</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="text-center mt-8">
              <Button size="lg" variant="outline" asChild>
                <Link href="/lessons">View All Paths →</Link>
              </Button>
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-20 bg-gradient-to-br from-primary/10 via-primary/5 to-background">
          <div className="container mx-auto px-4">
            <Card className="max-w-3xl mx-auto border-2 border-primary/20">
              <CardHeader className="text-center space-y-4 pb-8">
                <div className="inline-flex items-center justify-center p-4 bg-primary/10 rounded-2xl w-fit mx-auto">
                  <Zap className="h-8 w-8 text-primary" />
                </div>
                <CardTitle className="text-3xl md:text-4xl">Ready to Start Learning?</CardTitle>
                <CardDescription className="text-lg">
                  Join thousands of developers improving their skills with AI-powered learning
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="flex flex-col sm:flex-row gap-4">
                  <Button size="lg" className="flex-1 text-lg" onClick={handleGetStarted}>
                    {session?.user ? "Go to Dashboard" : "Create Free Account"}
                  </Button>
                  <Button size="lg" variant="outline" className="flex-1 text-lg" asChild>
                    <Link href={session?.user ? "/lessons" : "/login"}>
                      {session?.user ? "Browse Lessons" : "Sign In"}
                    </Link>
                  </Button>
                </div>
                <p className="text-center text-sm text-muted-foreground">
                  No credit card required • Start learning in 30 seconds
                </p>
              </CardContent>
            </Card>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t py-12 bg-muted/30">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex items-center space-x-2">
              <Code2 className="h-6 w-6 text-primary" />
              <span className="font-bold text-lg">RepoRoverAI</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 RepoRoverAI. Built with Next.js and AI.
            </p>
          </div>
        </div>
      </footer>
    </>
  );
}