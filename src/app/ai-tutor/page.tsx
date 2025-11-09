"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSession } from "@/lib/auth-client";
import { Navigation } from "@/components/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Sparkles, 
  Code2, 
  Loader2, 
  BookOpen, 
  Lightbulb,
  MessageSquare,
  Copy,
  Check
} from "lucide-react";
import { toast } from "sonner";

// Component to render formatted explanation
function FormattedExplanation({ text }: { text: string }) {
  // Convert markdown-style formatting to HTML
  const formatText = (content: string) => {
    return content
      // Convert **bold** to <strong>
      .replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold text-foreground">$1</strong>')
      // Convert *italic* to <em> (but not ** which is already handled)
      .replace(/(?<!\*)\*([^*]+?)\*(?!\*)/g, '<em class="italic text-primary">$1</em>')
      // Convert `code` to styled spans
      .replace(/`([^`]+?)`/g, '<code class="px-1.5 py-0.5 bg-muted text-primary rounded text-sm font-mono">$1</code>')
      // Convert ### Headers to h3
      .replace(/^###\s+(.+?)$/gm, '<h3 class="text-lg font-bold mt-6 mb-3 text-foreground">$1</h3>')
      // Convert ## Headers to h2
      .replace(/^##\s+(.+?)$/gm, '<h2 class="text-xl font-bold mt-8 mb-4 text-foreground">$1</h2>')
      // Convert # Headers to h1
      .replace(/^#\s+(.+?)$/gm, '<h1 class="text-2xl font-bold mt-8 mb-4 text-foreground">$1</h1>')
      // Convert bullet points
      .replace(/^\*\s+(.+?)$/gm, '<li class="ml-4">$1</li>')
      // Split into paragraphs (double line breaks)
      .split('\n\n')
      .map(para => {
        // Wrap lists
        if (para.includes('<li class="ml-4">')) {
          return `<ul class="list-disc ml-6 space-y-2 my-4">${para}</ul>`;
        }
        // Don't wrap headers
        if (para.match(/^<h[1-3]/)) {
          return para;
        }
        // Wrap regular paragraphs
        return `<p class="mb-4 leading-relaxed">${para.replace(/\n/g, '<br/>')}</p>`;
      })
      .join('\n');
  };

  // Split by code blocks first
  const parts = text.split(/(```[\s\S]*?```)/g);
  
  return (
    <div className="space-y-2">
      {parts.map((part, index) => {
        // Check if this is a code block
        if (part.startsWith('```')) {
          const lines = part.split('\n');
          const language = lines[0].replace('```', '').trim() || 'code';
          const code = lines.slice(1, -1).join('\n');
          
          return (
            <div key={index} className="my-6">
              <div className="flex items-center gap-2 px-4 py-2 bg-muted rounded-t-lg border border-b-0">
                <Code2 className="h-4 w-4 text-primary" />
                <span className="text-xs font-mono font-semibold text-foreground">{language}</span>
              </div>
              <pre className="bg-slate-950 dark:bg-slate-900 text-slate-50 p-4 rounded-b-lg overflow-x-auto border border-slate-700">
                <code className="text-sm font-mono leading-relaxed">{code}</code>
              </pre>
            </div>
          );
        }
        
        // Skip empty parts
        if (!part.trim()) return null;
        
        // Regular text with inline formatting
        return (
          <div 
            key={index}
            className="text-sm"
            dangerouslySetInnerHTML={{ __html: formatText(part) }}
          />
        );
      })}
    </div>
  );
}

