import { sqliteTable, integer, text, index } from 'drizzle-orm/sqlite-core';

// Auth tables for better-auth
export const user = sqliteTable("user", {
  id: text("id").primaryKey(),
  name: text("name").notNull(),
  email: text("email").notNull().unique(),
  emailVerified: integer("email_verified", { mode: "boolean" })
    .$defaultFn(() => false)
    .notNull(),
  image: text("image"),
  createdAt: integer("created_at", { mode: "timestamp" })
    .$defaultFn(() => new Date())
    .notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp" })
    .$defaultFn(() => new Date())
    .notNull(),
}, (table) => ({
  emailIdx: index("user_email_idx").on(table.email),
  createdAtIdx: index("user_created_at_idx").on(table.createdAt),
}));

export const session = sqliteTable("session", {
  id: text("id").primaryKey(),
  expiresAt: integer("expires_at", { mode: "timestamp" }).notNull(),
  token: text("token").notNull().unique(),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull(),
  ipAddress: text("ip_address"),
  userAgent: text("user_agent"),
  userId: text("user_id")
    .notNull()
    .references(() => user.id, { onDelete: "cascade" }),
}, (table) => ({
  userIdIdx: index("session_user_id_idx").on(table.userId),
  tokenIdx: index("session_token_idx").on(table.token),
  expiresAtIdx: index("session_expires_at_idx").on(table.expiresAt),
}));

export const account = sqliteTable("account", {
  id: text("id").primaryKey(),
  accountId: text("account_id").notNull(),
  providerId: text("provider_id").notNull(),
  userId: text("user_id")
    .notNull()
    .references(() => user.id, { onDelete: "cascade" }),
  accessToken: text("access_token"),
  refreshToken: text("refresh_token"),
  idToken: text("id_token"),
  accessTokenExpiresAt: integer("access_token_expires_at", {
    mode: "timestamp",
  }),
  refreshTokenExpiresAt: integer("refresh_token_expires_at", {
    mode: "timestamp",
  }),
  scope: text("scope"),
  password: text("password"),
  createdAt: integer("created_at", { mode: "timestamp" }).notNull(),
  updatedAt: integer("updated_at", { mode: "timestamp" }).notNull(),
}, (table) => ({
  userIdIdx: index("account_user_id_idx").on(table.userId),
  providerIdx: index("account_provider_idx").on(table.providerId),
}));

export const verification = sqliteTable("verification", {
  id: text("id").primaryKey(),
  identifier: text("identifier").notNull(),
  value: text("value").notNull(),
  expiresAt: integer("expires_at", { mode: "timestamp" }).notNull(),
  createdAt: integer("created_at", { mode: "timestamp" }).$defaultFn(
    () => new Date(),
  ),
  updatedAt: integer("updated_at", { mode: "timestamp" }).$defaultFn(
    () => new Date(),
  ),
}, (table) => ({
  identifierIdx: index("verification_identifier_idx").on(table.identifier),
  expiresAtIdx: index("verification_expires_at_idx").on(table.expiresAt),
}));

// Application tables with optimized indexes
export const userProgress = sqliteTable('user_progress', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
  totalXp: integer('total_xp').notNull().default(0),
  level: integer('level').notNull().default(1),
  streakDays: integer('streak_days').notNull().default(0),
  lastActiveDate: text('last_active_date'),
  createdAt: text('created_at').notNull(),
  updatedAt: text('updated_at').notNull(),
}, (table) => ({
  userIdIdx: index("user_progress_user_id_idx").on(table.userId),
  levelIdx: index("user_progress_level_idx").on(table.level),
  totalXpIdx: index("user_progress_total_xp_idx").on(table.totalXp),
  lastActiveDateIdx: index("user_progress_last_active_date_idx").on(table.lastActiveDate),
}));

export const learningPaths = sqliteTable('learning_paths', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  title: text('title').notNull(),
  description: text('description'),
  difficulty: text('difficulty').notNull(),
  estimatedHours: integer('estimated_hours').notNull(),
  icon: text('icon'),
  orderIndex: integer('order_index').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => ({
  difficultyIdx: index("learning_paths_difficulty_idx").on(table.difficulty),
  orderIndexIdx: index("learning_paths_order_index_idx").on(table.orderIndex),
}));

export const lessons = sqliteTable('lessons', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  learningPathId: integer('learning_path_id').notNull().references(() => learningPaths.id, { onDelete: 'cascade' }),
  title: text('title').notNull(),
  description: text('description'),
  content: text('content'),
  difficulty: text('difficulty').notNull(),
  xpReward: integer('xp_reward').notNull(),
  orderIndex: integer('order_index').notNull(),
  estimatedMinutes: integer('estimated_minutes').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => ({
  learningPathIdIdx: index("lessons_learning_path_id_idx").on(table.learningPathId),
  difficultyIdx: index("lessons_difficulty_idx").on(table.difficulty),
  orderIndexIdx: index("lessons_order_index_idx").on(table.orderIndex),
  compositeIdx: index("lessons_path_order_idx").on(table.learningPathId, table.orderIndex),
}));

