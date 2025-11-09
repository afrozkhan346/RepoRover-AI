# Database Optimization Guide

This guide explains the database optimization features implemented in RepoRover AI, including indexing strategies, query optimization patterns, and performance monitoring tools.

## Table of Contents

1. [Overview](#overview)
2. [Index Strategy](#index-strategy)
3. [Optimization Utilities](#optimization-utilities)
4. [Usage Examples](#usage-examples)
5. [Monitoring & Analytics](#monitoring--analytics)
6. [Best Practices](#best-practices)
7. [Migration Guide](#migration-guide)

## Overview

The database optimization system provides:

- **35+ Strategic Indexes**: Carefully placed indexes on foreign keys, frequently queried fields, and common JOIN patterns
- **Query Performance Monitoring**: Automatic tracking of query execution times with slow query detection
- **Connection Pooling**: Efficient connection management with queue system
- **N+1 Query Detection**: Automatic detection of inefficient query patterns
- **Batch Query Executor**: DataLoader-style batching to reduce database round-trips
- **Database Analytics**: Tools for analyzing table sizes, index usage, and optimization opportunities

### Performance Goals

- Query response time: < 100ms for 95th percentile
- Connection pool utilization: < 80% under normal load
- Zero N+1 queries in production code
- Index coverage: > 90% of queries use indexes

## Index Strategy

### Philosophy

Our indexing strategy follows these principles:

1. **Index all foreign keys**: Every foreign key relationship has an index
2. **Composite indexes for JOINs**: Common JOIN patterns get composite indexes
3. **Descending indexes for sorting**: Frequently sorted fields (XP, dates) use DESC indexes
4. **Avoid over-indexing**: Only index fields used in WHERE, JOIN, or ORDER BY clauses

### Index Categories

#### 1. Foreign Key Indexes

Every foreign key has an index for efficient JOINs:

```sql
-- Examples
CREATE INDEX idx_session_user_id ON session(userId);
CREATE INDEX idx_lessons_learning_path ON lessons(learningPathId);
CREATE INDEX idx_lesson_progress_user_id ON lessonProgress(userId);
```

**Impact**: 10-100x faster JOIN queries

#### 2. Composite Indexes

Common query patterns get composite indexes:

```sql
-- User + Status queries
CREATE INDEX idx_lesson_progress_user_status ON lessonProgress(userId, status);

-- Learning path + order queries
CREATE INDEX idx_lessons_path_order ON lessons(learningPathId, orderIndex);

-- User + achievement queries
CREATE INDEX idx_user_achievements_user_achievement ON userAchievements(userId, achievementId);
```

**Impact**: Single index lookup instead of multiple, 2-5x faster

#### 3. Sort Optimization Indexes

Fields used in ORDER BY clauses get DESC indexes:

```sql
-- Leaderboard queries
CREATE INDEX idx_user_progress_total_xp ON userProgress(totalXp DESC);

-- Recent activity queries
CREATE INDEX idx_lesson_progress_updated ON lessonProgress(updatedAt DESC);

-- Quiz history
CREATE INDEX idx_quiz_attempts_attempted_at ON quizAttempts(attemptedAt DESC);
```

**Impact**: No sort operation needed, instant results

#### 4. Filter Indexes

Frequently filtered fields get indexes:

```sql
-- Difficulty filters
CREATE INDEX idx_lessons_difficulty ON lessons(difficulty);
CREATE INDEX idx_learning_paths_difficulty ON learningPaths(difficulty);

-- Status filters
CREATE INDEX idx_lesson_progress_status ON lessonProgress(status);

-- Boolean filters
CREATE INDEX idx_quiz_attempts_is_correct ON quizAttempts(isCorrect);
```

**Impact**: Fast filtering without table scans

### Complete Index List

| Table | Index Name | Columns | Purpose |
|-------|-----------|---------|---------|
| user | idx_user_email | email | Login lookups |
| session | idx_session_user_id | userId | User sessions |
| session | idx_session_expires_at | expiresAt | Cleanup queries |
| session | idx_session_user_expires | userId, expiresAt | Active sessions |
| account | idx_account_user_id | userId | OAuth accounts |
| account | idx_account_provider_account | providerId, providerAccountId | OAuth lookup |
| verification | idx_verification_identifier | identifier | Email verification |
| verification | idx_verification_token | token | Token lookup |
| userProgress | idx_user_progress_user_id | userId | User progress |
| userProgress | idx_user_progress_level | level | Level queries |
| userProgress | idx_user_progress_total_xp | totalXp DESC | Leaderboards |
| userProgress | idx_user_progress_streak | streakDays DESC | Streak queries |
| learningPaths | idx_learning_paths_order | orderIndex | Path ordering |
| learningPaths | idx_learning_paths_difficulty | difficulty | Filtering |
| lessons | idx_lessons_learning_path | learningPathId | Path lessons |
| lessons | idx_lessons_path_order | learningPathId, orderIndex | Ordered lessons |
| lessons | idx_lessons_difficulty | difficulty | Filtering |
| lessons | idx_lessons_order | orderIndex | Global order |
| lessonProgress | idx_lesson_progress_user_id | userId | User progress |
| lessonProgress | idx_lesson_progress_lesson_id | lessonId | Lesson stats |
| lessonProgress | idx_lesson_progress_user_lesson | userId, lessonId | Specific progress |
| lessonProgress | idx_lesson_progress_status | status | Status filtering |
| lessonProgress | idx_lesson_progress_updated | updatedAt DESC | Recent activity |
| lessonProgress | idx_lesson_progress_user_status | userId, status | User completed |
| achievements | idx_achievements_category | category | Category queries |
| achievements | idx_achievements_difficulty | difficulty | Filtering |
| userAchievements | idx_user_achievements_user_id | userId | User achievements |
| userAchievements | idx_user_achievements_achievement_id | achievementId | Achievement users |
| userAchievements | idx_user_achievements_user_achievement | userId, achievementId | Unique check |
| userAchievements | idx_user_achievements_earned_at | earnedAt DESC | Recent achievements |
| quizzes | idx_quizzes_lesson_id | lessonId | Lesson quizzes |
| quizzes | idx_quizzes_difficulty | difficulty | Filtering |
| quizAttempts | idx_quiz_attempts_user_id | userId | User attempts |
| quizAttempts | idx_quiz_attempts_quiz_id | quizId | Quiz stats |
| quizAttempts | idx_quiz_attempts_user_quiz | userId, quizId | User quiz history |
| quizAttempts | idx_quiz_attempts_attempted_at | attemptedAt DESC | Recent attempts |
| quizAttempts | idx_quiz_attempts_is_correct | isCorrect | Accuracy stats |
| repositories | idx_repositories_user_id | userId | User repos |
| repositories | idx_repositories_language | language | Language filter |
| repositories | idx_repositories_stars | stars DESC | Popular repos |
| repositories | idx_repositories_created_at | createdAt DESC | Recent repos |
| repositories | idx_repositories_user_language | userId, language | User lang repos |

## Optimization Utilities

### 1. Query Performance Monitor

Tracks query execution times and identifies slow queries.

```typescript
import { queryMonitor, monitoredQuery } from '@/db';

// Automatic monitoring with wrapper
const result = await monitoredQuery(
  async () => {
    return db.select().from(lessons);
  },
  'getAllLessons'
);

// Get statistics
const stats = queryMonitor.getStatistics();
console.log(stats);
// {
//   totalQueries: 150,
//   avgQueryTime: 45.5,
//   maxQueryTime: 250,
//   minQueryTime: 5,
//   slowQueries: 12,
//   queriesByName: { getAllLessons: 10, ... }
// }

// Get slow queries
const slowQueries = queryMonitor.getSlowQueries(100); // > 100ms
```

**Features**:
- Configurable slow query threshold (default: 100ms)
- Query name tracking for easier debugging
- Circular buffer to prevent memory leaks (max 1000 queries)
- Real-time statistics

### 2. Connection Pool Manager

Manages database connections efficiently.

```typescript
import { connectionPool } from '@/db';

// Automatic connection management
await connectionPool.acquireConnection(async () => {
  return db.select().from(lessons);
});

// Check pool status
const stats = connectionPool.getStats();
console.log(stats);
// {
//   activeConnections: 5,
//   queuedRequests: 0,
//   totalAcquired: 123,
//   totalReleased: 118,
//   totalWaitTime: 50,
//   avgWaitTime: 0.4
// }
```

**Features**:
- Max 20 concurrent connections
- Request queue for excess connections
- 5-second timeout on connection acquisition
- Automatic connection release
- Wait time tracking

### 3. N+1 Query Detector

Detects inefficient query patterns automatically.

```typescript
import { n1Detector } from '@/db';

// Queries are automatically tracked
const lessons = await db.select().from(lessons).limit(10);

// This would trigger N+1 detection (BAD)
for (const lesson of lessons) {
  await db.select().from(lessonProgress)
    .where(eq(lessonProgress.lessonId, lesson.id));
}

// Check for patterns
const patterns = n1Detector.getPatterns();
// Warning: Detected N+1 pattern - same query executed 10 times
```

**Features**:
- Automatic pattern detection
- Configurable threshold (default: 5 repetitions)
- Query signature normalization
- Console warnings for detected patterns

### 4. Batch Query Executor

Batches multiple queries together using DataLoader pattern.

```typescript
import { batchExecutor } from '@/db';

// Create a data loader
const userLoader = batchExecutor.createDataLoader(
  async (userIds: string[]) => {
    const users = await db.select().from(user)
      .where(inArray(user.id, userIds));
    
    const userMap = new Map(users.map(u => [u.id, u]));
    return userIds.map(id => userMap.get(id) || new Error(`Not found: ${id}`));
  },
  { cache: true, maxBatchSize: 100 }
);

// Load users - automatically batched!
const user1 = await userLoader.load('user-1');
const user2 = await userLoader.load('user-2');
const user3 = await userLoader.load('user-3');
// Only 1 database query for all 3 users!
```

**Features**:
- Automatic request batching
- Configurable batch size (default: 50)
- Configurable batch delay (default: 10ms)
- Per-request caching
- Error handling per key

### 5. Database Analytics

Provides insights into database health and optimization opportunities.

```typescript
import { dbAnalytics } from '@/db';

// Get table sizes
const sizes = await dbAnalytics.getTableSizes();
// [
//   { name: 'lessonProgress', rows: 5420, diskSize: 245760 },
//   { name: 'userProgress', rows: 1234, diskSize: 98304 },
//   ...
// ]

// Get index statistics
const indexes = await dbAnalytics.getIndexStats();
// [
//   { name: 'idx_lesson_progress_user_id', tableName: 'lessonProgress' },
//   ...
// ]

// Get optimization suggestions
const suggestions = await dbAnalytics.analyzeAndSuggest();
// [
//   'Table lessonProgress has 5420 rows - consider partitioning',
//   'Total database size: 2.4 MB'
// ]

// Run maintenance
await dbAnalytics.vacuum(); // Reclaim space
await dbAnalytics.analyze(); // Update statistics
const ok = await dbAnalytics.integrityCheck(); // Verify integrity
```

## Usage Examples

### Optimized Query Patterns

All optimized query examples are in `src/db/queries.optimized.ts`:

```typescript
import optimizedQueries from '@/db/queries.optimized';

// Get user dashboard (single query)
const dashboard = await optimizedQueries.getUserDashboardData(userId);

// Get lessons with progress (2 queries instead of N+1)
const lessons = await optimizedQueries.getLessonsWithProgress(pathId, userId);

// Leaderboard (uses index on totalXp)
const top100 = await optimizedQueries.getLeaderboard(100);

// Batch create progress
await optimizedQueries.batchCreateLessonProgress([
  { userId: 'u1', lessonId: 1, status: 'completed' },
  { userId: 'u2', lessonId: 1, status: 'in_progress' },
  // ... more records
]);
```

### Using Data Loaders

```typescript
import { userLoader, lessonLoader } from '@/db/queries.optimized';

// In your API route
const userIds = ['user1', 'user2', 'user3'];
const users = await Promise.all(
  userIds.map(id => userLoader.load(id))
);
// Only 1 database query!
```

## Monitoring & Analytics

### Admin API Endpoints

Access database statistics via the admin API:

```bash
# Get comprehensive stats
GET /api/db/stats

# Response:
{
  "queryPerformance": {
    "totalQueries": 1523,
    "avgQueryTime": 45.2,
    "slowQueries": [...]
  },
  "connectionPool": {
    "activeConnections": 3,
    "queuedRequests": 0
  },
  "n1Patterns": [...],
  "optimizationSuggestions": [...]
}

# Run maintenance operations
POST /api/db/stats
{
  "operation": "vacuum" | "analyze" | "integrity-check" | "get-table-sizes" | "get-index-stats"
}

# Clear monitoring logs
DELETE /api/db/stats
```

### Monitoring in Production

```typescript
// Set up periodic monitoring
setInterval(async () => {
  const stats = queryMonitor.getStatistics();
  
  if (stats.slowQueries > 10) {
    console.warn('High number of slow queries detected', stats);
  }
  
  const poolStats = connectionPool.getStats();
  if (poolStats.activeConnections / 20 > 0.8) {
    console.warn('Connection pool utilization high', poolStats);
  }
}, 60000); // Every minute
```

## Best Practices

### DO ✅

1. **Use indexed columns in WHERE clauses**
   ```typescript
   // GOOD - uses idx_lesson_progress_user_id
   db.select().from(lessonProgress).where(eq(lessonProgress.userId, userId));
   ```

2. **Use JOINs instead of multiple queries**
   ```typescript
   // GOOD - single query with JOIN
   db.select()
     .from(lessonProgress)
     .innerJoin(lessons, eq(lessonProgress.lessonId, lessons.id))
     .where(eq(lessonProgress.userId, userId));
   ```

3. **Use batch operations**
   ```typescript
   // GOOD - single insert
   db.insert(lessonProgress).values(records);
   ```

4. **Use data loaders for repeated queries**
   ```typescript
   // GOOD - batched automatically
   const users = await Promise.all(ids.map(id => userLoader.load(id)));
   ```

5. **Monitor query performance**
   ```typescript
   // GOOD - wrapped for monitoring
   await monitoredQuery(() => db.select()..., 'queryName');
   ```

### DON'T ❌

1. **Don't query in loops (N+1)**
   ```typescript
   // BAD - N+1 query problem
   for (const lesson of lessons) {
     const progress = await db.select()
       .from(lessonProgress)
       .where(eq(lessonProgress.lessonId, lesson.id));
   }
   ```

2. **Don't forget to use indexes**
   ```typescript
   // BAD - full table scan on non-indexed field
   db.select().from(lessons).where(eq(lessons.content, 'something'));
   ```

3. **Don't select unnecessary columns**
   ```typescript
   // BAD - fetches all columns
   db.select().from(lessons);
   
   // GOOD - only needed columns
   db.select({ id: lessons.id, title: lessons.title }).from(lessons);
   ```

4. **Don't ignore connection pool**
   ```typescript
   // BAD - unmanaged connection
   await db.select()...;
   
   // GOOD - managed connection
   await connectionPool.acquireConnection(() => db.select()...);
   ```

## Migration Guide

### Applying the Indexes

1. **Run the migration SQL**:
   ```bash
   # Using Drizzle Kit
   npm run drizzle:push

   # Or manually
   sqlite3 your-database.db < drizzle/0002_add_performance_indexes.sql
   ```

2. **Verify indexes created**:
   ```typescript
   import { dbAnalytics } from '@/db';
   
   const indexes = await dbAnalytics.getIndexStats();
   console.log(`Created ${indexes.length} indexes`);
   ```

3. **Update queries to use optimization utilities**:
   ```typescript
   // Before
   const lessons = await db.select().from(lessons);
   
   // After
   const lessons = await monitoredQuery(
     () => db.select().from(lessons),
     'getAllLessons'
   );
   ```

### Gradual Rollout

1. **Phase 1**: Apply indexes (no code changes)
2. **Phase 2**: Add monitoring to critical queries
3. **Phase 3**: Refactor N+1 queries to use JOINs
4. **Phase 4**: Implement data loaders
5. **Phase 5**: Enable production monitoring

### Performance Testing

```typescript
// Before optimization
console.time('query');
const result = await oldQuery();
console.timeEnd('query');
// query: 250ms

// After optimization
console.time('query');
const result = await optimizedQuery();
console.timeEnd('query');
// query: 15ms

// 16x improvement!
```

## Troubleshooting

### Slow Queries

1. Check if query uses indexes:
   ```sql
   EXPLAIN QUERY PLAN SELECT * FROM lessons WHERE learningPathId = 1;
   -- Should show "USING INDEX idx_lessons_learning_path"
   ```

2. Check slow query log:
   ```typescript
   const slowQueries = queryMonitor.getSlowQueries(100);
   console.log(slowQueries);
   ```

3. Add missing indexes or optimize query structure

### High Connection Pool Usage

1. Check pool stats:
   ```typescript
   const stats = connectionPool.getStats();
   console.log('Active:', stats.activeConnections);
   console.log('Queued:', stats.queuedRequests);
   ```

2. Look for long-running queries
3. Consider increasing pool size if needed

### N+1 Queries Detected

1. Check patterns:
   ```typescript
   const patterns = n1Detector.getPatterns();
   ```

2. Refactor to use JOINs or batch loading
3. Use provided optimized query examples

## Performance Metrics

Expected improvements after optimization:

| Query Type | Before | After | Improvement |
|------------|--------|-------|-------------|
| User progress lookup | 50ms | 5ms | 10x |
| Lessons with progress | 500ms | 30ms | 16x |
| Leaderboard (top 100) | 200ms | 8ms | 25x |
| Dashboard data | 800ms | 45ms | 17x |
| Quiz attempts | 150ms | 12ms | 12x |

## Resources

- [SQLite Index Documentation](https://www.sqlite.org/queryplanner.html)
- [Drizzle ORM Docs](https://orm.drizzle.team/)
- [DataLoader Pattern](https://github.com/graphql/dataloader)
- Query optimization examples: `src/db/queries.optimized.ts`
- Migration script: `drizzle/0002_add_performance_indexes.sql`

---

**Last Updated**: 2024
**Version**: 1.0.0
**Maintained By**: RepoRover AI Team
