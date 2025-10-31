import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { quizAttempts } from '@/db/schema';
import { eq, and, desc } from 'drizzle-orm';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const userIdFilter = searchParams.get('userId');
    const quizIdFilter = searchParams.get('quizId');

    // Single record by ID
    if (id) {
      if (!id || isNaN(parseInt(id))) {
        return NextResponse.json({ 
          error: "Valid ID is required",
          code: "INVALID_ID" 
        }, { status: 400 });
      }

      const attempt = await db.select()
        .from(quizAttempts)
        .where(and(
          eq(quizAttempts.id, parseInt(id)),
          eq(quizAttempts.userId, user.id)
        ))
        .limit(1);

      if (attempt.length === 0) {
        return NextResponse.json({ 
          error: 'Quiz attempt not found',
          code: 'NOT_FOUND' 
        }, { status: 404 });
      }

      return NextResponse.json(attempt[0], { status: 200 });
    }

    // List with pagination and filters
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '10'), 100);
    const offset = parseInt(searchParams.get('offset') ?? '0');

    let query = db.select().from(quizAttempts);

    // Build filter conditions
    const conditions = [eq(quizAttempts.userId, user.id)];

    if (userIdFilter) {
      // Only allow filtering by own userId
      if (userIdFilter !== user.id) {
        return NextResponse.json({ 
          error: 'Cannot access other users\' quiz attempts',
          code: 'UNAUTHORIZED_ACCESS' 
        }, { status: 403 });
      }
    }

    if (quizIdFilter) {
      if (isNaN(parseInt(quizIdFilter))) {
        return NextResponse.json({ 
          error: "Valid quiz ID is required",
          code: "INVALID_QUIZ_ID" 
        }, { status: 400 });
      }
      conditions.push(eq(quizAttempts.quizId, parseInt(quizIdFilter)));
    }

    query = query.where(and(...conditions));

    const results = await query
      .orderBy(desc(quizAttempts.attemptedAt))
      .limit(limit)
      .offset(offset);

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
    const user = await getCurrentUser(request);
    if (!user) {
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

    const { quizId, userAnswer, isCorrect } = body;

    // Validate required fields
    if (!quizId) {
      return NextResponse.json({ 
        error: "Quiz ID is required",
        code: "MISSING_QUIZ_ID" 
      }, { status: 400 });
    }

    if (!userAnswer) {
      return NextResponse.json({ 
        error: "User answer is required",
        code: "MISSING_USER_ANSWER" 
      }, { status: 400 });
    }

    if (typeof isCorrect !== 'boolean') {
      return NextResponse.json({ 
        error: "isCorrect must be a boolean value",
        code: "INVALID_IS_CORRECT" 
      }, { status: 400 });
    }

    // Validate quizId is a valid integer
    if (isNaN(parseInt(quizId))) {
      return NextResponse.json({ 
        error: "Quiz ID must be a valid integer",
        code: "INVALID_QUIZ_ID" 
      }, { status: 400 });
    }

    const currentTimestamp = new Date().toISOString();

    const newAttempt = await db.insert(quizAttempts)
      .values({
        userId: user.id,
        quizId: parseInt(quizId),
        userAnswer: userAnswer.trim(),
        isCorrect: isCorrect,
        attemptedAt: currentTimestamp,
        createdAt: currentTimestamp,
      })
      .returning();

    return NextResponse.json(newAttempt[0], { status: 201 });

  } catch (error) {
    console.error('POST error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}

export async function PUT(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json({ 
        error: "Valid ID is required",
        code: "INVALID_ID" 
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
      .from(quizAttempts)
      .where(and(
        eq(quizAttempts.id, parseInt(id)),
        eq(quizAttempts.userId, user.id)
      ))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json({ 
        error: 'Quiz attempt not found',
        code: 'NOT_FOUND' 
      }, { status: 404 });
    }

    const { userAnswer, isCorrect, attemptedAt } = body;

    // Build update object with only provided fields
    const updates: Record<string, any> = {};

    if (userAnswer !== undefined) {
      updates.userAnswer = userAnswer.trim();
    }

    if (isCorrect !== undefined) {
      if (typeof isCorrect !== 'boolean') {
        return NextResponse.json({ 
          error: "isCorrect must be a boolean value",
          code: "INVALID_IS_CORRECT" 
        }, { status: 400 });
      }
      updates.isCorrect = isCorrect;
    }

    if (attemptedAt !== undefined) {
      updates.attemptedAt = attemptedAt;
    }

    // If no valid updates provided
    if (Object.keys(updates).length === 0) {
      return NextResponse.json({ 
        error: "No valid fields to update",
        code: "NO_UPDATES" 
      }, { status: 400 });
    }

    const updated = await db.update(quizAttempts)
      .set(updates)
      .where(and(
        eq(quizAttempts.id, parseInt(id)),
        eq(quizAttempts.userId, user.id)
      ))
      .returning();

    if (updated.length === 0) {
      return NextResponse.json({ 
        error: 'Quiz attempt not found',
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
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json({ 
        error: "Valid ID is required",
        code: "INVALID_ID" 
      }, { status: 400 });
    }

    // Check if record exists and belongs to user
    const existing = await db.select()
      .from(quizAttempts)
      .where(and(
        eq(quizAttempts.id, parseInt(id)),
        eq(quizAttempts.userId, user.id)
      ))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json({ 
        error: 'Quiz attempt not found',
        code: 'NOT_FOUND' 
      }, { status: 404 });
    }

    const deleted = await db.delete(quizAttempts)
      .where(and(
        eq(quizAttempts.id, parseInt(id)),
        eq(quizAttempts.userId, user.id)
      ))
      .returning();

    if (deleted.length === 0) {
      return NextResponse.json({ 
        error: 'Quiz attempt not found',
        code: 'NOT_FOUND' 
      }, { status: 404 });
    }

    return NextResponse.json({ 
      message: 'Quiz attempt deleted successfully',
      deleted: deleted[0]
    }, { status: 200 });

  } catch (error) {
    console.error('DELETE error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}