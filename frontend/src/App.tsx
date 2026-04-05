import { useEffect, useMemo, useRef, useState } from "react";
import axios from "axios";
import {
  Activity,
  ArrowRight,
  BarChart3,
  Brain,
  BookOpen,
  ChartColumnBig,
  Calendar,
  ClipboardCopy,
  Code2,
  Clock,
  FileText,
  FolderOpen,
  GitBranch,
  Github,
  LayoutDashboard,
  Loader2,
  Lock,
  LogOut,
  Mail,
  Menu,
  Moon,
  Route,
  Sparkles,
  Sun,
  Target,
  TriangleAlert,
  TrendingUp,
  User,
  Award,
  Trophy,
  X,
} from "lucide-react";

import "./App.css";
import { GraphVisualizer } from "./components/analysis/graph-visualizer";
import GraphView from "./components/analysis/GraphView";
import {
  analyzeProjectByName,
  cloneProjectFromGithub,
  explainCode,
  fetchAuthSession,
  fetchAchievements,
  fetchLesson,
  fetchLessons,
  fetchUserAchievements,
  fetchLearningPaths,
  loginUser,
  logoutUser,
  registerUser,
  fetchProjectFlow,
  fetchProjectGaps,
  fetchProjectPriority,
  fetchProjectRisk,
  uploadProjectFiles,
  type AIExplanationResponse,
  type AuthUser,
  type LearningPath,
  type Lesson,
  type ProjectAnalyzeResponse,
  type ProjectCloneResponse,
  type ProjectFlowResponse,
  type ProjectGapsResponse,
  type ProjectPriorityResponse,
  type ProjectRiskResponse,
  type ProjectUploadResponse,
} from "./api";

type ResultPayload =
  | ProjectUploadResponse
  | ProjectCloneResponse
  | ProjectAnalyzeResponse
  | ProjectFlowResponse
  | ProjectGapsResponse
  | ProjectPriorityResponse
  | ProjectRiskResponse
  | null;

type SavedWorkspaceState = {
  projectName: string;
  lastAction: string;
  payload: ResultPayload;
  analysisResult: unknown;
  savedAt: string;
};

const WORKSPACE_STORAGE_KEY = "repoorover:vite-workspace";
const THEME_STORAGE_KEY = "repoorover:theme";
const SAMPLE_CODE = `function calculateScore(items) {
  const total = items.reduce((sum, item) => sum + item.value, 0);
  if (total > 100) {
    return total * 1.1;
  }
  return total;
}`;

type NavigateFn = (path: string) => void;

type Achievement = {
  id: number;
  title: string;
  description: string | null;
  icon: string | null;
  xp_reward: number;
  requirement: string;
};

type UserAchievement = {
  id: number;
  user_id: string;
  achievement_id: number;
  earned_at: string;
  created_at: string;
};

function readSavedWorkspaceState(): SavedWorkspaceState | null {
  const saved = window.localStorage.getItem(WORKSPACE_STORAGE_KEY);
  if (!saved) {
    return null;
  }

  try {
    return JSON.parse(saved) as SavedWorkspaceState;
  } catch {
    window.localStorage.removeItem(WORKSPACE_STORAGE_KEY);
    return null;
  }
}

