"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";
import { Navigation } from "@/components/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Trophy, Lock, Sparkles, Award } from "lucide-react";

export default function AchievementsPage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const [allAchievements, setAllAchievements] = useState<any[]>([]);
  const [userAchievements, setUserAchievements] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!isPending && !session?.user) {
      router.push("/login");
    }
  }, [session, isPending, router]);

  useEffect(() => {
    if (session?.user) {
      fetchAchievements();
    }
  }, [session]);

  const fetchAchievements = async () => {
    try {
      const token = localStorage.getItem("bearer_token");

      // Fetch all achievements
      const allRes = await fetch("/api/achievements", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const allData = await allRes.json();
      setAllAchievements(allData.achievements || []);

      // Fetch user's unlocked achievements
      const userRes = await fetch("/api/user-achievements", {
        headers: { Authorization: `Bearer ${token}` }
      });
      const userData = await userRes.json();
      setUserAchievements(userData.achievements || []);

      setIsLoading(false);
    } catch (error) {
      console.error("Error fetching achievements:", error);
      setIsLoading(false);
    }
  };

  const isUnlocked = (achievementId: number) => {
    return userAchievements.some(ua => ua.achievement_id === achievementId);
  };

  const unlockedCount = userAchievements.length;
  const totalCount = allAchievements.length;
  const completionPercentage = totalCount > 0 ? (unlockedCount / totalCount) * 100 : 0;

  if (isPending || isLoading) {
    return (
      <>
        <Navigation />
        <div className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background">
          <div className="container mx-auto px-4 py-8">
            <div className="animate-pulse space-y-6">
              <div className="h-12 bg-muted rounded-lg w-1/3" />
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {[1, 2, 3, 4, 5, 6].map(i => (
                  <div key={i} className="h-48 bg-muted rounded-lg" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navigation />
      <main className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background">
        <div className="container mx-auto px-4 py-8">
          {/* Header */}
          <div className="mb-8">
            <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
              <Trophy className="h-10 w-10 text-primary" />
              Achievements
            </h1>
            <p className="text-muted-foreground text-lg">
              Unlock badges by completing lessons and reaching milestones
            </p>
          </div>

          {/* Progress Overview */}
          <Card className="mb-8 border-2 bg-gradient-to-br from-primary/5 to-background">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-xl">Your Progress</CardTitle>
                  <CardDescription>
                    {unlockedCount} of {totalCount} achievements unlocked
                  </CardDescription>
                </div>
                <Badge variant="secondary" className="text-lg px-4 py-2">
                  <Sparkles className="h-4 w-4 mr-1" />
                  {Math.round(completionPercentage)}%
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              <Progress value={completionPercentage} className="h-3" />
            </CardContent>
          </Card>

          {/* Achievements Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {allAchievements.map((achievement) => {
              const unlocked = isUnlocked(achievement.id);
              
              return (
                <Card
                  key={achievement.id}
                  className={`border-2 transition-all ${
                    unlocked
                      ? "border-primary/50 hover:border-primary shadow-lg"
                      : "border-muted opacity-60"
                  }`}
                >
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="text-5xl mb-3">
                        {unlocked ? achievement.icon : "🔒"}
                      </div>
                      {unlocked ? (
                        <Badge variant="default" className="bg-primary">
                          <Award className="h-3 w-3 mr-1" />
                          Unlocked
                        </Badge>
                      ) : (
                        <Badge variant="secondary">
                          <Lock className="h-3 w-3 mr-1" />
                          Locked
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-xl">{achievement.title}</CardTitle>
                    <CardDescription className="text-base">
                      {achievement.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground">Reward</span>
                      <Badge variant="outline" className="font-semibold">
                        +{achievement.xp_reward} XP
                      </Badge>
                    </div>
                    {achievement.requirement && (
                      <p className="text-xs text-muted-foreground mt-2">
                        {achievement.requirement}
                      </p>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>

          {totalCount === 0 && (
            <Card className="border-2 text-center py-12">
              <CardContent>
                <Trophy className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Achievements Yet</h3>
                <p className="text-muted-foreground">
                  Start completing lessons to unlock achievements!
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </>
  );
}
