# API Response Caching Guide

This guide explains the Redis-based caching system implemented in RepoRover AI for improved API performance and reduced database load.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Setup](#setup)
4. [Usage](#usage)
5. [Cache Strategies](#cache-strategies)
6. [Invalidation](#invalidation)
7. [Monitoring](#monitoring)
8. [Best Practices](#best-practices)

## Overview

The caching system provides:

- **Redis-based caching**: Fast in-memory cache with persistence
- **Automatic serialization**: JSON serialization/deserialization
- **TTL management**: Configurable time-to-live for each cache entry
- **Tag-based invalidation**: Group cache entries by tags for easy invalidation
- **Pattern-based invalidation**: Delete multiple keys matching a pattern
- **Cache statistics**: Hit/miss rates, performance metrics
- **Middleware integration**: Easy-to-use middleware for Next.js API routes
- **Stale-while-revalidate**: Serve stale data while fetching fresh data in background

### Performance Goals

- API response time: < 50ms for cached responses (vs 200-800ms uncached)
- Cache hit rate: > 80% for frequently accessed data
- Redis memory usage: < 512MB under normal load
- Reduced database queries: 70-90% reduction for cacheable endpoints

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ GET Request
       ▼
┌─────────────┐
│  Next.js    │
│   Route     │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌─────────────┐
│   Cache     │─────▶│   Redis     │
│ Middleware  │      │   Server    │
└──────┬──────┘      └─────────────┘
       │
       │ Cache MISS
       ▼
┌─────────────┐
│  Database   │
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Cache     │
│   Store     │
└─────────────┘
```

## Setup

### 1. Install Dependencies

```bash
npm install ioredis
npm install --save-dev @types/ioredis
```

### 2. Configure Environment Variables

Add to `.env`:

```bash
# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your-redis-password
REDIS_DB=0
REDIS_KEY_PREFIX=reporover:
REDIS_DEFAULT_TTL=3600

# Optional: Redis URL (alternative to separate host/port)
REDIS_URL=redis://localhost:6379
```

### 3. Run Redis Server

**Local Development:**
```bash
# Using Docker
docker run -d -p 6379:6379 --name redis redis:7-alpine

# Using Docker Compose (recommended)
docker-compose up -d redis
```

**Production:**
- Use managed Redis service (Redis Cloud, AWS ElastiCache, Azure Cache, etc.)
- Enable persistence (AOF + RDB)
- Configure memory limits and eviction policy

### 4. Initialize Cache

In your application startup:

```typescript
import { initializeCache } from '@/lib/cache';

// Initialize cache on app start
initializeCache({
  host: process.env.REDIS_HOST || 'localhost',
  port: parseInt(process.env.REDIS_PORT || '6379'),
  password: process.env.REDIS_PASSWORD,
  ttl: 3600, // 1 hour default
});
```

## Usage

### Basic Caching

```typescript
import { getCache, CacheKeys } from '@/lib/cache';

const cache = getCache();

// Set value
await cache.set(CacheKeys.learningPath(1), learningPathData, {
  ttl: 3600, // 1 hour
  tags: ['learning-paths'],
});

// Get value
const cached = await cache.get(CacheKeys.learningPath(1));

// Delete value
await cache.delete(CacheKeys.learningPath(1));
```

### Using Cache Middleware

The easiest way to add caching to API routes:

```typescript
import { withCache, CacheKeys, CacheTags } from '@/lib/cache';
import { NextRequest, NextResponse } from 'next/server';

async function getLearningPaths(request: NextRequest) {
  // Your existing handler logic
  const data = await db.select().from(learningPaths);
  return NextResponse.json(data);
}

// Wrap with cache middleware
export const GET = withCache(getLearningPaths, {
  ttl: 3600, // Cache for 1 hour
  tags: [CacheTags.LEARNING_PATHS],
  keyGenerator: (req) => {
    const url = new URL(req.url);
    const id = url.searchParams.get('id');
    return id ? CacheKeys.learningPath(id) : CacheKeys.learningPaths();
  },
});
```

### Cache-Aside Pattern

```typescript
import { getCache } from '@/lib/cache';

const cache = getCache();

const learningPath = await cache.getOrSet(
  CacheKeys.learningPath(pathId),
  async () => {
    // Fetch from database only if cache miss
    return await db
      .select()
      .from(learningPaths)
      .where(eq(learningPaths.id, pathId))
      .limit(1);
  },
  { ttl: 3600, tags: [CacheTags.LEARNING_PATHS] }
);
```

### Stale-While-Revalidate

Serve stale data immediately while fetching fresh data in the background:

```typescript
import { getWithRevalidate, CacheKeys } from '@/lib/cache';

const lessons = await getWithRevalidate(
  CacheKeys.lessonsByPath(pathId),
  async () => {
    return await db
      .select()
      .from(lessons)
      .where(eq(lessons.learningPathId, pathId));
  },
  { ttl: 1800, staleTime: 300 } // Cache 30min, stale after 5min
);
```

## Cache Strategies

### Time-Based TTL

Different data types have different update frequencies:

| Data Type | TTL | Reason |
|-----------|-----|--------|
| Learning Paths | 1 hour (3600s) | Rarely updated |
| Lessons | 30 min (1800s) | Occasionally updated |
| Achievements | 1 hour (3600s) | Static data |
| User Progress | 5 min (300s) | Frequently updated |
| Leaderboard | 1 min (60s) | Real-time data |
| User Dashboard | 5 min (300s) | Aggregated data |

### Cache Keys

Use consistent key naming:

```typescript
// Predefined cache keys
CacheKeys.learningPath(id)        // 'learning-path:1'
CacheKeys.learningPaths()         // 'learning-paths:all'
CacheKeys.lesson(id)              // 'lesson:1'
CacheKeys.lessonsByPath(pathId)   // 'lessons:path:1'
CacheKeys.userProgress(userId)    // 'user-progress:user123'
CacheKeys.leaderboard(100)        // 'leaderboard:top:100'
```

### Cache Tags

Group related cache entries for batch invalidation:

```typescript
// Predefined cache tags
CacheTags.LEARNING_PATHS  // 'learning-paths'
CacheTags.LESSONS         // 'lessons'
CacheTags.ACHIEVEMENTS    // 'achievements'
CacheTags.USER_PROGRESS   // 'user-progress'
CacheTags.QUIZZES         // 'quizzes'
CacheTags.LEADERBOARD     // 'leaderboard'
```

## Invalidation

### Tag-Based Invalidation

Invalidate all cache entries with specific tags:

```typescript
import { invalidateCacheTags, CacheTags } from '@/lib/cache';

// When a lesson is updated
await invalidateCacheTags([CacheTags.LESSONS]);

// When learning path is updated
await invalidateCacheTags([
  CacheTags.LEARNING_PATHS,
  CacheTags.LESSONS, // Also invalidate lessons
]);
```

### Pattern-Based Invalidation

Invalidate keys matching a pattern:

```typescript
import { invalidateCache } from '@/lib/cache';

// Invalidate all user progress caches
await invalidateCache('user-progress:*');

// Invalidate specific user's caches
await invalidateCache(`dashboard:${userId}`);

// Invalidate multiple patterns
await invalidateCache([
  'lessons:path:1',
  'lessons:path:2',
  'learning-path:*',
]);
```

### Write-Through Cache

Invalidate immediately when data changes:

```typescript
// In your mutation endpoint
export async function PUT(request: NextRequest) {
  const { id } = await request.json();
  
  // Update database
  await db
    .update(lessons)
    .set({ title: 'Updated Title' })
    .where(eq(lessons.id, id));

  // Invalidate cache
  await invalidateCacheTags([CacheTags.LESSONS]);
  
  return NextResponse.json({ success: true });
}
```

## Monitoring

### Cache Statistics Endpoint

Access cache metrics via API:

```bash
# Get cache statistics
GET /api/cache/stats

Response:
{
  "status": "connected",
  "stats": {
    "hits": 1523,
    "misses": 342,
    "sets": 445,
    "deletes": 12,
    "errors": 0,
    "hitRate": 0.8164,
    "hitRatePercentage": "81.64%"
  },
  "redis": {
    "connected": true,
    "keyCount": 445,
    "usedMemory": "2.34M",
    "connectedClients": 3,
    "totalCommands": 5234
  }
}
```

### Cache Operations

```bash
# Invalidate by tags
POST /api/cache/stats
{
  "operation": "invalidate-tags",
  "tags": ["learning-paths", "lessons"]
}

# Invalidate by pattern
POST /api/cache/stats
{
  "operation": "invalidate-pattern",
  "pattern": "user-progress:*"
}

# Flush all cache
POST /api/cache/stats
{
  "operation": "flush"
}

# Reset statistics
POST /api/cache/stats
{
  "operation": "reset-stats"
}

# Ping Redis
POST /api/cache/stats
{
  "operation": "ping"
}
```

### Response Headers

Cached responses include these headers:

```
X-Cache: HIT                          # From cache
X-Cache: MISS                         # From database
Cache-Control: public, max-age=3600   # TTL in seconds
```

### Monitoring Dashboard

Track cache performance:

```typescript
import { getCache } from '@/lib/cache';

const cache = getCache();
const stats = cache.getStats();

console.log(`Hit Rate: ${(stats.hitRate * 100).toFixed(2)}%`);
console.log(`Total Requests: ${stats.hits + stats.misses}`);
console.log(`Cache Size: ${await cache.getSize()} keys`);
```

## Best Practices

### DO ✅

1. **Cache immutable or rarely changing data**
   ```typescript
   // GOOD - Learning paths rarely change
   await cache.set(CacheKeys.learningPaths(), paths, { ttl: 3600 });
   ```

2. **Use appropriate TTLs**
   ```typescript
   // GOOD - Different TTLs for different data
   learningPaths: 1 hour
   userProgress: 5 minutes
   leaderboard: 1 minute
   ```

3. **Tag your cache entries**
   ```typescript
   // GOOD - Easy batch invalidation
   await cache.set(key, data, {
     tags: [CacheTags.LESSONS, CacheTags.LEARNING_PATHS],
   });
   ```

4. **Invalidate on writes**
   ```typescript
   // GOOD - Keep cache fresh
   await db.update(...);
   await invalidateCacheTags([CacheTags.LESSONS]);
   ```

5. **Use stale-while-revalidate for better UX**
   ```typescript
   // GOOD - Fast response, background update
   const data = await getWithRevalidate(key, fetchFn, { ttl: 1800 });
   ```

### DON'T ❌

1. **Don't cache user-specific data with long TTLs**
   ```typescript
   // BAD - User data changes frequently
   await cache.set(`user:${userId}`, userData, { ttl: 3600 });
   
   // GOOD - Short TTL for user data
   await cache.set(`user:${userId}`, userData, { ttl: 300 });
   ```

2. **Don't cache without invalidation strategy**
   ```typescript
   // BAD - No way to invalidate
   await cache.set('some-data', data);
   
   // GOOD - Tagged for invalidation
   await cache.set('some-data', data, { tags: ['my-data'] });
   ```

3. **Don't cache POST/PUT/DELETE requests**
   ```typescript
   // BAD - Mutations shouldn't be cached
   export const POST = withCache(createLesson, { ttl: 3600 });
   
   // GOOD - Only cache GET requests
   export const GET = withCache(getLessons, { ttl: 3600 });
   ```

4. **Don't use very long TTLs without reason**
   ```typescript
   // BAD - Data might become stale
   await cache.set(key, data, { ttl: 86400 }); // 24 hours
   
   // GOOD - Reasonable TTL
   await cache.set(key, data, { ttl: 3600 }); // 1 hour
   ```

## Performance Benchmarks

Expected performance improvements with caching:

| Endpoint | Without Cache | With Cache | Improvement |
|----------|--------------|------------|-------------|
| GET /api/learning-paths | 250ms | 15ms | **16x** |
| GET /api/lessons | 180ms | 12ms | **15x** |
| GET /api/achievements | 120ms | 8ms | **15x** |
| GET /api/user-progress | 200ms | 25ms | **8x** |
| GET /api/leaderboard | 450ms | 20ms | **22x** |

**Database Load Reduction**: 85-90% fewer queries for cached endpoints

## Troubleshooting

### Cache Not Working

1. Check Redis connection:
   ```typescript
   const cache = getCache();
   const connected = cache.isConnected();
   console.log('Redis connected:', connected);
   ```

2. Verify environment variables:
   ```bash
   echo $REDIS_HOST
   echo $REDIS_PORT
   ```

3. Check Redis server is running:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

### High Memory Usage

1. Check cache size:
   ```typescript
   const size = await cache.getSize();
   const info = await cache.getInfo();
   console.log('Keys:', size);
   ```

2. Reduce TTLs for large data:
   ```typescript
   // Instead of 1 hour
   { ttl: 1800 } // 30 minutes
   ```

3. Implement memory limit:
   ```bash
   # In redis.conf
   maxmemory 512mb
   maxmemory-policy allkeys-lru
   ```

### Low Hit Rate

1. Check statistics:
   ```typescript
   const stats = cache.getStats();
   console.log('Hit rate:', stats.hitRate);
   ```

2. Verify key generation is consistent
3. Increase TTLs if data doesn't change often
4. Check if invalidation is too aggressive

## Resources

- [Redis Documentation](https://redis.io/documentation)
- [ioredis Documentation](https://github.com/redis/ioredis)
- [Next.js Caching](https://nextjs.org/docs/app/building-your-application/caching)
- Cache implementation: `src/lib/cache/`
- Example endpoints: `src/app/api/*/cached/route.ts`

---

**Last Updated**: 2024
**Version**: 1.0.0
**Maintained By**: RepoRover AI Team
