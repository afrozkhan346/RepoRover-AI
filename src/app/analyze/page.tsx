"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";
import { Navigation } from "@/components/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  GitBranch, 
  Star, 
  GitFork, 
  Eye, 
  AlertCircle, 
  Calendar,
  Code2,
  FileText,
  Loader2,
  Github,
  CheckCircle2,
  TrendingUp,
  BookOpen
} from "lucide-react";
import { toast } from "sonner";
import { useEffect } from "react";

export default function AnalyzePage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const [githubUrl, setGithubUrl] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    if (!isPending && !session?.user) {
      router.push("/login");
    }
  }, [session, isPending, router]);

  const handleAnalyze = async () => {
    if (!githubUrl.trim()) {
      toast.error("Please enter a GitHub repository URL");
      return;
    }

    setIsAnalyzing(true);
    setAnalysis(null);

    try {
      const token = localStorage.getItem("bearer_token");
      const response = await fetch("/api/github/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ githubUrl }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to analyze repository");
      }

      setAnalysis(data);
      toast.success("Repository analyzed successfully!");
    } catch (error) {
      console.error("Analysis error:", error);
      toast.error((error as Error).message);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleSaveRepository = async () => {
    if (!analysis) return;

    setIsSaving(true);

    try {
      const token = localStorage.getItem("bearer_token");
      const response = await fetch("/api/repositories", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          githubUrl,
          repoName: analysis.name,
          description: analysis.description,
          language: analysis.language,
          stars: analysis.stars,
          analyzedAt: new Date().toISOString(),
          analysisData: JSON.stringify(analysis),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to save repository");
      }

      toast.success("Repository saved to your collection!");
    } catch (error) {
      console.error("Save error:", error);
      toast.error((error as Error).message);
    } finally {
      setIsSaving(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + " " + sizes[i];
  };

  if (isPending) {
    return (
      <>
        <Navigation />
        <div className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background flex items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
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
              <Github className="h-10 w-10 text-primary" />
              GitHub Repository Analyzer
            </h1>
            <p className="text-muted-foreground text-lg">
              Analyze any GitHub repository to understand its structure, languages, and activity
            </p>
          </div>

          {/* Input Section */}
          <Card className="mb-8 border-2">
            <CardHeader>
              <CardTitle>Enter Repository URL</CardTitle>
              <CardDescription>
                Paste a GitHub repository URL to start analysis
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <div className="flex-1">
                  <Label htmlFor="github-url" className="sr-only">
                    GitHub URL
                  </Label>
                  <Input
                    id="github-url"
                    type="url"
                    placeholder="https://github.com/username/repository"
                    value={githubUrl}
                    onChange={(e) => setGithubUrl(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && handleAnalyze()}
                    disabled={isAnalyzing}
                  />
                </div>
                <Button onClick={handleAnalyze} disabled={isAnalyzing}>
                  {isAnalyzing ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <GitBranch className="mr-2 h-4 w-4" />
                      Analyze
                    </>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Analysis Results */}
          {analysis && (
            <div className="space-y-6">
              {/* Overview Card */}
              <Card className="border-2">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="text-2xl mb-2">{analysis.name}</CardTitle>
                      <CardDescription className="text-base">
                        {analysis.description || "No description available"}
                      </CardDescription>
                      <div className="flex items-center gap-2 mt-3">
                        <Badge variant="secondary">
                          <Code2 className="mr-1 h-3 w-3" />
                          {analysis.language}
                        </Badge>
                        {analysis.license && (
                          <Badge variant="outline">{analysis.license}</Badge>
                        )}
                      </div>
                    </div>
                    <Button onClick={handleSaveRepository} disabled={isSaving}>
                      {isSaving ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Saving...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="mr-2 h-4 w-4" />
                          Save Repository
                        </>
                      )}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="flex items-center gap-3">
                      <Star className="h-5 w-5 text-yellow-500" />
                      <div>
                        <p className="text-2xl font-bold">{analysis.stars.toLocaleString()}</p>
                        <p className="text-xs text-muted-foreground">Stars</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <GitFork className="h-5 w-5 text-blue-500" />
                      <div>
                        <p className="text-2xl font-bold">{analysis.forks.toLocaleString()}</p>
                        <p className="text-xs text-muted-foreground">Forks</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Eye className="h-5 w-5 text-green-500" />
                      <div>
                        <p className="text-2xl font-bold">{analysis.watchers.toLocaleString()}</p>
                        <p className="text-xs text-muted-foreground">Watchers</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <AlertCircle className="h-5 w-5 text-orange-500" />
                      <div>
                        <p className="text-2xl font-bold">{analysis.openIssues}</p>
                        <p className="text-xs text-muted-foreground">Open Issues</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Detailed Information Tabs */}
              <Card className="border-2">
                <Tabs defaultValue="languages" className="w-full">
                  <CardHeader>
                    <TabsList className="grid w-full grid-cols-4">
                      <TabsTrigger value="languages">Languages</TabsTrigger>
                      <TabsTrigger value="activity">Activity</TabsTrigger>
                      <TabsTrigger value="structure">Structure</TabsTrigger>
                      <TabsTrigger value="details">Details</TabsTrigger>
                    </TabsList>
                  </CardHeader>
                  <CardContent>
                    {/* Languages Tab */}
                    <TabsContent value="languages" className="space-y-4">
                      <h3 className="font-semibold mb-3">Language Distribution</h3>
                      {Object.entries(analysis.languages).length > 0 ? (
                        <div className="space-y-3">
                          {Object.entries(analysis.languages)
                            .sort(([, a]: any, [, b]: any) => b - a)
                            .map(([lang, bytes]: any) => {
                              const total = Object.values(analysis.languages).reduce(
                                (sum: number, val: any) => sum + val,
                                0
                              ) as number;
                              const percentage = ((bytes / total) * 100).toFixed(1);
                              return (
                                <div key={lang} className="space-y-1">
                                  <div className="flex justify-between text-sm">
                                    <span className="font-medium">{lang}</span>
                                    <span className="text-muted-foreground">
                                      {percentage}% · {formatBytes(bytes)}
                                    </span>
                                  </div>
                                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                                    <div
                                      className="h-full bg-primary rounded-full"
                                      style={{ width: `${percentage}%` }}
                                    />
                                  </div>
                                </div>
                              );
                            })}
                        </div>
                      ) : (
                        <p className="text-muted-foreground">No language data available</p>
                      )}
                    </TabsContent>

                    {/* Activity Tab */}
                    <TabsContent value="activity" className="space-y-4">
                      <h3 className="font-semibold mb-3">Recent Commits</h3>
                      {analysis.recentCommits.length > 0 ? (
                        <div className="space-y-3">
                          {analysis.recentCommits.map((commit: any) => (
                            <div
                              key={commit.sha}
                              className="border rounded-lg p-4 hover:border-primary/50 transition-colors"
                            >
                              <div className="flex items-start justify-between gap-4">
                                <div className="flex-1">
                                  <p className="font-medium mb-1">{commit.message}</p>
                                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <span>{commit.author}</span>
                                    <span>·</span>
                                    <span>{formatDate(commit.date)}</span>
                                  </div>
                                </div>
                                <Badge variant="outline" className="font-mono text-xs">
                                  {commit.sha.substring(0, 7)}
                                </Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-muted-foreground">No recent commits available</p>
                      )}
                    </TabsContent>

                    {/* Structure Tab */}
                    <TabsContent value="structure" className="space-y-4">
                      <div className="flex items-center justify-between mb-3">
                        <h3 className="font-semibold">File Structure</h3>
                        <Badge variant="secondary">
                          {analysis.fileCount} files total
                        </Badge>
                      </div>
                      {analysis.fileStructure.length > 0 ? (
                        <div className="space-y-1 max-h-96 overflow-y-auto">
                          {analysis.fileStructure.map((file: any, index: number) => (
                            <div
                              key={index}
                              className="flex items-center gap-2 py-1 px-2 rounded hover:bg-muted text-sm font-mono"
                            >
                              {file.type === "tree" ? (
                                <FileText className="h-4 w-4 text-blue-500" />
                              ) : (
                                <FileText className="h-4 w-4 text-muted-foreground" />
                              )}
                              <span className="flex-1">{file.path}</span>
                              {file.size && (
                                <span className="text-xs text-muted-foreground">
                                  {formatBytes(file.size)}
                                </span>
                              )}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-muted-foreground">No file structure available</p>
                      )}
                    </TabsContent>

                    {/* Details Tab */}
                    <TabsContent value="details" className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div>
                          <h4 className="font-semibold mb-2 text-sm text-muted-foreground">
                            Repository Details
                          </h4>
                          <div className="space-y-2">
                            <div className="flex justify-between py-2 border-b">
                              <span className="text-sm">Full Name</span>
                              <span className="text-sm font-medium">{analysis.fullName}</span>
                            </div>
                            <div className="flex justify-between py-2 border-b">
                              <span className="text-sm">Owner</span>
                              <span className="text-sm font-medium">{analysis.owner}</span>
                            </div>
                            <div className="flex justify-between py-2 border-b">
                              <span className="text-sm">Default Branch</span>
                              <Badge variant="outline">{analysis.defaultBranch}</Badge>
                            </div>
                            <div className="flex justify-between py-2 border-b">
                              <span className="text-sm">Repository Size</span>
                              <span className="text-sm font-medium">
                                {formatBytes(analysis.size * 1024)}
                              </span>
                            </div>
                          </div>
                        </div>
                        <div>
                          <h4 className="font-semibold mb-2 text-sm text-muted-foreground">
                            Timeline
                          </h4>
                          <div className="space-y-2">
                            <div className="flex justify-between py-2 border-b">
                              <span className="text-sm flex items-center gap-2">
                                <Calendar className="h-4 w-4" />
                                Created
                              </span>
                              <span className="text-sm font-medium">
                                {formatDate(analysis.createdAt)}
                              </span>
                            </div>
                            <div className="flex justify-between py-2 border-b">
                              <span className="text-sm flex items-center gap-2">
                                <TrendingUp className="h-4 w-4" />
                                Last Updated
                              </span>
                              <span className="text-sm font-medium">
                                {formatDate(analysis.updatedAt)}
                              </span>
                            </div>
                          </div>
                          {analysis.topics && analysis.topics.length > 0 && (
                            <div className="mt-4">
                              <h4 className="font-semibold mb-2 text-sm text-muted-foreground">
                                Topics
                              </h4>
                              <div className="flex flex-wrap gap-2">
                                {analysis.topics.map((topic: string) => (
                                  <Badge key={topic} variant="secondary">
                                    {topic}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </TabsContent>
                  </CardContent>
                </Tabs>
              </Card>
            </div>
          )}

          {/* Empty State */}
          {!analysis && !isAnalyzing && (
            <Card className="border-2 border-dashed">
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Github className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-xl font-semibold mb-2">No Repository Analyzed Yet</h3>
                <p className="text-muted-foreground text-center max-w-md mb-4">
                  Enter a GitHub repository URL above to analyze its structure, languages, and activity
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </main>
    </>
  );
}
