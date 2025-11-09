import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { achievements } from '@/db/schema';
import { eq } from 'drizzle-orm';
import { withCache, CacheKeys, CacheTags } from '@/lib/cache';

/**
 * GET /api/achievements/cached
 * Cached version of achievements endpoint
 */
async function getAchievements(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    // Single achievement by ID
    if (id) {
      const achievementId = parseInt(id);
      if (isNaN(achievementId)) {
        return NextResponse.json(
          { error: 'Valid ID is required', code: 'INVALID_ID' },
          { status: 400 }
        );
      }

      const record = await db
        .select()
        .from(achievements)
        .where(eq(achievements.id, achievementId))
        .limit(1);

      if (record.length === 0) {
        return NextResponse.json(
          { error: 'Achievement not found', code: 'NOT_FOUND' },
          { status: 404 }
        );
      }

      return NextResponse.json(record[0], { status: 200 });
    }

    // All achievements
    const allAchievements = await db
      .select()
      .from(achievements);

    return NextResponse.json(allAchievements, { status: 200 });
  } catch (error) {
    console.error('Error fetching achievements:', error);
    return NextResponse.json(
      { error: 'Failed to fetch achievements', code: 'FETCH_ERROR' },
      { status: 500 }
    );
  }
}

/**
 * Export cached GET handler
 * - Cache for 1 hour (3600 seconds) - achievements rarely change
 * - Tagged for invalidation
 */
export const GET = withCache(getAchievements, {
  ttl: 3600, // 1 hour
  tags: [CacheTags.ACHIEVEMENTS],
  keyGenerator: (req) => {
    const url = new URL(req.url);
    const id = url.searchParams.get('id');
    
    if (id) {
      return CacheKeys.achievement(id);
    }
    
    return CacheKeys.achievements();
  },
});
