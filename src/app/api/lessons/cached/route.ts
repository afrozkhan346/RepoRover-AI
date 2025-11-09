import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { lessons } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { withCache, CacheKeys, CacheTags } from '@/lib/cache';

/**
 * GET /api/lessons/cached
 * Cached version of lessons endpoint
 */
async function getLessons(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const learningPathId = searchParams.get('learningPathId');

    // Single lesson by ID
    if (id) {
      const lessonId = parseInt(id);
      if (isNaN(lessonId)) {
        return NextResponse.json(
          { error: 'Valid ID is required', code: 'INVALID_ID' },
          { status: 400 }
        );
      }

      const record = await db
        .select()
        .from(lessons)
        .where(eq(lessons.id, lessonId))
        .limit(1);

      if (record.length === 0) {
        return NextResponse.json(
          { error: 'Lesson not found', code: 'NOT_FOUND' },
          { status: 404 }
        );
      }

      return NextResponse.json(record[0], { status: 200 });
    }

    // Lessons by learning path
    if (learningPathId) {
      const pathId = parseInt(learningPathId);
      if (isNaN(pathId)) {
        return NextResponse.json(
          { error: 'Valid learning path ID is required', code: 'INVALID_PATH_ID' },
          { status: 400 }
        );
      }

      const pathLessons = await db
        .select()
        .from(lessons)
        .where(eq(lessons.learningPathId, pathId))
        .orderBy(lessons.orderIndex);

      return NextResponse.json(pathLessons, { status: 200 });
    }

    // All lessons
    const allLessons = await db
      .select()
      .from(lessons)
      .orderBy(lessons.orderIndex)
      .limit(100);

    return NextResponse.json(allLessons, { status: 200 });
  } catch (error) {
    console.error('Error fetching lessons:', error);
    return NextResponse.json(
      { error: 'Failed to fetch lessons', code: 'FETCH_ERROR' },
      { status: 500 }
    );
  }
}

/**
 * Export cached GET handler
 * - Cache for 30 minutes (1800 seconds)
 * - Tagged for invalidation
 */
export const GET = withCache(getLessons, {
  ttl: 1800, // 30 minutes
  tags: [CacheTags.LESSONS],
  keyGenerator: (req) => {
    const url = new URL(req.url);
    const id = url.searchParams.get('id');
    const learningPathId = url.searchParams.get('learningPathId');
    
    if (id) {
      return CacheKeys.lesson(id);
    }
    
    if (learningPathId) {
      return CacheKeys.lessonsByPath(learningPathId);
    }
    
    return 'lessons:all';
  },
});
