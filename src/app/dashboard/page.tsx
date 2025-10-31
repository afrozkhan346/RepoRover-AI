"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";
import { Navigation } from "@/components/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { 
  BookOpen, 
  Trophy, 
  Zap, 
  TrendingUp, 
  Target,
  Clock,
  Award,
  BarChart3,
  Sparkles,
  ArrowRight
} from "lucide-react";
import Link from "next/link";

export default function DashboardPage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const [stats, setStats] = useState<any>(null);
  const [recentProgress, setRecentProgress] = useState<any[]>([]);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isPending && !session?.user) {
      router.push("/login");
    }
  }, [session, isPending, router]);

  useEffect(() => {
    if (session?.user) {
      fetchDashboardData();
    }
  }, [session]);

  const fetchDashboardData = async () => {
    try {
      const token = localStorage.getItem("bearer_token");
      
      // Fetch user progress stats
      const statsRes = await fetch("/api/user-progress", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const statsData = await statsRes.json();
      setStats(statsData.progress?.[0] || null);

      // Fetch recent lesson progress
      const progressRes = await fetch("/api/lesson-progress", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const progressData = await progressRes.json();
      setRecentProgress(progressData.progress?.slice(0, 5) || []);

      // Fetch user achievements
      const achievementsRes = await fetch("/api/user-achievements", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const achievementsData = await achievementsRes.json();
      setAchievements(achievementsData.achievements?.slice(0, 3) || []);
      
      setIsLoading(false);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
      setIsLoading(false);
    }
  };

  if (isPending || isLoading) {
    return (
      <>
        <Navigation />
        <div className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background">
          <div className="container mx-auto px-4 py-8">
            <div className="animate-pulse space-y-6">
              <div className="h-12 bg-muted rounded-lg w-1/3" />
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-32 bg-muted rounded-lg" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  const currentLevel = Math.floor((stats?.total_xp || 0) / 100) + 1;
  const xpForNextLevel = currentLevel * 100;
  const xpProgress = ((stats?.total_xp || 0) % 100);

  return (
    <>
      <Navigation />
      <main className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background">
        <div className="container mx-auto px-4 py-8">
          {/* Welcome Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">
              Welcome back, {session?.user?.name?.split(" ")[0]}! 👋
            </h1>
            <p className="text-muted-foreground text-lg">
              Continue your learning journey and level up your skills
            </p>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <Card className="border-2">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Total XP
                </CardTitle>
                <Zap className="h-5 w-5 text-yellow-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats?.total_xp || 0}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Level {currentLevel}
                </p>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Lessons Completed
                </CardTitle>
                <BookOpen className="h-5 w-5 text-blue-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats?.lessons_completed || 0}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Keep learning!
                </p>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Current Streak
                </CardTitle>
                <TrendingUp className="h-5 w-5 text-green-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{stats?.current_streak || 0}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {stats?.current_streak > 0 ? "Days in a row 🔥" : "Start today!"}
                </p>
              </CardContent>
            </Card>

            <Card className="border-2">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Achievements
                </CardTitle>
                <Trophy className="h-5 w-5 text-purple-500" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold">{achievements.length}</div>
                <p className="text-xs text-muted-foreground mt-1">
                  Unlocked badges
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Level Progress */}
          <Card className="mb-8 border-2 bg-gradient-to-br from-primary/5 to-background">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl">Level {currentLevel}</CardTitle>
                  <CardDescription>
                    {xpProgress} / 100 XP to Level {currentLevel + 1}
                  </CardDescription>
                </div>
                <Badge variant="secondary" className="text-lg px-4 py-2">
                  <Sparkles className="h-4 w-4 mr-1" />
                  {xpProgress}%
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Progress value={xpProgress} className="h-3" />
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Recent Progress */}
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Target className="h-5 w-5 text-primary" />
                      Continue Learning
                    </CardTitle>
                    <CardDescription>Pick up where you left off</CardDescription>
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <Link href="/lessons">
                      View All <ArrowRight className="h-4 w-4 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {recentProgress.length > 0 ? (
                  recentProgress.map((progress: any) => (
                    <div
                      key={progress.id}
                      className="flex items-center justify-between p-4 rounded-lg border hover:border-primary/50 transition-colors cursor-pointer"
                      onClick={() => router.push(`/lessons/${progress.lesson_id}`)}
                    >
                      <div className="flex-1">
                        <h4 className="font-semibold mb-1">Lesson #{progress.lesson_id}</h4>
                        <div className="flex items-center gap-2 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>
                            {progress.completed ? "Completed" : `${progress.progress}% complete`}
                          </span>
                        </div>
                      </div>
                      <Progress value={progress.progress} className="w-24 h-2" />
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <BookOpen className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground mb-4">No lessons started yet</p>
                    <Button asChild>
                      <Link href="/lessons">Start Learning</Link>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Recent Achievements */}
            <Card className="border-2">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <Award className="h-5 w-5 text-primary" />
                      Recent Achievements
                    </CardTitle>
                    <CardDescription>Your latest unlocks</CardDescription>
                  </div>
                  <Button variant="ghost" size="sm" asChild>
                    <Link href="/achievements">
                      View All <ArrowRight className="h-4 w-4 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {achievements.length > 0 ? (
                  achievements.map((achievement: any) => (
                    <div
                      key={achievement.id}
                      className="flex items-center gap-4 p-4 rounded-lg border"
                    >
                      <div className="text-4xl">{achievement.icon}</div>
                      <div className="flex-1">
                        <h4 className="font-semibold">{achievement.title}</h4>
                        <p className="text-sm text-muted-foreground">
                          {achievement.description}
                        </p>
                      </div>
                      <Badge variant="secondary">+{achievement.xp_reward} XP</Badge>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <Trophy className="h-12 w-12 text-muted-foreground mx-auto mb-3" />
                    <p className="text-muted-foreground mb-4">No achievements yet</p>
                    <Button asChild variant="outline">
                      <Link href="/lessons">Start earning badges</Link>
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card className="border-2 hover:border-primary/50 transition-colors cursor-pointer group" onClick={() => router.push("/lessons")}>
              <CardHeader>
                <BookOpen className="h-8 w-8 text-primary mb-2" />
                <CardTitle className="group-hover:text-primary transition-colors">Browse Lessons</CardTitle>
                <CardDescription>Explore all available courses</CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-colors cursor-pointer group" onClick={() => router.push("/achievements")}>
              <CardHeader>
                <Trophy className="h-8 w-8 text-primary mb-2" />
                <CardTitle className="group-hover:text-primary transition-colors">View Achievements</CardTitle>
                <CardDescription>See all available badges</CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 hover:border-primary/50 transition-colors cursor-pointer group" onClick={() => router.push("/profile")}>
              <CardHeader>
                <BarChart3 className="h-8 w-8 text-primary mb-2" />
                <CardTitle className="group-hover:text-primary transition-colors">Track Progress</CardTitle>
                <CardDescription>View detailed statistics</CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </main>
    </>
  );
}