function MainNav({
  navigate,
  authActions,
}: {
  navigate: NavigateFn;
  authActions?: React.ReactNode;
}) {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isDarkMode, setIsDarkMode] = useState(() => {
    const savedTheme = window.localStorage.getItem(THEME_STORAGE_KEY);
    if (savedTheme === "dark") {
      return true;
    }
    if (savedTheme === "light") {
      return false;
    }

    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  });
  const currentPath = window.location.pathname;

  useEffect(() => {
    document.documentElement.classList.toggle("theme-dark", isDarkMode);
    window.localStorage.setItem(THEME_STORAGE_KEY, isDarkMode ? "dark" : "light");
  }, [isDarkMode]);

  const navLinks = [
    { path: "/", label: "Home" },
    { path: "/dashboard", label: "Dashboard" },
    { path: "/analyze", label: "Analyze" },
    { path: "/ai-tutor", label: "AI Tutor" },
    { path: "/lessons", label: "Lessons" },
    { path: "/achievements", label: "Achievements" },
  ];

  const go = (path: string) => {
    setMobileMenuOpen(false);
    if (path.startsWith("#")) {
      if (window.location.pathname !== "/") {
        navigate("/");
      }
      setTimeout(() => {
        const target = document.querySelector(path);
        target?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 0);
      return;
    }
    navigate(path);
  };

  const isActivePath = (path: string) => {
    if (path === "/") {
      return currentPath === "/";
    }
    return currentPath === path || currentPath.startsWith(`${path}/`);
  };

  return (
    <nav className="site-nav">
      <div className="site-nav-inner">
        <button type="button" className="site-brand" onClick={() => go("/")}>
          <div className="site-brand-icon">
            <Code2 className="icon-sm" />
          </div>
          <span>RepoRoverAI</span>
        </button>

        <div className="site-nav-links">
          {navLinks.map((link) => (
            <button
              key={link.label}
              type="button"
              className={`site-nav-link ${isActivePath(link.path) ? "site-nav-link-active" : ""}`}
              aria-current={isActivePath(link.path) ? "page" : undefined}
              onClick={() => go(link.path)}
            >
              {link.label}
            </button>
          ))}
        </div>

        <div className="site-nav-actions">
          <button
            type="button"
            className="secondary-button site-theme-toggle"
            onClick={() => setIsDarkMode((prev) => !prev)}
            aria-label={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
            title={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
          >
            {isDarkMode ? <Sun className="icon-sm" /> : <Moon className="icon-sm" />}
          </button>
          {authActions}
          <button
            type="button"
            className="site-nav-mobile-toggle"
            onClick={() => setMobileMenuOpen((prev) => !prev)}
          >
            {mobileMenuOpen ? <X className="icon-sm" /> : <Menu className="icon-sm" />}
          </button>
        </div>
      </div>

      {mobileMenuOpen ? (
        <div className="site-nav-mobile-panel">
          {navLinks.map((link) => (
            <button
              key={link.label}
              type="button"
              className={`site-nav-mobile-link ${isActivePath(link.path) ? "site-nav-mobile-link-active" : ""}`}
              aria-current={isActivePath(link.path) ? "page" : undefined}
              onClick={() => go(link.path)}
            >
              {link.label}
            </button>
          ))}
        </div>
      ) : null}
    </nav>
  );
}

function App() {
  const [locationPath, setLocationPath] = useState(() => window.location.pathname + window.location.search);

  useEffect(() => {
    const handlePopState = () => {
      setLocationPath(window.location.pathname + window.location.search);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  const navigate = (path: string) => {
    if (window.location.pathname + window.location.search === path) {
      return;
    }

    window.history.pushState({}, "", path);
    setLocationPath(path);

    if (!path.startsWith("#")) {
      window.scrollTo({ top: 0, behavior: "auto" });
    }
  };

  const pathname = locationPath.split("?")[0];

  if (pathname === "/login") {
    return <LoginView navigate={navigate} />;
  }

  if (pathname === "/register") {
    return <RegisterView navigate={navigate} />;
  }

  if (pathname === "/profile") {
    return <ProfileView navigate={navigate} />;
  }

  if (pathname === "/achievements") {
    return <AchievementsView navigate={navigate} />;
  }

  if (pathname === "/dashboard") {
    return <DashboardView navigate={navigate} />;
  }

  if (pathname === "/analyze") {
    return <AnalyzeView navigate={navigate} />;
  }

  if (pathname === "/ai-tutor") {
    return <AiTutorView navigate={navigate} />;
  }

  if (pathname === "/lessons") {
    return <LessonsView navigate={navigate} />;
  }

  if (pathname.startsWith("/lessons/")) {
    const lessonId = Number(pathname.replace("/lessons/", ""));
    if (Number.isFinite(lessonId) && lessonId > 0) {
      return <LessonDetailView navigate={navigate} lessonId={lessonId} />;
    }
  }

  return <LandingPage navigate={navigate} />;
}

function LandingPage({ navigate }: { navigate: NavigateFn }) {
  return (
    <div className="app-shell app-shell-minimal">
      <MainNav
        navigate={navigate}
        authActions={(
          <>
            <button type="button" className="secondary-button site-auth-btn" onClick={() => navigate("/login")}>
              Sign in
            </button>
            <button type="button" className="site-auth-btn" onClick={() => navigate("/register")}>
              Get started
            </button>
          </>
        )}
      />

      <main className="minimal-home">
        <section className="minimal-home-card">
          <div className="eyebrow">
            <Sparkles className="icon-sm" />
            Minimal Home
          </div>
          <h1>One clean entry point for RepoRoverAI.</h1>
          <p>
            The home page is now intentionally minimal. Use dedicated routes for analysis, dashboards, lessons,
            achievements, and AI tutoring.
          </p>
          <div className="hero-actions">
            <button type="button" onClick={() => navigate("/analyze")}>
              Open Analyze <ArrowRight className="icon-sm" />
            </button>
            <button type="button" className="secondary-button" onClick={() => navigate("/dashboard")}>
              Open Dashboard
            </button>
          </div>
        </section>
      </main>
    </div>
  );
}

function LoginView({ navigate }: { navigate: NavigateFn }) {
  const query = new URLSearchParams(window.location.search);
  const registered = query.get("registered") === "true";
  const redirectUrl = query.get("redirect") || "/dashboard";
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [githubLoading, setGithubLoading] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    setError("Google sign-in is not enabled in the FastAPI auth bridge yet.");
    setGoogleLoading(false);
  };

  const handleGithubLogin = async () => {
    setGithubLoading(true);
    setError("GitHub sign-in is not enabled in the FastAPI auth bridge yet.");
    setGithubLoading(false);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await loginUser(email, password);
      localStorage.setItem("bearer_token", response.token);
      navigate(redirectUrl);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to sign in";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <section className="auth-card auth-modern-card">
        <div className="auth-brand">
          <Code2 className="icon-md" />
          <span>RepoRover AI</span>
        </div>
        <h1>Welcome back</h1>
        <p>Sign in to continue your learning and repository analysis flow.</p>
        {registered ? <div className="auth-note">Account created successfully. Sign in to continue.</div> : null}

        {!showEmailForm ? (
          <div className="auth-social-stack">
            <button type="button" className="auth-social-btn" onClick={handleGoogleLogin} disabled={googleLoading || githubLoading}>
              {googleLoading ? <Loader2 className="icon-sm spinning" /> : <Sparkles className="icon-sm" />} Continue with Google
            </button>

            <button type="button" className="auth-social-btn" onClick={handleGithubLogin} disabled={googleLoading || githubLoading}>
              {githubLoading ? <Loader2 className="icon-sm spinning" /> : <Github className="icon-sm" />} Continue with GitHub
            </button>

            <div className="auth-divider"><span>or</span></div>

            <button type="button" className="auth-social-btn" onClick={() => setShowEmailForm(true)}>
              <Mail className="icon-sm" /> Continue with Email
            </button>
          </div>
        ) : (
          <form className="auth-form" onSubmit={handleSubmit}>
            <label>
              Email
              <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="you@example.com" />
            </label>
            <label>
              Password
              <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="••••••••" />
            </label>
            <button type="submit" disabled={loading}>
              {loading ? <Loader2 className="icon-sm spin" /> : <Mail className="icon-sm" />} Sign in
            </button>

            <button type="button" className="secondary-button auth-back-btn" onClick={() => setShowEmailForm(false)} disabled={loading}>
              Back to social login
            </button>
          </form>
        )}

        {error ? <div className="error">{error}</div> : null}
        <div className="auth-links">
          <button type="button" className="secondary-button" onClick={() => navigate("/")}>Back home</button>
          <button type="button" className="secondary-button" onClick={() => navigate("/register")}>Create account</button>
        </div>
      </section>
    </div>
  );
}

function RegisterView({ navigate }: { navigate: NavigateFn }) {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [githubLoading, setGithubLoading] = useState(false);
  const [showEmailForm, setShowEmailForm] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleGoogleSignup = async () => {
    setGoogleLoading(true);
    setError("Google signup is not enabled in the FastAPI auth bridge yet.");
    setGoogleLoading(false);
  };

  const handleGithubSignup = async () => {
    setGithubLoading(true);
    setError("GitHub signup is not enabled in the FastAPI auth bridge yet.");
    setGithubLoading(false);
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();

    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await registerUser(name, email, password);
      localStorage.setItem("bearer_token", response.token);
      navigate("/profile");
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to register";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-shell">
      <section className="auth-card auth-modern-card">
        <div className="auth-brand">
          <Code2 className="icon-md" />
          <span>RepoRover AI</span>
        </div>
        <h1>Join RepoRover AI</h1>
        <p>Start your AI-powered learning journey in seconds.</p>

        {!showEmailForm ? (
          <div className="auth-social-stack">
            <button type="button" className="auth-social-btn" onClick={handleGoogleSignup} disabled={googleLoading || githubLoading}>
              {googleLoading ? <Loader2 className="icon-sm spinning" /> : <Sparkles className="icon-sm" />} Continue with Google
            </button>

            <button type="button" className="auth-social-btn" onClick={handleGithubSignup} disabled={googleLoading || githubLoading}>
              {githubLoading ? <Loader2 className="icon-sm spinning" /> : <Github className="icon-sm" />} Continue with GitHub
            </button>

            <div className="auth-divider"><span>or</span></div>

            <button type="button" className="auth-social-btn" onClick={() => setShowEmailForm(true)}>
              <Mail className="icon-sm" /> Continue with Email
            </button>
          </div>
        ) : (
          <form className="auth-form" onSubmit={handleSubmit}>
            <label>
              Full name
              <input value={name} onChange={(event) => setName(event.target.value)} type="text" placeholder="John Doe" />
            </label>
            <label>
              Email
              <input value={email} onChange={(event) => setEmail(event.target.value)} type="email" placeholder="you@example.com" />
            </label>
            <label>
              Password
              <input value={password} onChange={(event) => setPassword(event.target.value)} type="password" placeholder="••••••••" />
            </label>
            <label>
              Confirm password
              <input value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} type="password" placeholder="••••••••" />
            </label>
            <button type="submit" disabled={loading}>
              {loading ? <Loader2 className="icon-sm spin" /> : <User className="icon-sm" />} Create account
            </button>

            <button type="button" className="secondary-button auth-back-btn" onClick={() => setShowEmailForm(false)} disabled={loading}>
              Back to social login
            </button>
          </form>
        )}

        {error ? <div className="error">{error}</div> : null}
        <div className="auth-links">
          <button type="button" className="secondary-button" onClick={() => navigate("/")}>Back home</button>
          <button type="button" className="secondary-button" onClick={() => navigate("/login")}>Sign in</button>
        </div>
      </section>
    </div>
  );
}

function ProfileView({ navigate }: { navigate: NavigateFn }) {
  const [session, setSession] = useState<AuthUser | null>(null);
  const [stats, setStats] = useState({
    totalXp: 0,
    unlockedAchievements: 0,
    currentStreak: 0,
    longestStreak: 0,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadSession = async () => {
      const token = localStorage.getItem("bearer_token");
      if (!token) {
        navigate("/login");
        return;
      }

      try {
        const response = await fetchAuthSession(token);
        if (!response.user) {
          navigate("/login");
          return;
        }
        setSession(response.user);

        try {
          const [allAchievements, userAchievements] = await Promise.all([
            fetchAchievements(),
            fetchUserAchievements(token),
          ]);

          const unlockedIds = new Set(userAchievements.map((item) => item.achievement_id));
          const totalXp = allAchievements
            .filter((achievement) => unlockedIds.has(achievement.id))
            .reduce((sum, achievement) => sum + achievement.xp_reward, 0);

          setStats({
            totalXp,
            unlockedAchievements: userAchievements.length,
            currentStreak: Math.min(userAchievements.length, 7),
            longestStreak: Math.max(userAchievements.length, 0),
          });
        } catch {
          // Keep profile usable even if progress aggregation fails.
        }
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : "Unable to load profile";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, [navigate]);

  const handleSignOut = async () => {
    const token = localStorage.getItem("bearer_token");
    await logoutUser(token);
    localStorage.removeItem("bearer_token");
    navigate("/");
  };

  const getInitials = (name: string) =>
    name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);

  const currentLevel = Math.floor(stats.totalXp / 100) + 1;
  const xpProgress = stats.totalXp % 100;

  if (loading) {
    return (
      <div className="auth-shell">
        <section className="auth-card">Loading profile...</section>
      </div>
    );
  }

  return (
    <div className="app-shell">
      <MainNav navigate={navigate} />
      <main className="profile-shell">
        <section className="profile-header-card">
          <h1>Profile & Settings</h1>
          <p>View your account details and learning statistics.</p>
          {error ? <div className="error">{error}</div> : null}
        </section>

        <section className="profile-layout-grid">
          <article className="profile-main-card">
            <div className="profile-avatar">{getInitials(session?.name || "User")}</div>
            <h2>{session?.name || "User"}</h2>
            <p>Level {currentLevel} Developer</p>

            <div className="profile-detail-list">
              <div className="profile-detail-item">
                <Mail className="icon-sm" />
                <span>{session?.email || "No email available"}</span>
              </div>
              <div className="profile-detail-item">
                <Calendar className="icon-sm" />
                <span>Joined {session?.created_at ? new Date(session.created_at).toLocaleDateString() : "n/a"}</span>
              </div>
            </div>

            <div className="profile-xp-block">
              <div className="profile-xp-head">
                <span>Level {currentLevel}</span>
                <span>{xpProgress}/100 XP</span>
              </div>
              <div className="achievements-progress-track">
                <div className="achievements-progress-fill" style={{ width: `${xpProgress}%` }} />
              </div>
            </div>

            <div className="auth-links">
              <button type="button" className="secondary-button" onClick={() => navigate("/")}>Home</button>
              <button type="button" onClick={handleSignOut}>
                <LogOut className="icon-sm" /> Sign out
              </button>
            </div>
          </article>

          <div className="profile-side-stack">
            <section className="profile-stats-grid">
              <article className="profile-stat-card">
                <span>Total XP</span>
                <strong>{stats.totalXp}</strong>
              </article>
              <article className="profile-stat-card">
                <span>Achievements</span>
                <strong>{stats.unlockedAchievements}</strong>
              </article>
              <article className="profile-stat-card">
                <span>Current Streak</span>
                <strong>{stats.currentStreak}</strong>
              </article>
              <article className="profile-stat-card">
                <span>Longest Streak</span>
                <strong>{stats.longestStreak}</strong>
              </article>
            </section>

            <section className="profile-activity-card">
              <h3>
                <TrendingUp className="icon-sm" /> Learning Activity
              </h3>
              <div className="ai-tip-list">
                <p>
                  <Target className="icon-sm" /> Overall progress: {stats.unlockedAchievements} unlocked achievements
                </p>
                <p>
                  <Sparkles className="icon-sm" /> XP rate: {stats.unlockedAchievements > 0 ? Math.round(stats.totalXp / stats.unlockedAchievements) : 0} XP per achievement
                </p>
                <p>
                  <Trophy className="icon-sm" /> Milestone track: continue lessons to raise your level.
                </p>
              </div>
            </section>
          </div>
        </section>
      </main>
    </div>
  );
}

function AchievementsView({ navigate }: { navigate: NavigateFn }) {
  const [allAchievements, setAllAchievements] = useState<Achievement[]>([]);
  const [userAchievements, setUserAchievements] = useState<UserAchievement[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadAchievements = async () => {
      const token = localStorage.getItem("bearer_token");
      if (!token) {
        navigate("/login?redirect=/achievements");
        return;
      }

      try {
        const [all, user] = await Promise.all([fetchAchievements(), fetchUserAchievements(token)]);
        setAllAchievements(all);
        setUserAchievements(user);
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : "Unable to load achievements";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    loadAchievements();
  }, [navigate]);

  const isUnlocked = (achievementId: number) => userAchievements.some((ua) => ua.achievement_id === achievementId);
  const unlockedCount = userAchievements.length;
  const totalCount = allAchievements.length;
  const completionPercentage = totalCount > 0 ? (unlockedCount / totalCount) * 100 : 0;

  if (loading) {
    return <div className="auth-shell"><section className="auth-card">Loading achievements...</section></div>;
  }

  return (
    <div className="app-shell">
      <MainNav navigate={navigate} />

      <main className="achievements-shell">
        <section className="achievements-header-card">
          <h1>
            <Trophy className="icon-lg" /> Achievements
          </h1>
          <p>Unlock badges by completing lessons and reaching milestones.</p>
          {error ? <div className="error">{error}</div> : null}
        </section>

        <section className="achievements-progress-card">
          <div className="achievements-progress-head">
            <div>
              <h2>Your Progress</h2>
              <p>{unlockedCount} of {totalCount} achievements unlocked</p>
            </div>
            <span className="achievements-progress-badge">
              <Sparkles className="icon-sm" /> {Math.round(completionPercentage)}%
            </span>
          </div>
          <div className="achievements-progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(completionPercentage)}>
            <div className="achievements-progress-fill" style={{ width: `${completionPercentage}%` }} />
          </div>
        </section>

        <section className="achievements-grid">
          {allAchievements.map((achievement) => {
            const unlocked = isUnlocked(achievement.id);

            return (
              <article key={achievement.id} className={`achievement-card ${unlocked ? "achievement-card-unlocked" : "achievement-card-locked"}`}>
                <div className="achievement-card-head">
                  <span className="achievement-icon">{unlocked ? achievement.icon || "🏆" : "🔒"}</span>
                  <span className={`achievement-status-badge ${unlocked ? "unlocked" : "locked"}`}>
                    {unlocked ? <Award className="icon-sm" /> : <Lock className="icon-sm" />} {unlocked ? "Unlocked" : "Locked"}
                  </span>
                </div>
                <h3 className="achievement-title">{achievement.title}</h3>
                <p className="achievement-description">{achievement.description || "Achievement details are provided by the backend."}</p>
                <div className="achievement-footer">
                  <span className="achievement-reward">+{achievement.xp_reward} XP</span>
                  {achievement.requirement ? <span className="achievement-requirement">{achievement.requirement}</span> : null}
                </div>
              </article>
            );
          })}

          {!allAchievements.length ? (
            <div className="achievement-card learning-card-empty">
              <Award className="icon-lg" />
              <p>No achievements yet.</p>
            </div>
          ) : null}
        </section>
      </main>
    </div>
  );
}

function LessonsView({ navigate }: { navigate: NavigateFn }) {
  const [learningPaths, setLearningPaths] = useState<LearningPath[]>([]);
  const [lessons, setLessons] = useState<Record<number, Lesson[]>>({});
  const [expandedPath, setExpandedPath] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchLearningPaths();
        const sorted = [...data].sort((a, b) => a.order_index - b.order_index);
        setLearningPaths(sorted);
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : "Unable to load learning paths";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, []);

  const toggleLessons = async (pathId: number) => {
    if (lessons[pathId]) {
      setExpandedPath(expandedPath === pathId ? null : pathId);
      return;
    }

    try {
      const data = await fetchLessons(pathId);
      const normalized = Array.isArray(data) ? data : [data];
      setLessons((prev) => ({
        ...prev,
        [pathId]: normalized.sort((a, b) => a.order_index - b.order_index),
      }));
      setExpandedPath(pathId);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to load lessons";
      setError(message);
    }
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty.toLowerCase()) {
      case "beginner":
        return "bg-green-500/10 text-green-700";
      case "intermediate":
        return "bg-blue-500/10 text-blue-700";
      case "advanced":
        return "bg-purple-500/10 text-purple-700";
      default:
        return "bg-gray-500/10 text-gray-700";
    }
  };

  if (loading) {
    return <div className="auth-shell"><section className="auth-card">Loading lessons...</section></div>;
  }

  return (
    <div className="app-shell">
      <MainNav navigate={navigate} />

      <main className="lessons-shell">
        <section className="lessons-header-card">
          <h1>Learning Paths</h1>
          <p>
            Choose a learning path and start your coding journey. Each path contains structured lessons
            designed to move from beginner to expert.
          </p>
          {error ? <div className="error">{error}</div> : null}
        </section>

        <section className="lessons-paths-stack">
          {learningPaths.map((path) => (
            <article key={path.id} className="learning-path-card">
              <div className="learning-path-head">
                <div className="learning-path-main">
                  <div className="learning-path-icon">{path.icon || "📘"}</div>
                  <div className="learning-path-copy">
                    <h2>{path.title}</h2>
                    <p>{path.description || "Structured lessons are available for this path."}</p>
                    <div className="learning-path-meta">
                      <span className={`learning-difficulty ${getDifficultyColor(path.difficulty)}`}>{path.difficulty}</span>
                      <span className="learning-time">
                        <Clock className="icon-sm" /> {path.estimated_hours} hours
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="learning-path-actions">
                <button
                  type="button"
                  onClick={() => toggleLessons(path.id)}
                  className={expandedPath === path.id ? "secondary-button" : ""}
                >
                  {expandedPath === path.id ? "Hide Lessons" : "View Lessons"}
                  {expandedPath === path.id ? null : <ArrowRight className="icon-sm" />}
                </button>
              </div>

              {expandedPath === path.id && lessons[path.id] ? (
                <div className="lesson-stack">
                  <h3>Lessons in this path:</h3>
                  {lessons[path.id].map((lesson, index) => (
                    <article
                      key={lesson.id}
                      className="lesson-row-card"
                      role="button"
                      tabIndex={0}
                      onClick={() => navigate(`/lessons/${lesson.id}`)}
                      onKeyDown={(event) => {
                        if (event.key === "Enter" || event.key === " ") {
                          event.preventDefault();
                          navigate(`/lessons/${lesson.id}`);
                        }
                      }}
                    >
                      <div className="lesson-row-main">
                        <div className="lesson-index">{index + 1}</div>
                        <div className="lesson-row-copy">
                          <strong>{lesson.title}</strong>
                          <p>{lesson.description || "Lesson preview available in the backend."}</p>
                          <div className="lesson-row-meta">
                            <span>
                              <Clock className="icon-sm" /> {lesson.estimated_minutes} min
                            </span>
                            <span>
                              <Award className="icon-sm" /> {lesson.xp_reward} XP
                            </span>
                            <span className={`learning-difficulty ${getDifficultyColor(lesson.difficulty)}`}>
                              {lesson.difficulty}
                            </span>
                          </div>
                        </div>
                      </div>
                      <ArrowRight className="icon-sm lesson-row-arrow" />
                    </article>
                  ))}
                </div>
              ) : null}
            </article>
          ))}
        </section>
      </main>
    </div>
  );
}

function LessonDetailView({ navigate, lessonId }: { navigate: NavigateFn; lessonId: number }) {
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        const data = await fetchLesson(lessonId);
        setLesson(data);
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : "Unable to load lesson";
        setError(message);
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [lessonId]);

  if (loading) {
    return <div className="auth-shell"><section className="auth-card">Loading lesson...</section></div>;
  }

  return (
    <div className="app-shell">
      <MainNav navigate={navigate} />

      <main className="lesson-detail-shell">
        <section className="lesson-detail-hero">
          <button type="button" className="secondary-button lesson-back-button" onClick={() => navigate("/lessons")}>
            <ArrowRight className="icon-sm lesson-back-icon" /> Back to lessons
          </button>

          {error ? <div className="error">{error}</div> : null}

          {lesson ? (
            <>
              <h1>{lesson.title}</h1>
              <p>{lesson.description || "Lesson details from the FastAPI backend."}</p>
              <div className="lesson-detail-meta">
                <span className="learning-difficulty">{lesson.difficulty}</span>
                <span>
                  <Clock className="icon-sm" /> {lesson.estimated_minutes} min
                </span>
                <span>
                  <Award className="icon-sm" /> {lesson.xp_reward} XP
                </span>
              </div>
            </>
          ) : null}
        </section>

        <section className="lesson-detail-content-card">
          <h2>Lesson content</h2>
          {lesson ? (
            <p>{lesson.content || "Detailed lesson content will appear here as soon as it is provided by the backend."}</p>
          ) : (
            <p>No lesson data available.</p>
          )}
        </section>

        <section className="lesson-detail-content-card">
          <h2>How to use this lesson</h2>
          <ul className="lesson-detail-list">
            <li>Read the summary and estimated time first.</li>
            <li>Practice the concept in your local workspace.</li>
            <li>Return to the learning path and continue in order.</li>
          </ul>
        </section>
      </main>
    </div>
  );
}

function AnalyzeView({ navigate }: { navigate: NavigateFn }) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [projectName, setProjectName] = useState("");
  const [projectFiles, setProjectFiles] = useState<File[]>([]);
  const [loadingUpload, setLoadingUpload] = useState(false);
  const [loadingClone, setLoadingClone] = useState(false);
  const [loadingAnalyze, setLoadingAnalyze] = useState(false);
  const [loadingCodeAnalyze, setLoadingCodeAnalyze] = useState(false);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [loadingFlow, setLoadingFlow] = useState(false);
  const [loadingUnderstanding, setLoadingUnderstanding] = useState(false);
  const [loadingExplanation, setLoadingExplanation] = useState(false);
  const [loadingGaps, setLoadingGaps] = useState(false);
  const [loadingPriority, setLoadingPriority] = useState(false);
  const [loadingRisk, setLoadingRisk] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [payload, setPayload] = useState<ResultPayload>(null);
  const [analysisResult, setAnalysisResult] = useState<unknown>(null);
  const [savedWorkspace, setSavedWorkspace] = useState<SavedWorkspaceState | null>(() => readSavedWorkspaceState());

  useEffect(() => {
    if (!fileInputRef.current) {
      return;
    }

    fileInputRef.current.setAttribute("webkitdirectory", "");
    fileInputRef.current.setAttribute("directory", "");
  }, []);

  const persistWorkspace = (
    nextPayload: ResultPayload,
    nextAnalysis: unknown,
    lastAction: string,
    overrideProjectName?: string,
  ) => {
    const nextState: SavedWorkspaceState = {
      projectName: overrideProjectName ?? projectName,
      lastAction,
      payload: nextPayload,
      analysisResult: nextAnalysis,
      savedAt: new Date().toISOString(),
    };

    setSavedWorkspace(nextState);
    window.localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(nextState));
  };

  const formatApiError = (requestError: unknown, fallback: string): string => {
    if (axios.isAxiosError(requestError)) {
      const status = requestError.response?.status;
      const detail = requestError.response?.data?.detail;

      if (status === 404) {
        return "Project not found. Upload or clone a project first, then use its exact project name.";
      }

      if (typeof detail === "string" && detail.trim()) {
        return detail;
      }

      if (typeof detail === "object" && detail && typeof detail.detail === "string") {
        return detail.detail;
      }

      if (requestError.message) {
        return requestError.message;
      }
    }

    if (requestError instanceof Error && requestError.message) {
      return requestError.message;
    }

    return fallback;
  };

  const deriveProjectNameFromPath = (projectPath: string): string => {
    const normalized = projectPath.replace(/\\/g, "/").replace(/\/+$/, "");
    const parts = normalized.split("/").filter(Boolean);
    return parts.length ? parts[parts.length - 1] : "";
  };

  const projectNameFromPayload = (value: ResultPayload | SavedWorkspaceState["payload"]): string => {
    if (!value || typeof value !== "object") {
      return "";
    }

    if ("project_path" in value && typeof value.project_path === "string") {
      return deriveProjectNameFromPath(value.project_path);
    }

    return "";
  };

  const getEffectiveProjectName = (): string => {
    const direct = projectName.trim();
    if (direct) {
      return direct;
    }

    const fromPayload = projectNameFromPayload(payload);
    if (fromPayload) {
      return fromPayload;
    }

    if (savedWorkspace) {
      const fromSaved = savedWorkspace.projectName.trim();
      if (fromSaved) {
        return fromSaved;
      }

      const fromSavedPayload = projectNameFromPayload(savedWorkspace.payload);
      if (fromSavedPayload) {
        return fromSavedPayload;
      }
    }

    return "";
  };

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleUpload = async () => {
    if (!projectFiles.length) {
      setError("Choose a project folder before uploading.");
      return;
    }

    setLoadingUpload(true);
    setError(null);

    try {
      const response = await uploadProjectFiles(projectFiles);
      const nextProjectName = deriveProjectNameFromPath(response.project_path);
      if (nextProjectName) {
        setProjectName(nextProjectName);
      }
      setPayload(response);
      setAnalysisResult(null);
      persistWorkspace(response, null, "upload", nextProjectName);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to reach backend";
      setError(message);
    } finally {
      setLoadingUpload(false);
    }
  };

  const handleClone = async () => {
    if (!githubUrl.trim()) {
      setError("Enter a GitHub repository URL first.");
      return;
    }

    setLoadingClone(true);
    setError(null);

    try {
      const response = await cloneProjectFromGithub(githubUrl.trim());
      const nextProjectName = deriveProjectNameFromPath(response.project_path);
      if (nextProjectName) {
        setProjectName(nextProjectName);
      }
      setPayload(response);
      setAnalysisResult(null);
      persistWorkspace(response, null, "clone", nextProjectName);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Unable to reach backend";
      setError(message);
    } finally {
      setLoadingClone(false);
    }
  };

  const handleAnalyzeProject = async () => {
    setLoadingAnalyze(true);
    setError(null);

    try {
      let effectiveProjectName = getEffectiveProjectName();

      if (!effectiveProjectName && githubUrl.trim()) {
        const cloneResponse = await cloneProjectFromGithub(githubUrl.trim());
        const clonedProjectName = deriveProjectNameFromPath(cloneResponse.project_path);

        if (clonedProjectName) {
          setProjectName(clonedProjectName);
          setPayload(cloneResponse);
          persistWorkspace(cloneResponse, null, "clone", clonedProjectName);
          effectiveProjectName = clonedProjectName;
        }
      }

      if (!effectiveProjectName) {
        setError("Upload or clone a project first, then Analyze will run automatically.");
        return;
      }

      const response = await analyzeProjectByName(effectiveProjectName);
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }
      setPayload(response);
      setAnalysisResult(response);
      persistWorkspace(response, response, "project-analysis", effectiveProjectName);
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to analyze project");
      setError(message);
    } finally {
      setLoadingAnalyze(false);
    }
  };

  const analyzeCode = async () => {
    const effectiveProjectName = getEffectiveProjectName();
    if (!effectiveProjectName) {
      setError("Upload or clone a project first, then Analyze Code can run.");
      return;
    }

    setLoadingCodeAnalyze(true);
    setError(null);

    try {
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }
      const res = await axios.get(`http://127.0.0.1:8000/project/code-analysis/${encodeURIComponent(effectiveProjectName)}`);
      setAnalysisResult(res.data);
      persistWorkspace(payload, res.data, "code-analysis");
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to analyze code");
      setError(message);
    } finally {
      setLoadingCodeAnalyze(false);
    }
  };

  const getGraph = async () => {
    const effectiveProjectName = getEffectiveProjectName();
    if (!effectiveProjectName) {
      setError("Upload or clone a project first, then Build Graph can run.");
      return;
    }

    setLoadingGraph(true);
    setError(null);

    try {
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }
      const res = await axios.get(`http://127.0.0.1:8000/project/graph/${encodeURIComponent(effectiveProjectName)}`);
      console.log("📊 Graph Data with Call Relationships:", res.data);
      
      // Enhance the display with insights
      const graphData = {
        ...res.data,
        insights: {
          description: "Function call graph showing execution relationships",
          total_call_paths: res.data.call_edges || 0,
          node_types: {
            functions: "Analyzable code functions",
            called_by_count: "How many times a function is called"
          }
        }
      };
      
      setAnalysisResult(graphData);
      persistWorkspace(payload, graphData, "graph");
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to build graph");
      setError(message);
    } finally {
      setLoadingGraph(false);
    }
  };

  const getFlow = async () => {
    const effectiveProjectName = getEffectiveProjectName();
    if (!effectiveProjectName) {
      setError("Upload or clone a project first, then Flow Test can run.");
      return;
    }

    setLoadingFlow(true);
    setError(null);

    try {
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }
      const res = await fetchProjectFlow(effectiveProjectName);
      console.log("Execution flow:", res);
      setAnalysisResult(res);
      persistWorkspace(res, res, "flow");
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to trace execution flow");
      setError(message);
    } finally {
      setLoadingFlow(false);
    }
  };

  const getUnderstanding = async () => {
    const effectiveProjectName = getEffectiveProjectName();
    if (!effectiveProjectName) {
      setError("Upload or clone a project first, then Understanding Test can run.");
      return;
    }

    setLoadingUnderstanding(true);
    setError(null);

    try {
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }
      const res = await axios.get(`http://127.0.0.1:8000/project/understand/${encodeURIComponent(effectiveProjectName)}`);
      console.log(res.data);
      setAnalysisResult(res.data);
      persistWorkspace(payload, res.data, "understanding");
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to understand project");
      setError(message);
    } finally {
      setLoadingUnderstanding(false);
    }
  };

  const getAIExplanation = async () => {
    const effectiveProjectName = getEffectiveProjectName();
    if (!effectiveProjectName) {
      setError("Upload or clone a project first, then AI Explanation can run.");
      return;
    }

    setLoadingExplanation(true);
    setError(null);

    try {
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }
      const res = await axios.get(`http://127.0.0.1:8000/project/understand/${encodeURIComponent(effectiveProjectName)}`);
      console.log(res.data.summary);
      console.log(res.data.explanations);
      const aiExplanationPayload = {
        summary: res.data.summary,
        explanations: res.data.explanations,
      };
      setAnalysisResult(aiExplanationPayload);
      persistWorkspace(payload, aiExplanationPayload, "ai-explanations");
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to fetch explanations");
      setError(message);
    } finally {
      setLoadingExplanation(false);
    }
  };

  const getGaps = async () => {
    const effectiveProjectName = getEffectiveProjectName();
    if (!effectiveProjectName) {
      setError("Upload or clone a project first, then Get Gaps can run.");
      return;
    }

    setLoadingGaps(true);
    setError(null);

    try {
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }

      const res = await fetchProjectGaps(effectiveProjectName);
      setAnalysisResult(res);
      persistWorkspace(payload, res, "gaps", effectiveProjectName);
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to detect design gaps");
      setError(message);
    } finally {
      setLoadingGaps(false);
    }
  };

  const getRisk = async () => {
    const effectiveProjectName = getEffectiveProjectName();
    if (!effectiveProjectName) {
      setError("Upload or clone a project first, then Risk Analysis can run.");
      return;
    }

    setLoadingRisk(true);
    setError(null);

    try {
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }

      const res = await fetchProjectRisk(effectiveProjectName);
      setAnalysisResult(res);
      persistWorkspace(payload, res, "risk", effectiveProjectName);
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to analyze risk");
      setError(message);
    } finally {
      setLoadingRisk(false);
    }
  };

  const getPriority = async () => {
    const effectiveProjectName = getEffectiveProjectName();
    if (!effectiveProjectName) {
      setError("Upload or clone a project first, then Priority Analysis can run.");
      return;
    }

    setLoadingPriority(true);
    setError(null);

    try {
      if (!projectName.trim()) {
        setProjectName(effectiveProjectName);
      }

      const res = await fetchProjectPriority(effectiveProjectName);
      console.log(res);
      setAnalysisResult(res);
      persistWorkspace(payload, res, "priority", effectiveProjectName);
    } catch (requestError) {
      const message = formatApiError(requestError, "Unable to calculate priority");
      setError(message);
    } finally {
      setLoadingPriority(false);
    }
  };

  const payloadPreview = analysisResult ?? payload;

  const filesScanned =
    typeof savedWorkspace?.payload === "object" &&
    savedWorkspace.payload !== null &&
    "total_files" in savedWorkspace.payload
      ? Number((savedWorkspace.payload as ProjectAnalyzeResponse).total_files)
      : typeof savedWorkspace?.payload === "object" &&
          savedWorkspace.payload !== null &&
          "files_saved" in savedWorkspace.payload
        ? Number((savedWorkspace.payload as ProjectUploadResponse).files_saved)
        : 0;

  const getPriorityLevel = (score: number): "High" | "Medium" | "Low" => {
    if (score >= 8) {
      return "High";
    }
    if (score >= 5) {
      return "Medium";
    }
    return "Low";
  };

  const getPriorityClassName = (score: number): string => {
    const level = getPriorityLevel(score);
    if (level === "High") {
      return "priority-pill priority-high";
    }
    if (level === "Medium") {
      return "priority-pill priority-medium";
    }
    return "priority-pill priority-low";
  };

  const renderResultsPanel = () => {
    if (!payloadPreview) {
      return (
        <div className="empty-state">
          <Sparkles className="icon-lg" />
          <p>No results yet. Run an action from the controls panel.</p>
        </div>
      );
    }

    if (Array.isArray(payloadPreview)) {
      return (
        <div className="dashboard-summary-stack">
          <p>Code analysis returned {payloadPreview.length} file summaries.</p>
          {payloadPreview.slice(0, 8).map((item, index) => {
            const entry = item as Record<string, unknown>;
            const fileName = typeof entry.file === "string" ? entry.file : `file-${index + 1}`;
            return (
              <div key={`${fileName}-${index}`} className="dashboard-detail-row">
                <strong>{index + 1}.</strong>
                <span>{fileName}</span>
              </div>
            );
          })}
        </div>
      );
    }

    const panelData = payloadPreview as Record<string, unknown>;

    if ("graph" in panelData && panelData.graph && typeof panelData.graph === "object") {
      const effectiveProjectName = getEffectiveProjectName();
      const rawGraphData = panelData.graph as {
        nodes?: Array<{ id: string; node_type: string; label: string; file_path?: string | null }>;
        edges?: Array<{ source: string; target: string; edge_type: string }>;
        summary?: Record<string, unknown>;
      };

      if (Array.isArray(rawGraphData.nodes) && Array.isArray(rawGraphData.edges)) {
        const graphData = {
          nodes: rawGraphData.nodes,
          edges: rawGraphData.edges,
          summary: rawGraphData.summary,
        };

        return (
          <div className="dashboard-summary-stack">
            <div className="analyze-signal-grid">
              <AnalyzeStatTile icon={GitBranch} label="Nodes" value={String(graphData.nodes.length)} />
              <AnalyzeStatTile icon={Route} label="Edges" value={String(graphData.edges.length)} />
              <AnalyzeStatTile icon={FolderOpen} label="Files" value={String(graphData.summary?.file_nodes ?? 0)} />
              <AnalyzeStatTile icon={Code2} label="Functions" value={String(graphData.summary?.function_nodes ?? 0)} />
            </div>

            <section className="dashboard-summary-stack">
              <h1>Project Visualization</h1>
              <GraphView projectName={effectiveProjectName || null} title="Interactive Graph" />
            </section>
          </div>
        );
      }
    }

    if ("language" in panelData && "total_files" in panelData && Array.isArray(panelData.files)) {
      const files = panelData.files as Array<Record<string, unknown>>;
      const scanned = typeof panelData.total_files_scanned === "number" ? panelData.total_files_scanned : panelData.total_files;

      return (
        <div className="dashboard-summary-stack">
          <div className="analyze-signal-grid">
            <AnalyzeStatTile icon={Code2} label="Language" value={String(panelData.language)} />
            <AnalyzeStatTile icon={FileText} label="Code files" value={String(panelData.total_files)} />
            <AnalyzeStatTile icon={FolderOpen} label="Files scanned" value={String(scanned)} />
            <AnalyzeStatTile icon={Sparkles} label="Preview" value={`${Math.min(files.length, 8)} shown`} />
          </div>
          {files.slice(0, 8).map((file, index) => (
            <div key={`${String(file.path)}-${index}`} className="dashboard-detail-row">
              <strong>{String(file.extension || "-")}</strong>
              <span>{String(file.path || file.name || "unknown file")}</span>
            </div>
          ))}
        </div>
      );
    }

    if ("total_nodes" in panelData && "total_edges" in panelData) {
      return (
        <div className="analyze-signal-grid">
          <AnalyzeStatTile icon={GitBranch} label="Nodes" value={String(panelData.total_nodes)} />
          <AnalyzeStatTile icon={Route} label="Edges" value={String(panelData.total_edges)} />
          <AnalyzeStatTile icon={Code2} label="Call edges" value={String(panelData.call_edges ?? 0)} />
          <AnalyzeStatTile icon={FileText} label="Import edges" value={String(panelData.import_edges ?? 0)} />
        </div>
      );
    }

    if ("execution_flow" in panelData && Array.isArray(panelData.execution_flow)) {
      const flow = panelData.execution_flow as string[];
      return (
        <div className="dashboard-summary-stack">
          <div className="analyze-signal-grid analyze-signal-grid-3">
            <AnalyzeStatTile icon={Route} label="Steps" value={String(flow.length)} />
            <AnalyzeStatTile icon={GitBranch} label="Path" value={flow.length ? "Ready" : "Empty"} />
            <AnalyzeStatTile icon={Sparkles} label="Mode" value="Execution flow" />
          </div>

          <GraphVisualizer
            title="Execution Flow"
            description="Sequential path rendered as an interactive flow diagram."
            flowPath={flow}
          />
        </div>
      );
    }

    if ("summary" in panelData && "explanations" in panelData) {
      const explanations = (panelData.explanations || {}) as Record<string, unknown>;
      return (
        <div className="dashboard-summary-stack">
          <p>{String(panelData.summary || "No summary available")}</p>
          {typeof explanations.beginner === "string" ? <p><strong>Beginner:</strong> {explanations.beginner}</p> : null}
          {typeof explanations.intermediate === "string" ? <p><strong>Intermediate:</strong> {explanations.intermediate}</p> : null}
          {typeof explanations.advanced === "string" ? <p><strong>Advanced:</strong> {explanations.advanced}</p> : null}
        </div>
      );
    }

    if ("gaps" in panelData && Array.isArray(panelData.gaps)) {
      const gaps = panelData.gaps as Array<Record<string, unknown>>;
      const high = gaps.filter((gap) => String(gap.severity || "").toLowerCase() === "high").length;
      const medium = gaps.filter((gap) => String(gap.severity || "").toLowerCase() === "medium").length;
      const low = gaps.filter((gap) => String(gap.severity || "").toLowerCase() === "low").length;

      return (
        <div className="dashboard-summary-stack">
          <div className="analyze-signal-grid analyze-signal-grid-3">
            <AnalyzeStatTile icon={TriangleAlert} label="High" value={String(high)} />
            <AnalyzeStatTile icon={Activity} label="Medium" value={String(medium)} />
            <AnalyzeStatTile icon={FileText} label="Low" value={String(low)} />
          </div>

          {gaps.length ? (
            gaps.slice(0, 12).map((gap, index) => (
              <div key={`${String(gap.file)}-${index}`} className="dashboard-detail-row">
                <strong>{String(gap.severity || "unknown")}</strong>
                <span>{String(gap.file || "unknown file")}: {String(gap.issue || "No issue text")}</span>
              </div>
            ))
          ) : (
            <p>No design gaps detected.</p>
          )}
        </div>
      );
    }

    if ("risks" in panelData && Array.isArray(panelData.risks)) {
      const risks = panelData.risks as Array<Record<string, unknown>>;
      const high = risks.filter((risk) => Number(risk.score || 0) >= 8).length;
      const medium = risks.filter((risk) => Number(risk.score || 0) >= 5 && Number(risk.score || 0) < 8).length;
      const low = risks.filter((risk) => Number(risk.score || 0) < 5).length;

      return (
        <div className="dashboard-summary-stack">
          <div className="analyze-signal-grid analyze-signal-grid-3">
            <AnalyzeStatTile icon={TriangleAlert} label="High" value={String(high)} />
            <AnalyzeStatTile icon={Activity} label="Medium" value={String(medium)} />
            <AnalyzeStatTile icon={FileText} label="Low" value={String(low)} />
          </div>

          {risks.slice(0, 12).map((risk, index) => {
            const label = String(risk.file || risk.node || `risk-${index + 1}`);
            return (
              <div key={`${label}-${index}`} className="dashboard-detail-row">
                <strong>{String(risk.score ?? 0)}</strong>
                <span>{label}: {String(risk.risk || "Risk")}</span>
              </div>
            );
          })}
        </div>
      );
    }

    if ("top_risks" in panelData && Array.isArray(panelData.top_risks) && "important_functions" in panelData && Array.isArray(panelData.important_functions)) {
      const topRisks = panelData.top_risks as Array<Record<string, unknown>>;
      const importantFunctions = panelData.important_functions as Array<unknown>;

      return (
        <div className="dashboard-summary-stack">
          <div className="analyze-signal-grid analyze-signal-grid-3">
            <AnalyzeStatTile icon={Target} label="Top risks" value={String(topRisks.length)} />
            <AnalyzeStatTile icon={TrendingUp} label="Important functions" value={String(importantFunctions.length)} />
            <AnalyzeStatTile icon={Sparkles} label="Mode" value="Priority" />
          </div>

          <h3>Top Risks</h3>
          {topRisks.length ? (
            topRisks.slice(0, 5).map((risk, index) => {
              const score = Number(risk.score || 0);
              const label = String(risk.file || `risk-${index + 1}`);
              return (
                <div key={`${label}-${index}`} className="dashboard-detail-row">
                  <strong>{score.toFixed(2)}</strong>
                  <span>{label}: {String(risk.risk || "Risk signal")}</span>
                  <span className={getPriorityClassName(score)}>{getPriorityLevel(score)}</span>
                </div>
              );
            })
          ) : (
            <p>No priority risks found.</p>
          )}

          <h3>Important Functions</h3>
          {importantFunctions.length ? (
            importantFunctions.slice(0, 5).map((entry, index) => {
              const tuple = Array.isArray(entry) ? entry : [];
              const functionName = String(tuple[0] || `function-${index + 1}`);
              const centralityScore = Number(tuple[1] || 0);

              return (
                <div key={`${functionName}-${index}`} className="dashboard-detail-row">
                  <strong>{centralityScore.toFixed(4)}</strong>
                  <span>{functionName}</span>
                </div>
              );
            })
          ) : (
            <p>No important functions found.</p>
          )}
        </div>
      );
    }

    return (
      <div className="dashboard-summary-stack">
        <p>Showing raw response because this action returned a custom payload shape.</p>
      </div>
    );
  };

  return (
    <div className="app-shell">
      <MainNav navigate={navigate} />

      <main className="analyze-shell">
        <section className="analyze-hero-grid">
          <article className="analyze-hero-card">
            <div className="eyebrow">
              <Sparkles className="icon-sm" /> FastAPI analysis workspace
            </div>
            <h1>Repository intelligence, rendered live.</h1>
            <p>
              Point the app at a local project path and the backend returns project summaries, quality findings,
              graph analytics, explainability traces, and Mermaid-ready flow paths.
            </p>
            <div className="hero-actions">
              <a className="primary-link" href="#analyze-controls">
                Open controls <ArrowRight className="icon-sm" />
              </a>
              <button type="button" className="secondary-link analyze-link-button" onClick={() => navigate("/")}>
                Open dashboard
              </button>
            </div>
          </article>

          <div className="analyze-signal-stack">
            <article className="analyze-signal-card">
              <h2>Backend signals</h2>
              <p>Metrics returned by the FastAPI analysis pipeline.</p>
              <div className="analyze-signal-grid">
                <AnalyzeStatTile icon={ChartColumnBig} label="Files" value={filesScanned} />
                <AnalyzeStatTile icon={GitBranch} label="Graph nodes" value={0} />
                <AnalyzeStatTile icon={TriangleAlert} label="Risk score" value={0} />
                <AnalyzeStatTile icon={Brain} label="Reliability" value={0} />
              </div>
            </article>

            <article className="analyze-signal-card">
              <h2>Explainability coverage</h2>
              <p>Trace counts tied back to tokens, AST nodes, and graph paths.</p>
              <div className="analyze-signal-grid analyze-signal-grid-3">
                <AnalyzeStatTile icon={Code2} label="Tokens" value={0} />
                <AnalyzeStatTile icon={FileText} label="AST nodes" value={0} />
                <AnalyzeStatTile icon={Route} label="Paths" value={0} />
              </div>
            </article>
          </div>
        </section>

        <section id="analyze-controls" className="analyze-block-grid">
          <article className="analyze-block-card">
            <div className="section-heading">
              <h2>
                <Activity className="icon-sm" /> Analysis controls
              </h2>
              <p>Upload a folder, clone from GitHub, or analyze a saved project by name.</p>
            </div>

            <div className="form-row">
              <label htmlFor="analyze-github-url">GitHub URL</label>
              <input
                id="analyze-github-url"
                type="url"
                placeholder="https://github.com/owner/repo"
                value={githubUrl}
                onChange={(event) => setGithubUrl(event.target.value)}
              />
            </div>

            <div className="form-row">
              <label htmlFor="analyze-project-name">Project Name</label>
              <input
                id="analyze-project-name"
                type="text"
                placeholder="upload-project-20260403123456-ab12cd34"
                value={projectName}
                onChange={(event) => setProjectName(event.target.value)}
              />
            </div>

            <div className="upload-card">
              <input
                ref={fileInputRef}
                id="analyze-project-file"
                type="file"
                className="hidden-file-input"
                multiple
                onChange={(event) => setProjectFiles(Array.from(event.target.files ?? []))}
              />

              <button type="button" className="upload-picker" onClick={openFilePicker}>
                <span className="upload-plus" aria-hidden="true">
                  +
                </span>
                <span>{projectFiles.length ? "Change project folder" : "Choose project folder"}</span>
              </button>

              <p className="file-selection">
                {projectFiles.length ? `Selected files: ${projectFiles.length}` : "No folder selected yet"}
              </p>
            </div>

            <div className="action-row">
              <button onClick={handleUpload} disabled={loadingUpload}>
                {loadingUpload ? <Loader2 className="icon-sm spinning" /> : <FolderOpen className="icon-sm" />} Upload
              </button>
              <button onClick={handleClone} disabled={loadingClone}>
                {loadingClone ? <Loader2 className="icon-sm spinning" /> : <GitBranch className="icon-sm" />} Clone
              </button>
              <button onClick={handleAnalyzeProject} disabled={loadingAnalyze}>
                {loadingAnalyze ? <Loader2 className="icon-sm spinning" /> : <Sparkles className="icon-sm" />} Analyze
              </button>
              <button onClick={analyzeCode} disabled={loadingCodeAnalyze} className="secondary-button">
                {loadingCodeAnalyze ? <Loader2 className="icon-sm spinning" /> : <Code2 className="icon-sm" />} Code analysis
              </button>
              <button onClick={getGraph} disabled={loadingGraph} className="secondary-button">
                {loadingGraph ? <Loader2 className="icon-sm spinning" /> : <Route className="icon-sm" />} Build Graph
              </button>
              <button onClick={getFlow} disabled={loadingFlow} className="secondary-button">
                {loadingFlow ? <Loader2 className="icon-sm spinning" /> : <Route className="icon-sm" />} Flow Test
              </button>
              <button onClick={getUnderstanding} disabled={loadingUnderstanding} className="secondary-button">
                {loadingUnderstanding ? <Loader2 className="icon-sm spinning" /> : <Brain className="icon-sm" />} Understanding Test
              </button>
              <button onClick={getAIExplanation} disabled={loadingExplanation} className="secondary-button">
                {loadingExplanation ? <Loader2 className="icon-sm spinning" /> : <BookOpen className="icon-sm" />} AI Explanation Test
              </button>
              <button onClick={getGaps} disabled={loadingGaps} className="secondary-button">
                {loadingGaps ? <Loader2 className="icon-sm spinning" /> : <TriangleAlert className="icon-sm" />} Get Gaps
              </button>
              <button onClick={getRisk} disabled={loadingRisk} className="secondary-button">
                {loadingRisk ? <Loader2 className="icon-sm spinning" /> : <Target className="icon-sm" />} Risk Analysis
              </button>
              <button onClick={getPriority} disabled={loadingPriority} className="secondary-button">
                {loadingPriority ? <Loader2 className="icon-sm spinning" /> : <TrendingUp className="icon-sm" />} Priority Engine
              </button>
            </div>

            {error ? <div className="error">{error}</div> : null}
          </article>
          <article className="analyze-block-card">
            <div className="section-heading">
              <h2>
                <BarChart3 className="icon-sm" /> Results panel
              </h2>
              <p>Visualized analysis output with optional raw payload details.</p>
            </div>

            <div className="result-card">
              {renderResultsPanel()}
              {payloadPreview ? (
                <details style={{ marginTop: "1rem" }}>
                  <summary>Raw JSON details</summary>
                  <pre>{JSON.stringify(payloadPreview, null, 2)}</pre>
                </details>
              ) : null}
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}

