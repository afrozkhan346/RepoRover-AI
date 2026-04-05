import { Navigate, Route, Routes } from "react-router-dom";
import ErrorReporter from "@/components/ErrorReporter";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import HomePageClient from "@/app/page-client";
import DashboardPageClient from "@/app/dashboard/page-client";
import AnalyzePageClient from "@/app/analyze/page-client";
import AiTutorPageClient from "@/app/ai-tutor/page-client";
import LessonsPage from "@/app/lessons/page";
import LessonPage from "@/app/lessons/[id]/page";
import AchievementsPage from "@/app/achievements/page";
import ProfilePage from "@/app/profile/page";
import LoginPage from "@/app/login/page";
import RegisterPage from "@/app/register/page";

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