export default function AITutorPage() {
  const router = useRouter();
  const { data: session, isPending } = useSession();
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("javascript");
  const [question, setQuestion] = useState("");
  const [explanation, setExplanation] = useState("");
  const [isExplaining, setIsExplaining] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!isPending && !session?.user) {
      router.push("/login");
    }
  }, [session, isPending, router]);

  const handleExplain = async () => {
    if (!code.trim()) {
      toast.error("Please enter some code to analyze");
      return;
    }

    setIsExplaining(true);
    setExplanation("");

    try {
      const token = localStorage.getItem("bearer_token");
      const response = await fetch("/api/ai/explain-code", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ 
          code, 
          language,
          question: question.trim() || undefined
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Failed to generate explanation");
      }

      setExplanation(data.explanation);
      toast.success("Explanation generated!");
    } catch (error) {
      console.error("Explanation error:", error);
      toast.error((error as Error).message);
    } finally {
      setIsExplaining(false);
    }
  };

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(explanation);
      setCopied(true);
      toast.success("Copied to clipboard!");
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      toast.error("Failed to copy");
    }
  };

  const languages = [
    "javascript",
    "typescript",
    "python",
    "java",
    "cpp",
    "csharp",
    "go",
    "rust",
    "php",
    "ruby",
    "swift",
    "kotlin",
  ];

  const exampleCodes: Record<string, string> = {
    javascript: `function fibonacci(n) {
  if (n <= 1) return n;
  return fibonacci(n - 1) + fibonacci(n - 2);
}

console.log(fibonacci(10));`,
    python: `def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)`,
    typescript: `interface User {
  id: number;
  name: string;
  email: string;
}

async function fetchUser(id: number): Promise<User> {
  const response = await fetch(\`/api/users/\${id}\`);
  return response.json();
}`,
  };

  const loadExample = () => {
    const example = exampleCodes[language] || exampleCodes.javascript;
    setCode(example);
    toast.success("Example code loaded!");
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
              <Sparkles className="h-10 w-10 text-primary" />
              AI Code Tutor
            </h1>
            <p className="text-muted-foreground text-lg">
              Get instant explanations and insights about any code with AI-powered analysis
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Input Section */}
            <div className="space-y-6">
              {/* Code Input Card */}
              <Card className="border-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Code2 className="h-5 w-5 text-primary" />
                        Your Code
                      </CardTitle>
                      <CardDescription>Paste the code you want to understand</CardDescription>
                    </div>
                    <Button variant="outline" size="sm" onClick={loadExample}>
                      Load Example
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="language">Programming Language</Label>
                    <Select value={language} onValueChange={setLanguage}>
                      <SelectTrigger id="language">
                        <SelectValue placeholder="Select language" />
                      </SelectTrigger>
                      <SelectContent>
                        {languages.map((lang) => (
                          <SelectItem key={lang} value={lang}>
                            {lang.charAt(0).toUpperCase() + lang.slice(1)}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="code">Code Snippet</Label>
                    <Textarea
                      id="code"
                      placeholder="Paste your code here..."
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      className="min-h-[300px] font-mono text-sm"
                      disabled={isExplaining}
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Question Card */}
              <Card className="border-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5 text-primary" />
                    Ask a Question (Optional)
                  </CardTitle>
                  <CardDescription>
                    Ask a specific question about the code
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <Textarea
                    id="question"
                    placeholder="e.g., How does this algorithm work? What is the time complexity?"
                    value={question}
                    onChange={(e) => setQuestion(e.target.value)}
                    className="min-h-[100px]"
                    disabled={isExplaining}
                  />
                </CardContent>
              </Card>

              {/* Action Button */}
              <Button 
                onClick={handleExplain} 
                disabled={isExplaining || !code.trim()}
                size="lg"
                className="w-full"
              >
                {isExplaining ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    Analyzing Code...
                  </>
                ) : (
                  <>
                    <Sparkles className="mr-2 h-5 w-5" />
                    Explain Code
                  </>
                )}
              </Button>
            </div>

            {/* Output Section */}
            <div className="space-y-6">
              {/* Explanation Card */}
              <Card className="border-2 min-h-[500px]">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <Lightbulb className="h-5 w-5 text-primary" />
                        AI Explanation
                      </CardTitle>
                      <CardDescription>
                        Understanding your code step by step
                      </CardDescription>
                    </div>
                    {explanation && (
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleCopy}
                        disabled={copied}
                      >
                        {copied ? (
                          <>
                            <Check className="h-4 w-4 mr-2" />
                            Copied
                          </>
                        ) : (
                          <>
                            <Copy className="h-4 w-4 mr-2" />
                            Copy
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  {isExplaining ? (
                    <div className="flex flex-col items-center justify-center py-12 space-y-4">
                      <Loader2 className="h-12 w-12 animate-spin text-primary" />
                      <p className="text-muted-foreground">
                        AI is analyzing your code...
                      </p>
                    </div>
                  ) : explanation ? (
                    <div className="max-w-none">
                      <FormattedExplanation text={explanation} />
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center py-12 space-y-4 text-center">
                      <BookOpen className="h-16 w-16 text-muted-foreground" />
                      <div>
                        <h3 className="font-semibold text-lg mb-2">
                          Ready to Learn!
                        </h3>
                        <p className="text-muted-foreground max-w-md">
                          Paste your code and click "Explain Code" to get a detailed,
                          educational breakdown from our AI tutor
                        </p>
                      </div>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Tips Card */}
              <Card className="border-2 bg-primary/5">
                <CardHeader>
                  <CardTitle className="text-lg">💡 Tips for Better Results</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2 text-sm">
                  <div className="flex items-start gap-2">
                    <Badge variant="secondary" className="mt-0.5">1</Badge>
                    <p>Paste complete, working code snippets for best explanations</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <Badge variant="secondary" className="mt-0.5">2</Badge>
                    <p>Ask specific questions to get targeted answers</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <Badge variant="secondary" className="mt-0.5">3</Badge>
                    <p>Select the correct programming language for accurate analysis</p>
                  </div>
                  <div className="flex items-start gap-2">
                    <Badge variant="secondary" className="mt-0.5">4</Badge>
                    <p>Use the examples to see how the AI tutor works</p>
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
