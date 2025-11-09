/**
 * Optimized Database Query Examples
 * 
 * This file demonstrates best practices for database queries:
 * - Using indexes effectively
 * - Preventing N+1 queries
 * - Batch loading data
 * - Connection pool management
 */

import { db } from './index';
import { 
  user, 
  lessons, 
  lessonProgress, 
  userProgress,
  achievements,
  userAchievements,
  learningPaths,
  quizzes,
  quizAttempts,
} from './schema';
import { eq, and, desc, asc, inArray, sql } from 'drizzle-orm';
import { monitoredQuery, connectionPool, batchExecutor } from './optimization';

/**
 * OPTIMIZED: Get user progress with completed lessons
 * Uses JOIN to fetch data in single query instead of N+1
 */
export async function getUserProgressWithLessons(userId: string) {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        // Single query with JOIN - much faster than separate queries
        const result = await db
          .select({
            progress: userProgress,
            completedLessons: sql<number>`COUNT(DISTINCT ${lessonProgress.id})`,
            totalXp: userProgress.totalXp,
            level: userProgress.level,
          })
          .from(userProgress)
          .leftJoin(
            lessonProgress,
            and(
              eq(lessonProgress.userId, userProgress.userId),
              eq(lessonProgress.status, 'completed')
            )
          )
          .where(eq(userProgress.userId, userId))
          .groupBy(userProgress.id)
          .limit(1);

        return result[0];
      });
    },
    'getUserProgressWithLessons'
  );
}

/**
 * OPTIMIZED: Get learning path with lessons count
 * Uses subquery for efficient counting
 */
export async function getLearningPathsWithCounts() {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        return db
          .select({
            path: learningPaths,
            lessonCount: sql<number>`(
              SELECT COUNT(*) 
              FROM ${lessons} 
              WHERE ${lessons.learningPathId} = ${learningPaths.id}
            )`,
          })
          .from(learningPaths)
          .orderBy(asc(learningPaths.orderIndex));
      });
    },
    'getLearningPathsWithCounts'
  );
}

/**
 * OPTIMIZED: Get lessons for a learning path with progress
 * Uses batch loading to prevent N+1 queries
 */
export async function getLessonsWithProgress(
  learningPathId: number,
  userId: string
) {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        // Fetch lessons
        const pathLessons = await db
          .select()
          .from(lessons)
          .where(eq(lessons.learningPathId, learningPathId))
          .orderBy(asc(lessons.orderIndex));

        if (pathLessons.length === 0) {
          return [];
        }

        // Batch fetch progress for all lessons in single query
        const lessonIds = pathLessons.map(l => l.id);
        const progressRecords = await db
          .select()
          .from(lessonProgress)
          .where(
            and(
              eq(lessonProgress.userId, userId),
              inArray(lessonProgress.lessonId, lessonIds)
            )
          );

        // Create progress map for O(1) lookup
        const progressMap = new Map(
          progressRecords.map(p => [p.lessonId, p])
        );

        // Combine data
        return pathLessons.map(lesson => ({
          ...lesson,
          progress: progressMap.get(lesson.id) || null,
        }));
      });
    },
    'getLessonsWithProgress'
  );
}

/**
 * OPTIMIZED: Get user achievements with details
 * Uses JOIN and batching for efficiency
 */
export async function getUserAchievementsWithDetails(userId: string) {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        return db
          .select({
            userAchievement: userAchievements,
            achievement: achievements,
          })
          .from(userAchievements)
          .innerJoin(
            achievements,
            eq(userAchievements.achievementId, achievements.id)
          )
          .where(eq(userAchievements.userId, userId))
          .orderBy(desc(userAchievements.earnedAt));
      });
    },
    'getUserAchievementsWithDetails'
  );
}

/**
 * OPTIMIZED: Get quiz attempts with quiz details
 * Efficient JOIN query with proper indexes
 */
export async function getUserQuizAttempts(userId: string, limit = 50) {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        return db
          .select({
            attempt: quizAttempts,
            quiz: quizzes,
            lesson: lessons,
          })
          .from(quizAttempts)
          .innerJoin(quizzes, eq(quizAttempts.quizId, quizzes.id))
          .innerJoin(lessons, eq(quizzes.lessonId, lessons.id))
          .where(eq(quizAttempts.userId, userId))
          .orderBy(desc(quizAttempts.attemptedAt))
          .limit(limit);
      });
    },
    'getUserQuizAttempts'
  );
}

/**
 * OPTIMIZED: Batch create lesson progress records
 * Uses batch insert for multiple records
 */
export async function batchCreateLessonProgress(
  progressRecords: Array<{
    userId: string;
    lessonId: number;
    status: string;
    startedAt?: string;
    completedAt?: string;
  }>
) {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        const now = new Date().toISOString();
        const records = progressRecords.map(record => ({
          ...record,
          createdAt: now,
          updatedAt: now,
        }));

        // Insert all records in single query
        return db.insert(lessonProgress).values(records);
      });
    },
    'batchCreateLessonProgress'
  );
}

/**
 * OPTIMIZED: Get user leaderboard
 * Uses index on totalXp for fast sorting
 */
