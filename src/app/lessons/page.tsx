export default function LessonsPage() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-[radial-gradient(circle_at_top,_rgba(14,165,233,0.14),_transparent_35%),linear-gradient(180deg,_rgba(2,6,23,0.04),_transparent_40%)] p-6">
      <section className="max-w-2xl rounded-3xl border bg-white/85 p-8 shadow-2xl backdrop-blur">
        <div className="space-y-4 text-left">
          <p className="text-xs font-semibold uppercase tracking-[0.3em] text-sky-700">Migration notice</p>
          <h1 className="text-4xl font-bold tracking-tight text-slate-900">Lessons have moved to the Vite app.</h1>
          <p className="text-base leading-7 text-slate-600">
            The lessons interface is now part of the Vite frontend in <span className="font-semibold">frontend/</span>. 
            This provides better performance and a unified experience with the rest of the learning platform.
          </p>
          <div className="rounded-2xl border border-sky-200 bg-sky-50 p-4 text-sm text-sky-900">
            Use <span className="font-semibold">npm run dev</span> from the repo root to start the Vite app.
          </div>
        </div>
      </section>
    </main>
  );
}
  const [isLoading, setIsLoading] = useState(true);
  const [expandedPath, setExpandedPath] = useState<number | null>(null);

  useEffect(() => {
    if (!sessionLoading && !session?.user) {
      router.push("/login?redirect=/lessons");
    }
  }, [session, sessionLoading, router]);

  useEffect(() => {
    const fetchLearningPaths = async () => {
      try {
        const response = await fetch("/api/learning-paths");
        if (!response.ok) throw new Error("Failed to fetch learning paths");
        const data = await response.json();
        setLearningPaths(data.sort((a: LearningPath, b: LearningPath) => a.orderIndex - b.orderIndex));
      } catch (error) {
        toast.error("Failed to load learning paths");
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchLearningPaths();
  }, []);

  const fetchLessons = async (pathId: number) => {
    if (lessons[pathId]) {
      setExpandedPath(expandedPath === pathId ? null : pathId);
      return;
    }

    const token = localStorage.getItem("bearer_token");
    try {
      const response = await fetch(`/api/lessons?learningPathId=${pathId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (!response.ok) throw new Error("Failed to fetch lessons");
      const data = await response.json();
      setLessons((prev) => ({
        ...prev,
        [pathId]: data.sort((a: Lesson, b: Lesson) => a.orderIndex - b.orderIndex),
      }));
      setExpandedPath(pathId);
    } catch (error) {
      toast.error("Failed to load lessons");
      console.error(error);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case "beginner":
        return "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20";
      case "intermediate":
        return "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20";
      case "advanced":
        return "bg-purple-500/10 text-purple-700 dark:text-purple-400 border-purple-500/20";
      default:
        return "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20";
    }
  };

  if (sessionLoading || isLoading) {
    return (
      <>
        <Navigation />
        <div className="container mx-auto px-4 py-8">
          <div className="space-y-6">
            {[1, 2, 3].map((i) => (
              <Card key={i}>
                <CardHeader>
                  <Skeleton className="h-8 w-3/4" />
                  <Skeleton className="h-4 w-full mt-2" />
                </CardHeader>
                <CardContent>
                  <div className="flex gap-2">
                    <Skeleton className="h-6 w-20" />
                    <Skeleton className="h-6 w-24" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </>
    );
  }

  if (!session?.user) return null;

  return (
    <>
      <Navigation />
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-5xl mx-auto space-y-8">
          {/* Header */}
          <div className="space-y-4">
            <h1 className="text-4xl font-bold">Learning Paths</h1>
            <p className="text-lg text-muted-foreground">
              Choose a learning path and start your coding journey. Each path contains structured lessons designed to take you from beginner to expert.
            </p>
          </div>

          {/* Learning Paths */}
          <div className="space-y-6">
            {learningPaths.map((path) => (
              <Card key={path.id} className="border-2 hover:border-primary/50 transition-all">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-4">
                      <div className="text-5xl">{path.icon}</div>
                      <div className="space-y-2">
                        <CardTitle className="text-2xl">{path.title}</CardTitle>
                        <CardDescription className="text-base">{path.description}</CardDescription>
                        <div className="flex items-center gap-3 pt-2">
                          <Badge variant="outline" className={getDifficultyColor(path.difficulty)}>
                            {path.difficulty}
                          </Badge>
                          <div className="flex items-center gap-1 text-sm text-muted-foreground">
                            <Clock className="h-4 w-4" />
                            <span>{path.estimatedHours} hours</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Button
                    onClick={() => fetchLessons(path.id)}
                    variant={expandedPath === path.id ? "secondary" : "default"}
                    className="w-full sm:w-auto"
                  >
                    {expandedPath === path.id ? (
                      "Hide Lessons"
                    ) : (
                      <>
                        View Lessons
                        <ArrowRight className="ml-2 h-4 w-4" />
                      </>
                    )}
                  </Button>

                  {/* Lessons List */}
                  {expandedPath === path.id && lessons[path.id] && (
                    <div className="mt-6 space-y-3">
                      <h3 className="font-semibold text-lg mb-4">Lessons in this path:</h3>
                      {lessons[path.id].map((lesson, index) => (
                        <Link key={lesson.id} href={`/lessons/${lesson.id}`}>
                          <Card className="hover:bg-muted/50 transition-colors cursor-pointer border">
                            <CardContent className="p-4">
                              <div className="flex items-start justify-between">
                                <div className="flex gap-3 flex-1">
                                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center text-primary font-semibold">
                                    {index + 1}
                                  </div>
                                  <div className="space-y-1 flex-1">
                                    <h4 className="font-semibold">{lesson.title}</h4>
                                    <p className="text-sm text-muted-foreground line-clamp-1">
                                      {lesson.description}
                                    </p>
                                    <div className="flex items-center gap-3 text-xs text-muted-foreground pt-1">
                                      <div className="flex items-center gap-1">
                                        <Clock className="h-3 w-3" />
                                        <span>{lesson.estimatedMinutes} min</span>
                                      </div>
                                      <div className="flex items-center gap-1">
                                        <Award className="h-3 w-3" />
                                        <span>{lesson.xpReward} XP</span>
                                      </div>
                                      <Badge
                                        variant="outline"
                                        className={`${getDifficultyColor(lesson.difficulty)} text-xs`}
                                      >
                                        {lesson.difficulty}
                                      </Badge>
                                    </div>
                                  </div>
                                </div>
                                <ArrowRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                              </div>
                            </CardContent>
                          </Card>
                        </Link>
                      ))}
                    </div>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
