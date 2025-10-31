"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Navigation } from "@/components/navigation";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Label } from "@/components/ui/label";
import { useSession } from "@/lib/auth-client";
import { 
  BookOpen, Clock, Award, ArrowLeft, CheckCircle2, XCircle, 
  Lightbulb, Trophy, ChevronRight 
} from "lucide-react";
import { toast } from "sonner";
import Link from "next/link";

interface Lesson {
  id: number;
  learningPathId: number;
  title: string;
  description: string;
  content: string;
  difficulty: string;
  xpReward: number;
  estimatedMinutes: number;
  orderIndex: number;
}

interface Quiz {
  id: number;
  lessonId: number;
  question: string;
  options: string;
  correctAnswer: string;
  explanation: string;
  difficulty: string;
  xpReward: number;
}

interface QuizAttempt {
  quizId: number;
  selectedAnswer: string;
  isCorrect: boolean | null;
  showExplanation: boolean;
}

export default function LessonPage() {
  const params = useParams();
  const router = useRouter();
  const { data: session, isPending: sessionLoading } = useSession();
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [quizAttempts, setQuizAttempts] = useState<Record<number, QuizAttempt>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lessonCompleted, setLessonCompleted] = useState(false);

  const lessonId = params.id as string;

  useEffect(() => {
    if (!sessionLoading && !session?.user) {
      router.push(`/login?redirect=/lessons/${lessonId}`);
    }
  }, [session, sessionLoading, router, lessonId]);

  useEffect(() => {
    const fetchLesson = async () => {
      const token = localStorage.getItem("bearer_token");
      try {
        const response = await fetch(`/api/lessons?id=${lessonId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) throw new Error("Failed to fetch lesson");
        const data = await response.json();
        setLesson(data);
      } catch (error) {
        toast.error("Failed to load lesson");
        console.error(error);
      }
    };

    const fetchQuizzes = async () => {
      const token = localStorage.getItem("bearer_token");
      try {
        const response = await fetch(`/api/quizzes?lessonId=${lessonId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });
        if (!response.ok) throw new Error("Failed to fetch quizzes");
        const data = await response.json();
        setQuizzes(data);
        
        // Initialize quiz attempts
        const initialAttempts: Record<number, QuizAttempt> = {};
        data.forEach((quiz: Quiz) => {
          initialAttempts[quiz.id] = {
            quizId: quiz.id,
            selectedAnswer: "",
            isCorrect: null,
            showExplanation: false,
          };
        });
        setQuizAttempts(initialAttempts);
      } catch (error) {
        toast.error("Failed to load quizzes");
        console.error(error);
      } finally {
        setIsLoading(false);
      }
    };

    if (lessonId) {
      fetchLesson();
      fetchQuizzes();
    }
  }, [lessonId]);

  const handleAnswerSelect = (quizId: number, answer: string) => {
    setQuizAttempts((prev) => ({
      ...prev,
      [quizId]: {
        ...prev[quizId],
        selectedAnswer: answer,
      },
    }));
  };

  const handleSubmitQuiz = async (quiz: Quiz) => {
    const attempt = quizAttempts[quiz.id];
    if (!attempt.selectedAnswer) {
      toast.error("Please select an answer");
      return;
    }

    const isCorrect = attempt.selectedAnswer === quiz.correctAnswer;
    
    setQuizAttempts((prev) => ({
      ...prev,
      [quiz.id]: {
        ...prev[quiz.id],
        isCorrect,
        showExplanation: true,
      },
    }));

    // Submit quiz attempt to backend
    const token = localStorage.getItem("bearer_token");
    try {
      await fetch("/api/quiz-attempts", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          quizId: quiz.id,
          userAnswer: attempt.selectedAnswer,
          isCorrect,
        }),
      });

      if (isCorrect) {
        toast.success(`Correct! +${quiz.xpReward} XP`, {
          icon: "🎉",
        });
      } else {
        toast.error("Incorrect answer. Try again!");
      }
    } catch (error) {
      console.error("Failed to submit quiz attempt:", error);
    }
  };

  const handleCompleteLesson = async () => {
    if (!lesson) return;
    
    setIsSubmitting(true);
    const token = localStorage.getItem("bearer_token");
    
    try {
      // Create lesson progress
      await fetch("/api/lesson-progress", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          lessonId: lesson.id,
          status: "completed",
          completedAt: new Date().toISOString(),
        }),
      });

      // Update user progress (XP)
      await fetch("/api/user-progress", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          totalXp: lesson.xpReward,
        }),
      });

      setLessonCompleted(true);
      toast.success(`Lesson completed! +${lesson.xpReward} XP`, {
        icon: "✅",
      });
    } catch (error) {
      toast.error("Failed to complete lesson");
      console.error(error);
    } finally {
      setIsSubmitting(false);
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
          <div className="max-w-4xl mx-auto space-y-6">
            <Skeleton className="h-12 w-3/4" />
            <Skeleton className="h-64 w-full" />
            <Skeleton className="h-48 w-full" />
          </div>
        </div>
      </>
    );
  }

  if (!session?.user || !lesson) return null;

  return (
    <>
      <Navigation />
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-8">
          {/* Back Button */}
          <Button variant="ghost" asChild>
            <Link href="/lessons">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Lessons
            </Link>
          </Button>

          {/* Lesson Header */}
          <div className="space-y-4">
            <div className="flex items-center gap-3">
              <Badge variant="outline" className={getDifficultyColor(lesson.difficulty)}>
                {lesson.difficulty}
              </Badge>
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Clock className="h-4 w-4" />
                <span>{lesson.estimatedMinutes} minutes</span>
              </div>
              <div className="flex items-center gap-1 text-sm text-muted-foreground">
                <Award className="h-4 w-4" />
                <span>{lesson.xpReward} XP</span>
              </div>
            </div>
            <h1 className="text-4xl font-bold">{lesson.title}</h1>
            <p className="text-lg text-muted-foreground">{lesson.description}</p>
          </div>

          {/* Lesson Content */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Lesson Content
              </CardTitle>
            </CardHeader>
            <CardContent className="prose prose-gray dark:prose-invert max-w-none">
              <div className="whitespace-pre-wrap text-base leading-relaxed">
                {lesson.content}
              </div>
            </CardContent>
          </Card>

          {/* Quizzes Section */}
          {quizzes.length > 0 && (
            <div className="space-y-6">
              <div className="flex items-center gap-2">
                <Trophy className="h-6 w-6 text-primary" />
                <h2 className="text-2xl font-bold">Practice Questions</h2>
              </div>
              
              {quizzes.map((quiz, index) => {
                const attempt = quizAttempts[quiz.id];
                const options = JSON.parse(quiz.options);

                return (
                  <Card key={quiz.id} className="border-2">
                    <CardHeader>
                      <div className="flex items-start justify-between">
                        <CardTitle className="text-lg">
                          Question {index + 1}
                        </CardTitle>
                        <Badge variant="outline" className="text-xs">
                          +{quiz.xpReward} XP
                        </Badge>
                      </div>
                      <CardDescription className="text-base pt-2">
                        {quiz.question}
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <RadioGroup
                        value={attempt?.selectedAnswer}
                        onValueChange={(value) => handleAnswerSelect(quiz.id, value)}
                        disabled={attempt?.showExplanation}
                      >
                        {options.map((option: string, optIndex: number) => (
                          <div
                            key={optIndex}
                            className={`flex items-center space-x-2 p-4 rounded-lg border-2 transition-all ${
                              attempt?.showExplanation
                                ? option === quiz.correctAnswer
                                  ? "border-green-500 bg-green-500/5"
                                  : option === attempt.selectedAnswer
                                  ? "border-red-500 bg-red-500/5"
                                  : "border-border"
                                : "border-border hover:border-primary/50 cursor-pointer"
                            }`}
                          >
                            <RadioGroupItem value={option} id={`q${quiz.id}-${optIndex}`} />
                            <Label
                              htmlFor={`q${quiz.id}-${optIndex}`}
                              className="flex-1 cursor-pointer"
                            >
                              {option}
                            </Label>
                            {attempt?.showExplanation && option === quiz.correctAnswer && (
                              <CheckCircle2 className="h-5 w-5 text-green-600" />
                            )}
                            {attempt?.showExplanation &&
                              option === attempt.selectedAnswer &&
                              !attempt.isCorrect && (
                                <XCircle className="h-5 w-5 text-red-600" />
                              )}
                          </div>
                        ))}
                      </RadioGroup>

                      {!attempt?.showExplanation && (
                        <Button
                          onClick={() => handleSubmitQuiz(quiz)}
                          disabled={!attempt?.selectedAnswer}
                          className="w-full"
                        >
                          Submit Answer
                        </Button>
                      )}

                      {attempt?.showExplanation && (
                        <Card className="bg-blue-500/5 border-blue-500/20">
                          <CardHeader>
                            <CardTitle className="flex items-center gap-2 text-base">
                              <Lightbulb className="h-5 w-5 text-blue-600" />
                              Explanation
                            </CardTitle>
                          </CardHeader>
                          <CardContent>
                            <p className="text-sm">{quiz.explanation}</p>
                          </CardContent>
                        </Card>
                      )}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}

          {/* Complete Lesson Button */}
          {!lessonCompleted ? (
            <Card className="border-2 border-primary/20 bg-primary/5">
              <CardContent className="pt-6">
                <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                  <div className="space-y-1 text-center sm:text-left">
                    <h3 className="font-semibold text-lg">Ready to complete this lesson?</h3>
                    <p className="text-sm text-muted-foreground">
                      Mark as complete to earn {lesson.xpReward} XP and unlock achievements
                    </p>
                  </div>
                  <Button
                    size="lg"
                    onClick={handleCompleteLesson}
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? "Completing..." : "Complete Lesson"}
                    <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card className="border-2 border-green-500/20 bg-green-500/5">
              <CardContent className="pt-6">
                <div className="flex items-center justify-center gap-3 text-green-700 dark:text-green-400">
                  <CheckCircle2 className="h-6 w-6" />
                  <p className="font-semibold text-lg">Lesson Completed! 🎉</p>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </>
  );
}