function AnalyzeStatTile({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
}) {
  return (
    <div className="analyze-stat-tile">
      <div className="analyze-stat-label">
        <Icon className="icon-sm" />
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
    </div>
  );
}

function DashboardView({ navigate }: { navigate: NavigateFn }) {
  const [savedWorkspace] = useState<SavedWorkspaceState | null>(() => readSavedWorkspaceState());

  const workspaceSummary = useMemo(() => {
    const latest = savedWorkspace ?? {
      projectName: "",
      lastAction: "none",
      payload: null,
      analysisResult: null,
      savedAt: null as string | null,
    };

    const totalFiles =
      typeof latest.payload === "object" && latest.payload !== null && "total_files" in latest.payload
        ? Number((latest.payload as ProjectAnalyzeResponse).total_files)
        : typeof latest.payload === "object" && latest.payload !== null && "files_saved" in latest.payload
          ? Number((latest.payload as ProjectUploadResponse).files_saved)
          : 0;

    return {
      ...latest,
      totalFiles,
    };
  }, [savedWorkspace]);

  const [dashboardData, setDashboardData] = useState<Record<string, unknown> | null>(null);
  const [dashboardRisks, setDashboardRisks] = useState<Array<Record<string, unknown>>>([]);
  const [priority, setPriority] = useState<Record<string, unknown> | null>(null);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);

  const dashboardProjectName = workspaceSummary.projectName || "your_project_name";

  useEffect(() => {
    let isMounted = true;

    const loadDashboard = async () => {
      setDashboardLoading(true);
      setDashboardError(null);

      try {
        const [understandRes, riskRes, priorityRes] = await Promise.all([
          axios.get(`http://127.0.0.1:8000/project/understand/${encodeURIComponent(dashboardProjectName)}`),
          axios.get(`http://127.0.0.1:8000/project/risk/${encodeURIComponent(dashboardProjectName)}`),
          axios.get(`http://127.0.0.1:8000/project/priority/${encodeURIComponent(dashboardProjectName)}`),
        ]);

        if (!isMounted) {
          return;
        }

        const understandData =
          understandRes.data && typeof understandRes.data === "object"
            ? (understandRes.data as Record<string, unknown>)
            : null;
        const riskData =
          riskRes.data && typeof riskRes.data === "object"
            ? (riskRes.data as Record<string, unknown>)
            : null;
        const priorityData =
          priorityRes.data && typeof priorityRes.data === "object"
            ? (priorityRes.data as Record<string, unknown>)
            : null;

        setDashboardData(understandData);
        setDashboardRisks(Array.isArray(riskData?.risks) ? (riskData?.risks as Array<Record<string, unknown>>) : []);
        setPriority(priorityData);
      } catch (requestError) {
        if (!isMounted) {
          return;
        }

        const message = axios.isAxiosError(requestError)
          ? requestError.response?.data?.detail || requestError.message || "Unable to load dashboard"
          : requestError instanceof Error
            ? requestError.message
            : "Unable to load dashboard";
        setDashboardError(String(message));
      } finally {
        if (isMounted) {
          setDashboardLoading(false);
        }
      }
    };

    void loadDashboard();
    return () => {
      isMounted = false;
    };
  }, [dashboardProjectName]);

  const dashboardSummary = typeof dashboardData?.summary === "string" ? dashboardData.summary : null;
  const dashboardExplanations =
    dashboardData && typeof dashboardData.explanations === "object" && dashboardData.explanations !== null
      ? (dashboardData.explanations as Record<string, unknown>)
      : null;

  const priorityTopRisks =
    priority && Array.isArray(priority.top_risks)
      ? (priority.top_risks as Array<Record<string, unknown>>)
      : [];

  const priorityImportantFunctions =
    priority && Array.isArray(priority.important_functions)
      ? (priority.important_functions as Array<unknown>)
      : [];

  const getRiskLevel = (score: number): "High" | "Medium" | "Low" => {
    if (score >= 8) {
      return "High";
    }
    if (score >= 5) {
      return "Medium";
    }
    return "Low";
  };

  const getRiskBadgeClass = (score: number): string => {
    const level = getRiskLevel(score);
    if (level === "High") {
      return "priority-pill priority-high";
    }
    if (level === "Medium") {
      return "priority-pill priority-medium";
    }
    return "priority-pill priority-low";
  };

  const analysis =
    workspaceSummary.analysisResult && typeof workspaceSummary.analysisResult === "object"
      ? (workspaceSummary.analysisResult as Record<string, unknown>)
      : null;

  const metrics =
    analysis && typeof analysis.metrics === "object" && analysis.metrics !== null
      ? (analysis.metrics as Record<string, unknown>)
      : null;

  const severity =
    analysis && typeof analysis.severity_distribution === "object" && analysis.severity_distribution !== null
      ? (analysis.severity_distribution as Record<string, unknown>)
      : null;

  const toNumber = (value: unknown) => (typeof value === "number" && Number.isFinite(value) ? value : 0);

  const graphType = typeof analysis?.graph_type === "string" ? analysis.graph_type : "n/a";
  const riskScore = typeof analysis?.risk_score === "number" ? analysis.risk_score : 0;
  const reliabilityScore = typeof analysis?.reliability_score === "number" ? analysis.reliability_score : 0;

  const footprint = [
    { label: "Files", value: workspaceSummary.totalFiles || toNumber(metrics?.files_scanned) },
    { label: "Lines", value: toNumber(metrics?.total_lines) },
    { label: "Dependency edges", value: toNumber(metrics?.dependency_edges) },
    { label: "Call edges", value: toNumber(metrics?.call_edges) },
  ];

  const maxFootprint = Math.max(...footprint.map((item) => item.value), 1);

  const severityMix = [
    { label: "High", value: toNumber(severity?.high), tone: "high" },
    { label: "Medium", value: toNumber(severity?.medium), tone: "medium" },
    { label: "Low", value: toNumber(severity?.low), tone: "low" },
  ];

  const flowPath =
    analysis && Array.isArray(analysis.flow_path)
      ? (analysis.flow_path.filter((node): node is string => typeof node === "string") as string[])
      : [];

  const projectSummary = typeof analysis?.project_summary === "string" ? analysis.project_summary : null;
  const architectureSummary = typeof analysis?.architecture_summary === "string" ? analysis.architecture_summary : null;
  const executionSummary =
    typeof analysis?.execution_flow_summary === "string" ? analysis.execution_flow_summary : null;

  return (
    <div className="app-shell">
      <MainNav navigate={navigate} />

      <main className="dashboard-shell">
        <section className="dashboard-hero-card">
          <div className="dashboard-badge">
            <LayoutDashboard className="icon-sm" /> Analysis dashboard
          </div>
          <h1>Backend results at a glance.</h1>
          <p>
            The dashboard reads the last analysis saved by the analyzer workspace and turns FastAPI outputs
            into summary cards and visual diagnostics.
          </p>
          <div className="dashboard-hero-actions">
            <button type="button" onClick={() => navigate("/analyze")}>
              Open analyzer <ArrowRight className="icon-sm" />
            </button>
            <button type="button" className="secondary-button" onClick={() => navigate("/")}>
              Open home
            </button>
          </div>
        </section>

        <section className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Workspace signals</span>
            <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2">
              <DashboardMetricTile icon={Activity} label="Loaded" value={savedWorkspace ? "Yes" : "No"} />
              <DashboardMetricTile icon={GitBranch} label="Graph type" value={graphType} />
              <DashboardMetricTile icon={TriangleAlert} label="Risk" value={riskScore} />
              <DashboardMetricTile icon={Sparkles} label="Reliability" value={reliabilityScore} />
            </div>
          </article>

          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Snapshot details</span>
            <div className="mt-3 grid gap-2">
              <div className="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm">
                <strong>Project name</strong>
                <span>{workspaceSummary.projectName || "n/a"}</span>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm">
                <strong>File count</strong>
                <span>{workspaceSummary.totalFiles}</span>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm">
                <strong>Last action</strong>
                <span>{workspaceSummary.lastAction || "none"}</span>
              </div>
              <div className="flex items-center justify-between gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm">
                <strong>Saved at</strong>
                <span>{workspaceSummary.savedAt ? new Date(workspaceSummary.savedAt).toLocaleString() : "n/a"}</span>
              </div>
            </div>
          </article>
        </section>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Project dashboard</span>
            {dashboardLoading ? (
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">Loading...</p>
            ) : (
              <div className="space-y-3">
                {dashboardError ? <div className="rounded-md border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">{dashboardError}</div> : null}

                <h2 className="mb-2 text-lg font-semibold text-slate-900">Summary</h2>
                <p className="text-sm leading-6 text-slate-700">{dashboardSummary ?? "No summary available."}</p>

                <h2 className="mb-2 text-lg font-semibold text-slate-900">Explanations</h2>
                <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-800"><span className="font-semibold text-slate-900">Beginner:</span> {String(dashboardExplanations?.beginner || "n/a")}</p>
                <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-800"><span className="font-semibold text-slate-900">Intermediate:</span> {String(dashboardExplanations?.intermediate || "n/a")}</p>
                <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-800"><span className="font-semibold text-slate-900">Advanced:</span> {String(dashboardExplanations?.advanced || "n/a")}</p>
              </div>
            )}
          </article>

          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Risks</span>
            {dashboardLoading ? (
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">Loading...</p>
            ) : dashboardRisks.length ? (
              <div className="space-y-2">
                {dashboardRisks.slice(0, 12).map((risk, index) => {
                  const score = Number(risk.score || 0);
                  const label = String(risk.file || risk.node || `risk-${index + 1}`);
                  return (
                    <div key={`${label}-${index}`} className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-800">
                      <strong className="mr-2">{score.toFixed(2)}</strong>
                      <span>{label} - {String(risk.risk || "Risk")}</span>
                      <span className={`${getRiskBadgeClass(score)} ml-2`}>{getRiskLevel(score)}</span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">No risk items available.</p>
            )}
          </article>
        </section>

        <section className="grid grid-cols-1 gap-4">
          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Graph</span>
            <GraphView projectName={dashboardProjectName} title="Project Graph" />
          </article>
        </section>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Priority panel</span>
            {dashboardLoading ? (
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">Loading...</p>
            ) : (
              <>
                <h2 className="mb-3 text-lg font-semibold text-slate-900">Top Risks</h2>
                <ul className="space-y-2">
                  {priorityTopRisks.length ? (
                    priorityTopRisks.slice(0, 5).map((risk, index) => {
                      const score = Number(risk.score || 0);
                      return (
                        <li key={`priority-risk-${index}`} className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-800">
                          {String(risk.file || "unknown")} - {String(risk.risk || "Risk signal")}
                          <span className={`${getRiskBadgeClass(score)} ml-2`}>{getRiskLevel(score)}</span>
                        </li>
                      );
                    })
                  ) : (
                    <li className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">No priority risk data available.</li>
                  )}
                </ul>
              </>
            )}
          </article>

          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Function importance</span>
            {dashboardLoading ? (
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">Loading...</p>
            ) : (
              <>
                <h2 className="mb-3 text-lg font-semibold text-slate-900">Important Functions</h2>
                <ul className="space-y-2">
                  {priorityImportantFunctions.length ? (
                    priorityImportantFunctions.slice(0, 5).map((entry, index) => {
                      const tuple = Array.isArray(entry) ? entry : [];
                      const functionName = String(tuple[0] || `function-${index + 1}`);
                      const score = Number(tuple[1] || 0);

                      return (
                        <li key={`priority-function-${index}`} className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-800">
                          {functionName} (Score: {score.toFixed(4)})
                        </li>
                      );
                    })
                  ) : (
                    <li className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">No important functions data available.</li>
                  )}
                </ul>
              </>
            )}
          </article>
        </section>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Repository footprint</span>
            <div className="mt-3 grid gap-3">
              {footprint.map((item) => (
                <div key={item.label} className="grid gap-2">
                  <div className="flex items-center justify-between gap-3 text-sm text-slate-700">
                    <span className="font-medium">{item.label}</span>
                    <strong className="text-slate-900">{item.value}</strong>
                  </div>
                  <div className="h-2 rounded-full bg-slate-200">
                    <div
                      className="h-2 rounded-full bg-sky-500"
                      style={{ width: `${Math.max((item.value / maxFootprint) * 100, item.value > 0 ? 8 : 0)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </article>

          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Severity mix</span>
            <div className="mt-3 grid gap-2">
              {severityMix.map((item) => (
                <div key={item.label} className="flex items-center gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm">
                  <span className={`severity-dot severity-${item.tone}`} aria-hidden="true" />
                  <span className="text-slate-700">{item.label}</span>
                  <strong className="ml-auto text-slate-900">{item.value}</strong>
                </div>
              ))}
            </div>
          </article>
        </section>

        <section className="grid grid-cols-1 gap-4 md:grid-cols-2">
          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Backend summaries</span>
            <div className="mt-3 space-y-2">
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">{projectSummary ?? "No project summary available yet."}</p>
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">{architectureSummary ?? "No architecture summary available yet."}</p>
              <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">{executionSummary ?? "No execution flow summary available yet."}</p>
            </div>
          </article>

          <article className="rounded-xl border border-slate-200 bg-white/90 p-5 shadow-sm">
            <span className="text-xs font-semibold uppercase tracking-[0.12em] text-slate-500">Flow path</span>
            <div className="mt-3 grid gap-2">
              {flowPath.length ? (
                flowPath.slice(0, 8).map((node, index) => (
                  <div key={`${node}-${index}`} className="flex items-center gap-3 rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-700">
                    <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700">{index + 1}</span>
                    <span className="truncate">{node}</span>
                  </div>
                ))
              ) : (
                <p className="rounded-md bg-slate-50 px-3 py-2 text-sm text-slate-600">No flow path available in the saved analysis.</p>
              )}
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}

function DashboardMetricTile({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  value: number | string;
}) {
  return (
    <div className="rounded-md border border-slate-200 bg-slate-50 p-3">
      <div className="inline-flex items-center gap-2 text-xs text-slate-500">
        <Icon className="icon-sm" />
        <span>{label}</span>
      </div>
      <div className="mt-1 text-lg font-semibold text-slate-900">{value}</div>
    </div>
  );
}

function AiTutorView({ navigate }: { navigate: NavigateFn }) {
  const [code, setCode] = useState(SAMPLE_CODE);
  const [language, setLanguage] = useState("typescript");
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<AIExplanationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExplain = async () => {
    if (!code.trim()) {
      setError("Paste or type code first.");
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await explainCode(code, language, question.trim() || undefined);
      setResponse(data);
    } catch (requestError) {
      const message = requestError instanceof Error ? requestError.message : "Failed to explain code";
      setError(message);
    } finally {
      setIsLoading(false);
    }
  };

  const copyExplanation = async () => {
    if (!response?.explanation) {
      return;
    }

    await navigator.clipboard.writeText(response.explanation);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1200);
  };

  return (
    <div className="app-shell">
      <MainNav navigate={navigate} />

      <main className="ai-shell">
        <section className="ai-hero-grid">
          <article className="ai-hero-card">
            <div className="eyebrow">
              <Sparkles className="icon-sm" /> FastAPI explanation
            </div>
            <h1>Explain code with the Python pipeline.</h1>
            <p>
              This page sends code to the FastAPI explanation endpoint and renders returned summary,
              model metadata, complexity score, and key concepts.
            </p>

            <div className="ai-form-stack">
              <div className="form-row">
                <label htmlFor="ai-language">Language</label>
                <input id="ai-language" value={language} onChange={(event) => setLanguage(event.target.value)} />
              </div>
              <div className="form-row">
                <label htmlFor="ai-question">Question, if any</label>
                <input
                  id="ai-question"
                  placeholder="What is this function doing?"
                  value={question}
                  onChange={(event) => setQuestion(event.target.value)}
                />
              </div>
              <div className="form-row">
                <label htmlFor="ai-code">Code</label>
                <textarea
                  id="ai-code"
                  className="code-editor"
                  value={code}
                  onChange={(event) => setCode(event.target.value)}
                />
              </div>
              <div className="action-row">
                <button onClick={handleExplain} disabled={isLoading}>
                  {isLoading ? <Loader2 className="icon-sm spinning" /> : <Brain className="icon-sm" />} 
                  {isLoading ? "Generating..." : "Explain with FastAPI"}
                </button>
                <button type="button" className="secondary-button" onClick={() => setCode(SAMPLE_CODE)}>
                  Load sample
                </button>
              </div>
              {error ? <div className="error">{error}</div> : null}
            </div>
          </article>

          <div className="ai-meta-stack">
            <article className="ai-meta-card">
              <h2>Pipeline metadata</h2>
              <p>What the backend returns alongside explanation text.</p>
              <div className="ai-meta-grid">
                <AiMetaTile label="Pipeline" value={response?.pipeline ?? "n/a"} />
                <AiMetaTile label="Model" value={response?.model ?? "n/a"} />
                <AiMetaTile label="Complexity" value={response?.complexity_score?.toFixed(2) ?? "n/a"} />
                <AiMetaTile label="Concepts" value={response?.key_concepts?.length ?? 0} />
              </div>
            </article>
            <article className="ai-meta-card">
              <h2>Quick tips</h2>
              <p>Prompts that work well with the explanation backend.</p>
              <div className="ai-tip-list">
                <p>Ask for flow, side effects, and data transformations.</p>
                <p>Use a real snippet from your repository for best response quality.</p>
                <p>Pair this page with Analyze to jump from findings to explanation.</p>
              </div>
            </article>
          </div>
        </section>

        <section className="ai-main-grid">
          <article className="workspace-card result-card">
            <div className="section-heading ai-output-heading">
              <div>
                <h2>Explanation</h2>
                <p>Rendered output from the Python AI pipeline.</p>
              </div>
              <button
                type="button"
                className="secondary-button ai-copy-button"
                onClick={copyExplanation}
                disabled={!response?.explanation}
              >
                <ClipboardCopy className="icon-sm" /> {copied ? "Copied" : "Copy"}
              </button>
            </div>

            {response ? (
              <div className="tutor-output">
                <div className="tutor-output-bar">
                  <div>
                    <strong>{response.language ?? "Unknown"}</strong>
                    <span>
                      {response.pipeline ?? "pipeline"}
                      {response.model ? ` · ${response.model}` : ""}
                    </span>
                  </div>
                </div>
                <pre>{response.explanation}</pre>

                {response.key_concepts?.length ? (
                  <div className="ai-concept-chips">
                    {response.key_concepts.map((concept) => (
                      <span key={concept} className="ai-concept-chip">
                        {concept}
                      </span>
                    ))}
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="empty-state">
                <BookOpen className="icon-lg" />
                <p>Run the explanation pipeline to view the result here.</p>
              </div>
            )}
          </article>

          <article className="workspace-card">
            <div className="section-heading">
              <h2>How it works</h2>
              <p>The backend uses deterministic AI explanation with structured metadata.</p>
            </div>
            <div className="ai-tip-list">
              <p>1. Prompt is built from snippet, language, and optional question.</p>
              <p>2. Key concepts and complexity signals are extracted in Python.</p>
              <p>3. Explanation text and metadata are returned to the frontend.</p>
              <p>4. Output remains usable even when advanced models are unavailable.</p>
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}

function AiMetaTile({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="ai-meta-tile">
      <div className="ai-meta-label">{label}</div>
      <div className="ai-meta-value">{value}</div>
    </div>
  );
}

export default App;