export async function getLeaderboard(limit = 100) {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        return db
          .select({
            userId: userProgress.userId,
            userName: user.name,
            userEmail: user.email,
            totalXp: userProgress.totalXp,
            level: userProgress.level,
            streakDays: userProgress.streakDays,
          })
          .from(userProgress)
          .innerJoin(user, eq(userProgress.userId, user.id))
          .orderBy(desc(userProgress.totalXp))
          .limit(limit);
      });
    },
    'getLeaderboard'
  );
}

/**
 * OPTIMIZED: Get lesson completion stats
 * Uses efficient aggregation query
 */
export async function getLessonCompletionStats(lessonId: number) {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        const result = await db
          .select({
            totalAttempts: sql<number>`COUNT(*)`,
            completions: sql<number>`SUM(CASE WHEN ${lessonProgress.status} = 'completed' THEN 1 ELSE 0 END)`,
            avgTimeToComplete: sql<number>`AVG(
              CASE 
                WHEN ${lessonProgress.completedAt} IS NOT NULL 
                  AND ${lessonProgress.startedAt} IS NOT NULL
                THEN 
                  (julianday(${lessonProgress.completedAt}) - julianday(${lessonProgress.startedAt})) * 24 * 60
                ELSE NULL
              END
            )`,
          })
          .from(lessonProgress)
          .where(eq(lessonProgress.lessonId, lessonId));

        return result[0];
      });
    },
    'getLessonCompletionStats'
  );
}

/**
 * OPTIMIZED: Data loader for batching user queries
 * Prevents N+1 when fetching multiple users
 */
export const userLoader = batchExecutor.createDataLoader(
  async (userIds: string[]) => {
    const users = await db
      .select()
      .from(user)
      .where(inArray(user.id, userIds));

    // Create map for O(1) lookup
    const userMap = new Map(users.map(u => [u.id, u]));

    // Return in same order as input
    return userIds.map(
      id => userMap.get(id) || new Error(`User ${id} not found`)
    );
  },
  { cache: true, maxBatchSize: 100 }
);

/**
 * OPTIMIZED: Data loader for batching lesson queries
 */
export const lessonLoader = batchExecutor.createDataLoader(
  async (lessonIds: number[]) => {
    const lessonsData = await db
      .select()
      .from(lessons)
      .where(inArray(lessons.id, lessonIds));

    const lessonMap = new Map(lessonsData.map(l => [l.id, l]));

    return lessonIds.map(
      id => lessonMap.get(id) || new Error(`Lesson ${id} not found`)
    );
  },
  { cache: true, maxBatchSize: 100 }
);

/**
 * OPTIMIZED: Complex dashboard query
 * Fetches all necessary data in minimal queries
 */
export async function getUserDashboardData(userId: string) {
  return monitoredQuery(
    async () => {
      return connectionPool.acquireConnection(async () => {
        // Execute all queries in parallel
        const [
          progress,
          recentLessons,
          recentAchievements,
          stats,
        ] = await Promise.all([
          // User progress
          db
            .select()
            .from(userProgress)
            .where(eq(userProgress.userId, userId))
            .limit(1),

          // Recent lesson progress (with lesson details)
          db
            .select({
              progress: lessonProgress,
              lesson: lessons,
            })
            .from(lessonProgress)
            .innerJoin(lessons, eq(lessonProgress.lessonId, lessons.id))
            .where(eq(lessonProgress.userId, userId))
            .orderBy(desc(lessonProgress.updatedAt))
            .limit(5),

          // Recent achievements
          db
            .select({
              userAchievement: userAchievements,
              achievement: achievements,
            })
            .from(userAchievements)
            .innerJoin(
              achievements,
              eq(userAchievements.achievementId, achievements.id)
            )
            .where(eq(userAchievements.userId, userId))
            .orderBy(desc(userAchievements.earnedAt))
            .limit(3),

          // User stats
          db
            .select({
              totalLessons: sql<number>`COUNT(DISTINCT ${lessonProgress.lessonId})`,
              completedLessons: sql<number>`SUM(CASE WHEN ${lessonProgress.status} = 'completed' THEN 1 ELSE 0 END)`,
              totalQuizAttempts: sql<number>`(
                SELECT COUNT(*) 
                FROM ${quizAttempts} 
                WHERE ${quizAttempts.userId} = ${userId}
              )`,
              correctAnswers: sql<number>`(
                SELECT SUM(CASE WHEN ${quizAttempts.isCorrect} = 1 THEN 1 ELSE 0 END)
                FROM ${quizAttempts}
                WHERE ${quizAttempts.userId} = ${userId}
              )`,
            })
            .from(lessonProgress)
            .where(eq(lessonProgress.userId, userId)),
        ]);

        return {
          progress: progress[0] || null,
          recentLessons,
          recentAchievements,
          stats: stats[0] || null,
        };
      });
    },
    'getUserDashboardData'
  );
}

/**
 * Export all optimized queries
 */
export const optimizedQueries = {
  getUserProgressWithLessons,
  getLearningPathsWithCounts,
  getLessonsWithProgress,
  getUserAchievementsWithDetails,
  getUserQuizAttempts,
  batchCreateLessonProgress,
  getLeaderboard,
  getLessonCompletionStats,
  getUserDashboardData,
  userLoader,
  lessonLoader,
};

export default optimizedQueries;
