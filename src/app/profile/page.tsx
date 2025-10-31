"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";
import { Navigation } from "@/components/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  User, 
  Mail, 
  Calendar, 
  Zap, 
  BookOpen, 
  Trophy,
  TrendingUp,
  BarChart3,
  Target
} from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const [stats, setStats] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isPending && !session?.user) {
      router.push("/login");
    }
  }, [session, isPending, router]);

  useEffect(() => {
    if (session?.user) {
      fetchUserStats();
    }
  }, [session]);

  const fetchUserStats = async () => {
    try {
      const token = localStorage.getItem("bearer_token");
      
      const res = await fetch("/api/user-progress", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await res.json();
      setStats(data.progress?.[0] || null);
      setIsLoading(false);
    } catch (error) {
      console.error("Error fetching user stats:", error);
      setIsLoading(false);
    }
  };

  const getInitials = (name: string) => {
    return name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);
  };

  if (isPending || isLoading) {
    return (
      <>
        <Navigation />
        <div className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background">
          <div className="container mx-auto px-4 py-8">
            <div className="animate-pulse space-y-6">
              <div className="h-12 bg-muted rounded-lg w-1/3" />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-48 bg-muted rounded-lg" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  const currentLevel = Math.floor((stats?.total_xp || 0) / 100) + 1;
  const xpProgress = ((stats?.total_xp || 0) % 100);

  return (
    <>
      <Navigation />
      <main className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2">Profile & Settings</h1>
            <p className="text-muted-foreground text-lg">
              View your account details and learning statistics
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Profile Card */}
            <Card className="border-2 lg:col-span-1">
              <CardHeader className="text-center">
                <div className="flex justify-center mb-4">
                  <Avatar className="h-24 w-24">
                    <AvatarFallback className="bg-primary/10 text-primary text-2xl">
                      {getInitials(session?.user?.name || "U")}
                    </AvatarFallback>
                  </Avatar>
                </div>
                <CardTitle className="text-2xl">{session?.user?.name}</CardTitle>
                <CardDescription className="text-base">
                  Level {currentLevel} Developer
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center gap-3 text-sm">
                  <Mail className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">{session?.user?.email}</span>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <Calendar className="h-4 w-4 text-muted-foreground" />
                  <span className="text-muted-foreground">
                    Joined {new Date(session?.user?.createdAt || Date.now()).toLocaleDateString()}
                  </span>
                </div>
                
                <div className="pt-4 border-t">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Level {currentLevel}</span>
                    <span className="text-sm text-muted-foreground">{xpProgress}/100 XP</span>
                  </div>
                  <Progress value={xpProgress} className="h-2" />
                </div>
              </CardContent>
            </Card>

            {/* Statistics Cards */}
            <div className="lg:col-span-2 space-y-6">
              {/* Stats Overview */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
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
                      Experience points earned
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
                      Courses finished
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
                      Longest Streak
                    </CardTitle>
                    <Trophy className="h-5 w-5 text-purple-500" />
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">{stats?.longest_streak || 0}</div>
                    <p className="text-xs text-muted-foreground mt-1">
                      Personal best
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Learning Activity */}
              <Card className="border-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <BarChart3 className="h-5 w-5 text-primary" />
                    Learning Activity
                  </CardTitle>
                  <CardDescription>Your progress over time</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <Target className="h-5 w-5 text-primary" />
                        <div>
                          <p className="font-medium">Total Progress</p>
                          <p className="text-sm text-muted-foreground">
                            Overall learning completion
                          </p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-lg px-4 py-2">
                        {stats?.lessons_completed || 0} lessons
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <Zap className="h-5 w-5 text-yellow-500" />
                        <div>
                          <p className="font-medium">XP Rate</p>
                          <p className="text-sm text-muted-foreground">
                            Average experience per lesson
                          </p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-lg px-4 py-2">
                        {stats?.lessons_completed > 0 
                          ? Math.round((stats?.total_xp || 0) / stats.lessons_completed)
                          : 0} XP
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between p-4 rounded-lg bg-muted/50">
                      <div className="flex items-center gap-3">
                        <Trophy className="h-5 w-5 text-purple-500" />
                        <div>
                          <p className="font-medium">Achievements</p>
                          <p className="text-sm text-muted-foreground">
                            Badges and milestones
                          </p>
                        </div>
                      </div>
                      <Badge variant="secondary" className="text-lg px-4 py-2">
                        View All →
                      </Badge>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </main>
    </>
  );
}
