"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { authClient } from "@/lib/auth-client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Loader2, Code2, Github, Mail } from "lucide-react";
import Link from "next/link";
import { toast } from "sonner";

type ErrorTypes = Partial<Record<string, string>>;
const errorCodes: ErrorTypes = {
  USER_ALREADY_EXISTS: "User already registered",
};

const getErrorMessage = (code: string) => {
  if (code in errorCodes) {
    return errorCodes[code];
  }
  return "Registration failed";
};

export default function RegisterPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [githubLoading, setGithubLoading] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  });

  const handleGoogleSignup = async () => {
    setGoogleLoading(true);
    try {
      await authClient.signIn.social({
        provider: "google",
        callbackURL: "/dashboard",
      });
    } catch (error) {
      toast.error("Failed to sign up with Google");
      setGoogleLoading(false);
    }
  };

  const handleGithubSignup = async () => {
    setGithubLoading(true);
    try {
      await authClient.signIn.social({
        provider: "github",
        callbackURL: "/dashboard",
      });
    } catch (error) {
      toast.error("Failed to sign up with GitHub");
      setGithubLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (formData.password !== formData.confirmPassword) {
      toast.error("Passwords do not match");
      return;
    }

    if (formData.password.length < 8) {
      toast.error("Password must be at least 8 characters long");
      return;
    }

    setIsLoading(true);

    try {
      const { error } = await authClient.signUp.email({
        email: formData.email,
        name: formData.name,
        password: formData.password,
      });

      if (error?.code) {
        toast.error(getErrorMessage(error.code) || "Registration failed");
        setIsLoading(false);
        return;
      }

      toast.success("Account created successfully!");
      router.push("/login?registered=true");
    } catch (error) {
      toast.error("An unexpected error occurred. Please try again.");
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-muted/30 to-background flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-2xl border-muted/40">
        <CardHeader className="space-y-3 text-center pb-4">
          <div className="flex justify-center">
            <div className="p-3 bg-gradient-to-br from-primary/20 to-primary/10 rounded-2xl">
              <Code2 className="h-10 w-10 text-primary" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Join RepoRover AI
          </CardTitle>
          <CardDescription className="text-base">
            Start your AI-powered learning journey in seconds
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!showEmailForm ? (
            <>
              {/* Social Login Buttons */}
              <div className="space-y-3">
                <Button
                  type="button"
                  variant="outline"
                  className="w-full h-12 text-base font-medium hover:bg-accent hover:border-primary/30 transition-all"
                  onClick={handleGoogleSignup}
                  disabled={googleLoading || githubLoading}
                >
                  {googleLoading ? (
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  ) : (
                    <svg className="mr-2 h-5 w-5" viewBox="0 0 24 24">
                      <path
                        fill="currentColor"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="currentColor"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="currentColor"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                  )}
                  Continue with Google
                </Button>

                <Button
                  type="button"
                  variant="outline"
                  className="w-full h-12 text-base font-medium hover:bg-accent hover:border-primary/30 transition-all"
                  onClick={handleGithubSignup}
                  disabled={googleLoading || githubLoading}
                >
                  {githubLoading ? (
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                  ) : (
                    <Github className="mr-2 h-5 w-5" />
                  )}
                  Continue with GitHub
                </Button>
              </div>

              <div className="relative my-6">
                <Separator />
                <span className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 bg-card px-3 text-sm text-muted-foreground">
                  or
                </span>
              </div>

              {/* Email Signup Button */}
              <Button
                type="button"
                variant="outline"
                className="w-full h-12 text-base font-medium hover:bg-accent hover:border-primary/30 transition-all"
                onClick={() => setShowEmailForm(true)}
              >
                <Mail className="mr-2 h-5 w-5" />
                Continue with Email
              </Button>
            </>
          ) : (
            <>
              {/* Email Form */}
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="name">Full Name</Label>
                  <Input
                    id="name"
                    type="text"
                    placeholder="John Doe"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                    disabled={isLoading}
                    className="h-11"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    required
                    disabled={isLoading}
                    className="h-11"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    required
                    disabled={isLoading}
                    autoComplete="off"
                    className="h-11"
                  />
                  <p className="text-xs text-muted-foreground">Must be at least 8 characters</p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="confirmPassword">Confirm Password</Label>
                  <Input
                    id="confirmPassword"
                    type="password"
                    placeholder="••••••••"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                    required
                    disabled={isLoading}
                    autoComplete="off"
                    className="h-11"
                  />
                </div>

                <Button type="submit" className="w-full h-11 text-base" disabled={isLoading}>
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                      Creating account...
                    </>
                  ) : (
                    "Create Account"
                  )}
                </Button>

                <Button
                  type="button"
                  variant="ghost"
                  className="w-full"
                  onClick={() => setShowEmailForm(false)}
                  disabled={isLoading}
                >
                  ← Back to social login
                </Button>
              </form>
            </>
          )}

          <div className="mt-6 text-center text-sm">
            <span className="text-muted-foreground">Already have an account? </span>
            <Link href="/login" className="text-primary hover:underline font-semibold">
              Sign in
            </Link>
          </div>

          <p className="text-xs text-center text-muted-foreground mt-4">
            By continuing, you agree to our Terms of Service and Privacy Policy
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
