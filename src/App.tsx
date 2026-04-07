import { Navigate, Route, Routes } from "react-router-dom";
import ErrorReporter from "@/components/ErrorReporter";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import HomePageClient from "@/pages/page-client";
import DashboardPageClient from "@/pages/dashboard/page-client";
import AnalyzePageClient from "@/pages/analyze/page-client";
import AiTutorPageClient from "@/pages/ai-tutor/page-client";
import LessonsPage from "@/pages/lessons/page";
import LessonPage from "@/pages/lessons/[id]/page";
import AchievementsPage from "@/pages/achievements/page";
import ProfilePage from "@/pages/profile/page";
import LoginPage from "@/pages/login/page";
import RegisterPage from "@/pages/register/page";

export default function App() {
  return (
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
      <ErrorReporter />
      <Routes>
        <Route path="/" element={<HomePageClient />} />
        <Route path="/dashboard" element={<DashboardPageClient />} />
        <Route path="/analyze" element={<AnalyzePageClient />} />
        <Route path="/ai-tutor" element={<AiTutorPageClient />} />
        <Route path="/lessons" element={<LessonsPage />} />
        <Route path="/lessons/:id" element={<LessonPage />} />
        <Route path="/achievements" element={<AchievementsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      <Toaster />
    </ThemeProvider>
  );
}