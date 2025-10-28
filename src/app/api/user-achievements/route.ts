import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { userAchievements, user, achievements } from '@/db/schema';
import { eq, and } from 'drizzle-orm';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const currentUser = await getCurrentUser(request);
    if (!currentUser) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const userIdFilter = searchParams.get('userId');
    const achievementIdFilter = searchParams.get('achievementId');

    // Single record by ID (user-scoped)
    if (id) {
      if (isNaN(parseInt(id))) {
        return NextResponse.json({ 
          error: 'Valid ID is required',
          code: 'INVALID_ID' 
        }, { status: 400 });
      }

      const record = await db.select()
        .from(userAchievements)
        .where(and(
          eq(userAchievements.id, parseInt(id)),
          eq(userAchievements.userId, currentUser.id)
        ))
        .limit(1);

      if (record.length === 0) {
        return NextResponse.json({ 
          error: 'Record not found',
          code: 'NOT_FOUND' 
        }, { status: 404 });
      }

      return NextResponse.json(record[0], { status: 200 });
    }

    // List with pagination and filters (user-scoped)
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '10'), 100);
    const offset = parseInt(searchParams.get('offset') ?? '0');

    let query = db.select().from(userAchievements);

    // Build conditions
    const conditions = [eq(userAchievements.userId, currentUser.id)];

    if (userIdFilter) {
      conditions.push(eq(userAchievements.userId, userIdFilter));
    }

    if (achievementIdFilter) {
      if (isNaN(parseInt(achievementIdFilter))) {
        return NextResponse.json({ 
          error: 'Valid achievement ID is required',
          code: 'INVALID_ACHIEVEMENT_ID' 
        }, { status: 400 });
      }
      conditions.push(eq(userAchievements.achievementId, parseInt(achievementIdFilter)));
    }

    query = query.where(and(...conditions));
    const results = await query.limit(limit).offset(offset);

    return NextResponse.json(results, { status: 200 });
  } catch (error) {
    console.error('GET error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const currentUser = await getCurrentUser(request);
    if (!currentUser) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const body = await request.json();

    // Security check: reject if userId provided in body
    if ('userId' in body || 'user_id' in body) {
      return NextResponse.json({ 
        error: "User ID cannot be provided in request body",
        code: "USER_ID_NOT_ALLOWED" 
      }, { status: 400 });
    }

    const { achievementId } = body;

    // Validate required fields
    if (!achievementId) {
      return NextResponse.json({ 
        error: 'achievementId is required',
        code: 'MISSING_ACHIEVEMENT_ID' 
      }, { status: 400 });
    }

    // Validate achievementId is valid integer
    if (isNaN(parseInt(achievementId))) {
      return NextResponse.json({ 
        error: 'Valid achievement ID is required',
        code: 'INVALID_ACHIEVEMENT_ID' 
      }, { status: 400 });
    }

    // Verify achievement exists
    const achievementExists = await db.select()
      .from(achievements)
      .where(eq(achievements.id, parseInt(achievementId)))
      .limit(1);

    if (achievementExists.length === 0) {
      return NextResponse.json({ 
        error: 'Achievement not found',
        code: 'ACHIEVEMENT_NOT_FOUND' 
      }, { status: 404 });
    }

    const now = new Date().toISOString();

    const newRecord = await db.insert(userAchievements)
      .values({
        userId: currentUser.id,
        achievementId: parseInt(achievementId),
        earnedAt: now,
        createdAt: now,
      })
      .returning();

    return NextResponse.json(newRecord[0], { status: 201 });
  } catch (error) {
    console.error('POST error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  try {
    const currentUser = await getCurrentUser(request);
    if (!currentUser) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json({ 
        error: 'Valid ID is required',
        code: 'INVALID_ID' 
      }, { status: 400 });
    }

    const body = await request.json();

    // Security check: reject if userId provided in body
    if ('userId' in body || 'user_id' in body) {
      return NextResponse.json({ 
        error: "User ID cannot be provided in request body",
        code: "USER_ID_NOT_ALLOWED" 
      }, { status: 400 });
    }

    // Check if record exists and belongs to user
    const existing = await db.select()
      .from(userAchievements)
      .where(and(
        eq(userAchievements.id, parseInt(id)),
        eq(userAchievements.userId, currentUser.id)
      ))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json({ 
        error: 'Record not found',
        code: 'NOT_FOUND' 
      }, { status: 404 });
    }

    const { earnedAt } = body;
    const updates: { earnedAt?: string } = {};

    if (earnedAt !== undefined) {
      updates.earnedAt = earnedAt;
    }

    const updated = await db.update(userAchievements)
      .set(updates)
      .where(and(
        eq(userAchievements.id, parseInt(id)),
        eq(userAchievements.userId, currentUser.id)
      ))
      .returning();

    if (updated.length === 0) {
      return NextResponse.json({ 
        error: 'Record not found',
        code: 'NOT_FOUND' 
      }, { status: 404 });
    }

    return NextResponse.json(updated[0], { status: 200 });
  } catch (error) {
    console.error('PUT error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const currentUser = await getCurrentUser(request);
    if (!currentUser) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json({ 
        error: 'Valid ID is required',
        code: 'INVALID_ID' 
      }, { status: 400 });
    }

    // Check if record exists and belongs to user
    const existing = await db.select()
      .from(userAchievements)
      .where(and(
        eq(userAchievements.id, parseInt(id)),
        eq(userAchievements.userId, currentUser.id)
      ))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json({ 
        error: 'Record not found',
        code: 'NOT_FOUND' 
      }, { status: 404 });
    }

    const deleted = await db.delete(userAchievements)
      .where(and(
        eq(userAchievements.id, parseInt(id)),
        eq(userAchievements.userId, currentUser.id)
      ))
      .returning();

    if (deleted.length === 0) {
      return NextResponse.json({ 
        error: 'Record not found',
        code: 'NOT_FOUND' 
      }, { status: 404 });
    }

    return NextResponse.json({
      message: 'Record deleted successfully',
      record: deleted[0]
    }, { status: 200 });
  } catch (error) {
    console.error('DELETE error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}