export const lessonProgress = sqliteTable('lesson_progress', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
  lessonId: integer('lesson_id').notNull().references(() => lessons.id, { onDelete: 'cascade' }),
  status: text('status').notNull(),
  startedAt: text('started_at'),
  completedAt: text('completed_at'),
  createdAt: text('created_at').notNull(),
  updatedAt: text('updated_at').notNull(),
}, (table) => ({
  userIdIdx: index("lesson_progress_user_id_idx").on(table.userId),
  lessonIdIdx: index("lesson_progress_lesson_id_idx").on(table.lessonId),
  statusIdx: index("lesson_progress_status_idx").on(table.status),
  completedAtIdx: index("lesson_progress_completed_at_idx").on(table.completedAt),
  compositeUserLessonIdx: index("lesson_progress_user_lesson_idx").on(table.userId, table.lessonId),
  compositeUserStatusIdx: index("lesson_progress_user_status_idx").on(table.userId, table.status),
}));

export const achievements = sqliteTable('achievements', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  title: text('title').notNull(),
  description: text('description'),
  icon: text('icon'),
  xpReward: integer('xp_reward').notNull(),
  requirementType: text('requirement_type').notNull(),
  requirementValue: integer('requirement_value').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => ({
  requirementTypeIdx: index("achievements_requirement_type_idx").on(table.requirementType),
  xpRewardIdx: index("achievements_xp_reward_idx").on(table.xpReward),
}));

export const userAchievements = sqliteTable('user_achievements', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
  achievementId: integer('achievement_id').notNull().references(() => achievements.id, { onDelete: 'cascade' }),
  earnedAt: text('earned_at').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => ({
  userIdIdx: index("user_achievements_user_id_idx").on(table.userId),
  achievementIdIdx: index("user_achievements_achievement_id_idx").on(table.achievementId),
  earnedAtIdx: index("user_achievements_earned_at_idx").on(table.earnedAt),
  compositeIdx: index("user_achievements_user_achievement_idx").on(table.userId, table.achievementId),
}));

export const quizzes = sqliteTable('quizzes', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  lessonId: integer('lesson_id').notNull().references(() => lessons.id, { onDelete: 'cascade' }),
  question: text('question').notNull(),
  options: text('options').notNull(),
  correctAnswer: text('correct_answer').notNull(),
  explanation: text('explanation'),
  difficulty: text('difficulty').notNull(),
  xpReward: integer('xp_reward').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => ({
  lessonIdIdx: index("quizzes_lesson_id_idx").on(table.lessonId),
  difficultyIdx: index("quizzes_difficulty_idx").on(table.difficulty),
}));

export const quizAttempts = sqliteTable('quiz_attempts', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
  quizId: integer('quiz_id').notNull().references(() => quizzes.id, { onDelete: 'cascade' }),
  userAnswer: text('user_answer').notNull(),
  isCorrect: integer('is_correct', { mode: 'boolean' }).notNull(),
  attemptedAt: text('attempted_at').notNull(),
  createdAt: text('created_at').notNull(),
}, (table) => ({
  userIdIdx: index("quiz_attempts_user_id_idx").on(table.userId),
  quizIdIdx: index("quiz_attempts_quiz_id_idx").on(table.quizId),
  isCorrectIdx: index("quiz_attempts_is_correct_idx").on(table.isCorrect),
  attemptedAtIdx: index("quiz_attempts_attempted_at_idx").on(table.attemptedAt),
  compositeIdx: index("quiz_attempts_user_quiz_idx").on(table.userId, table.quizId),
}));

export const repositories = sqliteTable('repositories', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  userId: text('user_id').notNull().references(() => user.id, { onDelete: 'cascade' }),
  githubUrl: text('github_url').notNull(),
  repoName: text('repo_name').notNull(),
  description: text('description'),
  language: text('language'),
  stars: integer('stars').notNull().default(0),
  analyzedAt: text('analyzed_at'),
  analysisData: text('analysis_data'),
  createdAt: text('created_at').notNull(),
}, (table) => ({
  userIdIdx: index("repositories_user_id_idx").on(table.userId),
  languageIdx: index("repositories_language_idx").on(table.language),
  starsIdx: index("repositories_stars_idx").on(table.stars),
  analyzedAtIdx: index("repositories_analyzed_at_idx").on(table.analyzedAt),
  repoNameIdx: index("repositories_repo_name_idx").on(table.repoName),
}));
