-- Migration: Add Performance Indexes
-- Description: Adds comprehensive indexes to improve query performance
-- Date: 2024

-- User table indexes
CREATE INDEX IF NOT EXISTS idx_user_email ON user(email);

-- Session table indexes
CREATE INDEX IF NOT EXISTS idx_session_user_id ON session(userId);
CREATE INDEX IF NOT EXISTS idx_session_expires_at ON session(expiresAt);
CREATE INDEX IF NOT EXISTS idx_session_user_expires ON session(userId, expiresAt);

-- Account table indexes
CREATE INDEX IF NOT EXISTS idx_account_user_id ON account(userId);
CREATE INDEX IF NOT EXISTS idx_account_provider_account ON account(providerId, providerAccountId);

-- Verification table indexes
CREATE INDEX IF NOT EXISTS idx_verification_identifier ON verification(identifier);
CREATE INDEX IF NOT EXISTS idx_verification_token ON verification(token);

-- User Progress table indexes
CREATE INDEX IF NOT EXISTS idx_user_progress_user_id ON userProgress(userId);
CREATE INDEX IF NOT EXISTS idx_user_progress_level ON userProgress(level);
CREATE INDEX IF NOT EXISTS idx_user_progress_total_xp ON userProgress(totalXp DESC);
CREATE INDEX IF NOT EXISTS idx_user_progress_streak ON userProgress(streakDays DESC);

-- Learning Paths table indexes
CREATE INDEX IF NOT EXISTS idx_learning_paths_order ON learningPaths(orderIndex);
CREATE INDEX IF NOT EXISTS idx_learning_paths_difficulty ON learningPaths(difficulty);

-- Lessons table indexes
CREATE INDEX IF NOT EXISTS idx_lessons_learning_path ON lessons(learningPathId);
CREATE INDEX IF NOT EXISTS idx_lessons_path_order ON lessons(learningPathId, orderIndex);
CREATE INDEX IF NOT EXISTS idx_lessons_difficulty ON lessons(difficulty);
CREATE INDEX IF NOT EXISTS idx_lessons_order ON lessons(orderIndex);

-- Lesson Progress table indexes
CREATE INDEX IF NOT EXISTS idx_lesson_progress_user_id ON lessonProgress(userId);
CREATE INDEX IF NOT EXISTS idx_lesson_progress_lesson_id ON lessonProgress(lessonId);
CREATE INDEX IF NOT EXISTS idx_lesson_progress_user_lesson ON lessonProgress(userId, lessonId);
CREATE INDEX IF NOT EXISTS idx_lesson_progress_status ON lessonProgress(status);
CREATE INDEX IF NOT EXISTS idx_lesson_progress_updated ON lessonProgress(updatedAt DESC);
CREATE INDEX IF NOT EXISTS idx_lesson_progress_user_status ON lessonProgress(userId, status);

-- Achievements table indexes
CREATE INDEX IF NOT EXISTS idx_achievements_category ON achievements(category);
CREATE INDEX IF NOT EXISTS idx_achievements_difficulty ON achievements(difficulty);

-- User Achievements table indexes
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_id ON userAchievements(userId);
CREATE INDEX IF NOT EXISTS idx_user_achievements_achievement_id ON userAchievements(achievementId);
CREATE INDEX IF NOT EXISTS idx_user_achievements_user_achievement ON userAchievements(userId, achievementId);
CREATE INDEX IF NOT EXISTS idx_user_achievements_earned_at ON userAchievements(earnedAt DESC);

-- Quizzes table indexes
CREATE INDEX IF NOT EXISTS idx_quizzes_lesson_id ON quizzes(lessonId);
CREATE INDEX IF NOT EXISTS idx_quizzes_difficulty ON quizzes(difficulty);

-- Quiz Attempts table indexes
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_id ON quizAttempts(userId);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_quiz_id ON quizAttempts(quizId);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_user_quiz ON quizAttempts(userId, quizId);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_attempted_at ON quizAttempts(attemptedAt DESC);
CREATE INDEX IF NOT EXISTS idx_quiz_attempts_is_correct ON quizAttempts(isCorrect);

-- Repositories table indexes (if table exists)
CREATE INDEX IF NOT EXISTS idx_repositories_user_id ON repositories(userId);
CREATE INDEX IF NOT EXISTS idx_repositories_language ON repositories(language);
CREATE INDEX IF NOT EXISTS idx_repositories_stars ON repositories(stars DESC);
CREATE INDEX IF NOT EXISTS idx_repositories_created_at ON repositories(createdAt DESC);
CREATE INDEX IF NOT EXISTS idx_repositories_user_language ON repositories(userId, language);
