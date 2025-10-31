import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { lessonProgress } from '@/db/schema';
import { eq, and } from 'drizzle-orm';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json(
        { error: 'Authentication required', code: 'AUTH_REQUIRED' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const lessonId = searchParams.get('lessonId');
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '10'), 100);
    const offset = parseInt(searchParams.get('offset') ?? '0');

    // Single record by ID
    if (id) {
      if (!id || isNaN(parseInt(id))) {
        return NextResponse.json(
          { error: 'Valid ID is required', code: 'INVALID_ID' },
          { status: 400 }
        );
      }

      const record = await db
        .select()
        .from(lessonProgress)
        .where(
          and(
            eq(lessonProgress.id, parseInt(id)),
            eq(lessonProgress.userId, user.id)
          )
        )
        .limit(1);

      if (record.length === 0) {
        return NextResponse.json(
          { error: 'Lesson progress not found', code: 'NOT_FOUND' },
          { status: 404 }
        );
      }

      return NextResponse.json(record[0], { status: 200 });
    }

    // List with filters
    let query = db.select().from(lessonProgress);

    // Always scope to authenticated user
    if (lessonId) {
      if (isNaN(parseInt(lessonId))) {
        return NextResponse.json(
          { error: 'Valid lesson ID is required', code: 'INVALID_LESSON_ID' },
          { status: 400 }
        );
      }
      query = query.where(
        and(
          eq(lessonProgress.userId, user.id),
          eq(lessonProgress.lessonId, parseInt(lessonId))
        )
      );
    } else {
      query = query.where(eq(lessonProgress.userId, user.id));
    }

    const results = await query.limit(limit).offset(offset);

    return NextResponse.json(results, { status: 200 });
  } catch (error) {
    console.error('GET error:', error);
    return NextResponse.json(
      { error: 'Internal server error: ' + (error as Error).message },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json(
        { error: 'Authentication required', code: 'AUTH_REQUIRED' },
        { status: 401 }
      );
    }

    const body = await request.json();

    // Security check: reject if userId provided in body
    if ('userId' in body || 'user_id' in body) {
      return NextResponse.json(
        {
          error: 'User ID cannot be provided in request body',
          code: 'USER_ID_NOT_ALLOWED',
        },
        { status: 400 }
      );
    }

    const { lessonId, status, startedAt, completedAt } = body;

    // Validate required fields
    if (!lessonId) {
      return NextResponse.json(
        { error: 'Lesson ID is required', code: 'MISSING_LESSON_ID' },
        { status: 400 }
      );
    }

    if (!status) {
      return NextResponse.json(
        { error: 'Status is required', code: 'MISSING_STATUS' },
        { status: 400 }
      );
    }

    if (isNaN(parseInt(lessonId))) {
      return NextResponse.json(
        { error: 'Valid lesson ID is required', code: 'INVALID_LESSON_ID' },
        { status: 400 }
      );
    }

    // Create new lesson progress record
    const now = new Date().toISOString();
    const newRecord = await db
      .insert(lessonProgress)
      .values({
        userId: user.id,
        lessonId: parseInt(lessonId),
        status: status.trim(),
        startedAt: startedAt || null,
        completedAt: completedAt || null,
        createdAt: now,
        updatedAt: now,
      })
      .returning();

    return NextResponse.json(newRecord[0], { status: 201 });
  } catch (error) {
    console.error('POST error:', error);
    return NextResponse.json(
      { error: 'Internal server error: ' + (error as Error).message },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json(
        { error: 'Authentication required', code: 'AUTH_REQUIRED' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    // Validate ID
    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json(
        { error: 'Valid ID is required', code: 'INVALID_ID' },
        { status: 400 }
      );
    }

    const body = await request.json();

    // Security check: reject if userId provided in body
    if ('userId' in body || 'user_id' in body) {
      return NextResponse.json(
        {
          error: 'User ID cannot be provided in request body',
          code: 'USER_ID_NOT_ALLOWED',
        },
        { status: 400 }
      );
    }

    // Check if record exists and belongs to user
    const existing = await db
      .select()
      .from(lessonProgress)
      .where(
        and(
          eq(lessonProgress.id, parseInt(id)),
          eq(lessonProgress.userId, user.id)
        )
      )
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json(
        { error: 'Lesson progress not found', code: 'NOT_FOUND' },
        { status: 404 }
      );
    }

    // Prepare update data
    const updates: {
      status?: string;
      startedAt?: string | null;
      completedAt?: string | null;
      updatedAt: string;
    } = {
      updatedAt: new Date().toISOString(),
    };

    if (body.status !== undefined) {
      updates.status = body.status.trim();
    }

    if (body.startedAt !== undefined) {
      updates.startedAt = body.startedAt;
    }

    if (body.completedAt !== undefined) {
      updates.completedAt = body.completedAt;
    }

    // Update record
    const updated = await db
      .update(lessonProgress)
      .set(updates)
      .where(
        and(
          eq(lessonProgress.id, parseInt(id)),
          eq(lessonProgress.userId, user.id)
        )
      )
      .returning();

    if (updated.length === 0) {
      return NextResponse.json(
        { error: 'Failed to update lesson progress', code: 'UPDATE_FAILED' },
        { status: 500 }
      );
    }

    return NextResponse.json(updated[0], { status: 200 });
  } catch (error) {
    console.error('PUT error:', error);
    return NextResponse.json(
      { error: 'Internal server error: ' + (error as Error).message },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json(
        { error: 'Authentication required', code: 'AUTH_REQUIRED' },
        { status: 401 }
      );
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    // Validate ID
    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json(
        { error: 'Valid ID is required', code: 'INVALID_ID' },
        { status: 400 }
      );
    }

    // Check if record exists and belongs to user
    const existing = await db
      .select()
      .from(lessonProgress)
      .where(
        and(
          eq(lessonProgress.id, parseInt(id)),
          eq(lessonProgress.userId, user.id)
        )
      )
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json(
        { error: 'Lesson progress not found', code: 'NOT_FOUND' },
        { status: 404 }
      );
    }

    // Delete record
    const deleted = await db
      .delete(lessonProgress)
      .where(
        and(
          eq(lessonProgress.id, parseInt(id)),
          eq(lessonProgress.userId, user.id)
        )
      )
      .returning();

    return NextResponse.json(
      {
        message: 'Lesson progress deleted successfully',
        deleted: deleted[0],
      },
      { status: 200 }
    );
  } catch (error) {
    console.error('DELETE error:', error);
    return NextResponse.json(
      { error: 'Internal server error: ' + (error as Error).message },
      { status: 500 }
    );
  }
}