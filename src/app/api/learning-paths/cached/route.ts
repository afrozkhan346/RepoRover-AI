import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { learningPaths } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { withCache, CacheKeys, CacheTags } from '@/lib/cache';

/**
 * GET /api/learning-paths/cached
 * Cached version of learning paths endpoint with Redis caching
 */
async function getLearningPaths(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    // Single record by ID
    if (id) {
      const pathId = parseInt(id);
      if (isNaN(pathId)) {
        return NextResponse.json(
          { error: 'Valid ID is required', code: 'INVALID_ID' },
          { status: 400 }
        );
      }

      const record = await db
        .select()
        .from(learningPaths)
        .where(eq(learningPaths.id, pathId))
        .limit(1);

      if (record.length === 0) {
        return NextResponse.json(
          { error: 'Learning path not found', code: 'NOT_FOUND' },
          { status: 404 }
        );
      }

      return NextResponse.json(record[0], { status: 200 });
    }

    // Get all learning paths
    const allPaths = await db
      .select()
      .from(learningPaths)
      .orderBy(learningPaths.orderIndex);

    return NextResponse.json(allPaths, { status: 200 });
  } catch (error) {
    console.error('Error fetching learning paths:', error);
    return NextResponse.json(
      { error: 'Failed to fetch learning paths', code: 'FETCH_ERROR' },
      { status: 500 }
    );
  }
}

/**
 * Export cached GET handler
 * - Cache for 1 hour (3600 seconds)
 * - Tagged for invalidation
 * - Custom key generator based on query params
 */
export const GET = withCache(getLearningPaths, {
  ttl: 3600, // 1 hour
  tags: [CacheTags.LEARNING_PATHS],
  keyGenerator: (req) => {
    const url = new URL(req.url);
    const id = url.searchParams.get('id');
    
    if (id) {
      return CacheKeys.learningPath(id);
    }
    
    return CacheKeys.learningPaths();
  },
});
