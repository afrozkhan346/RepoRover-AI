import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { lessons, learningPaths } from '@/db/schema';
import { eq, like, and, desc } from 'drizzle-orm';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const searchParams = request.nextUrl.searchParams;
    const id = searchParams.get('id');
    const learningPathId = searchParams.get('learningPathId');
    const search = searchParams.get('search');
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '10'), 100);
    const offset = parseInt(searchParams.get('offset') ?? '0');

    // Single record by ID
    if (id) {
      if (!id || isNaN(parseInt(id))) {
        return NextResponse.json({ 
          error: "Valid ID is required",
          code: "INVALID_ID" 
        }, { status: 400 });
      }

      const lesson = await db.select()
        .from(lessons)
        .where(eq(lessons.id, parseInt(id)))
        .limit(1);

      if (lesson.length === 0) {
        return NextResponse.json({ 
          error: 'Lesson not found',
          code: 'LESSON_NOT_FOUND' 
        }, { status: 404 });
      }

      return NextResponse.json(lesson[0], { status: 200 });
    }

    // List with filters
    let query = db.select().from(lessons);
    const conditions = [];

    // Filter by learningPathId
    if (learningPathId) {
      if (isNaN(parseInt(learningPathId))) {
        return NextResponse.json({ 
          error: "Valid learningPathId is required",
          code: "INVALID_LEARNING_PATH_ID" 
        }, { status: 400 });
      }
      conditions.push(eq(lessons.learningPathId, parseInt(learningPathId)));
    }

    // Search by title
    if (search) {
      conditions.push(like(lessons.title, `%${search}%`));
    }

    if (conditions.length > 0) {
      query = query.where(and(...conditions));
    }

    const results = await query
      .orderBy(desc(lessons.orderIndex))
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
    const { learningPathId, title, description, content, difficulty, xpReward, orderIndex, estimatedMinutes } = body;

    // Validate required fields
    if (!learningPathId) {
      return NextResponse.json({ 
        error: "learningPathId is required",
        code: "MISSING_LEARNING_PATH_ID" 
      }, { status: 400 });
    }

    if (!title || title.trim() === '') {
      return NextResponse.json({ 
        error: "title is required",
        code: "MISSING_TITLE" 
      }, { status: 400 });
    }

    if (!difficulty || difficulty.trim() === '') {
      return NextResponse.json({ 
        error: "difficulty is required",
        code: "MISSING_DIFFICULTY" 
      }, { status: 400 });
    }

    if (xpReward === undefined || xpReward === null) {
      return NextResponse.json({ 
        error: "xpReward is required",
        code: "MISSING_XP_REWARD" 
      }, { status: 400 });
    }

    if (orderIndex === undefined || orderIndex === null) {
      return NextResponse.json({ 
        error: "orderIndex is required",
        code: "MISSING_ORDER_INDEX" 
      }, { status: 400 });
    }

    if (estimatedMinutes === undefined || estimatedMinutes === null) {
      return NextResponse.json({ 
        error: "estimatedMinutes is required",
        code: "MISSING_ESTIMATED_MINUTES" 
      }, { status: 400 });
    }

    // Validate learningPathId exists
    const learningPath = await db.select()
      .from(learningPaths)
      .where(eq(learningPaths.id, parseInt(learningPathId)))
      .limit(1);

    if (learningPath.length === 0) {
      return NextResponse.json({ 
        error: "Referenced learning path does not exist",
        code: "INVALID_LEARNING_PATH" 
      }, { status: 400 });
    }

    // Validate numeric fields
    if (isNaN(parseInt(learningPathId))) {
      return NextResponse.json({ 
        error: "learningPathId must be a valid integer",
        code: "INVALID_LEARNING_PATH_ID" 
      }, { status: 400 });
    }

    if (isNaN(parseInt(xpReward))) {
      return NextResponse.json({ 
        error: "xpReward must be a valid integer",
        code: "INVALID_XP_REWARD" 
      }, { status: 400 });
    }

    if (isNaN(parseInt(orderIndex))) {
      return NextResponse.json({ 
        error: "orderIndex must be a valid integer",
        code: "INVALID_ORDER_INDEX" 
      }, { status: 400 });
    }

    if (isNaN(parseInt(estimatedMinutes))) {
      return NextResponse.json({ 
        error: "estimatedMinutes must be a valid integer",
        code: "INVALID_ESTIMATED_MINUTES" 
      }, { status: 400 });
    }

    // Create new lesson
    const newLesson = await db.insert(lessons)
      .values({
        learningPathId: parseInt(learningPathId),
        title: title.trim(),
        description: description ? description.trim() : null,
        content: content ? content.trim() : null,
        difficulty: difficulty.trim(),
        xpReward: parseInt(xpReward),
        orderIndex: parseInt(orderIndex),
        estimatedMinutes: parseInt(estimatedMinutes),
        createdAt: new Date().toISOString()
      })
      .returning();

    return NextResponse.json(newLesson[0], { status: 201 });
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

    const searchParams = request.nextUrl.searchParams;
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json({ 
        error: "Valid ID is required",
        code: "INVALID_ID" 
      }, { status: 400 });
    }

    // Check if lesson exists
    const existingLesson = await db.select()
      .from(lessons)
      .where(eq(lessons.id, parseInt(id)))
      .limit(1);

    if (existingLesson.length === 0) {
      return NextResponse.json({ 
        error: 'Lesson not found',
        code: 'LESSON_NOT_FOUND' 
      }, { status: 404 });
    }

    const body = await request.json();
    const { learningPathId, title, description, content, difficulty, xpReward, orderIndex, estimatedMinutes } = body;

    const updates: any = {};

    // Validate and add fields to update
    if (learningPathId !== undefined) {
      if (isNaN(parseInt(learningPathId))) {
        return NextResponse.json({ 
          error: "learningPathId must be a valid integer",
          code: "INVALID_LEARNING_PATH_ID" 
        }, { status: 400 });
      }

      // Validate learningPathId exists
      const learningPath = await db.select()
        .from(learningPaths)
        .where(eq(learningPaths.id, parseInt(learningPathId)))
        .limit(1);

      if (learningPath.length === 0) {
        return NextResponse.json({ 
          error: "Referenced learning path does not exist",
          code: "INVALID_LEARNING_PATH" 
        }, { status: 400 });
      }

      updates.learningPathId = parseInt(learningPathId);
    }

    if (title !== undefined) {
      if (!title || title.trim() === '') {
        return NextResponse.json({ 
          error: "title cannot be empty",
          code: "INVALID_TITLE" 
        }, { status: 400 });
      }
      updates.title = title.trim();
    }

    if (description !== undefined) {
      updates.description = description ? description.trim() : null;
    }

    if (content !== undefined) {
      updates.content = content ? content.trim() : null;
    }

    if (difficulty !== undefined) {
      if (!difficulty || difficulty.trim() === '') {
        return NextResponse.json({ 
          error: "difficulty cannot be empty",
          code: "INVALID_DIFFICULTY" 
        }, { status: 400 });
      }
      updates.difficulty = difficulty.trim();
    }

    if (xpReward !== undefined) {
      if (isNaN(parseInt(xpReward))) {
        return NextResponse.json({ 
          error: "xpReward must be a valid integer",
          code: "INVALID_XP_REWARD" 
        }, { status: 400 });
      }
      updates.xpReward = parseInt(xpReward);
    }

    if (orderIndex !== undefined) {
      if (isNaN(parseInt(orderIndex))) {
        return NextResponse.json({ 
          error: "orderIndex must be a valid integer",
          code: "INVALID_ORDER_INDEX" 
        }, { status: 400 });
      }
      updates.orderIndex = parseInt(orderIndex);
    }

    if (estimatedMinutes !== undefined) {
      if (isNaN(parseInt(estimatedMinutes))) {
        return NextResponse.json({ 
          error: "estimatedMinutes must be a valid integer",
          code: "INVALID_ESTIMATED_MINUTES" 
        }, { status: 400 });
      }
      updates.estimatedMinutes = parseInt(estimatedMinutes);
    }

    // If no updates provided, return current record
    if (Object.keys(updates).length === 0) {
      return NextResponse.json(existingLesson[0], { status: 200 });
    }

    // Update lesson
    const updated = await db.update(lessons)
      .set(updates)
      .where(eq(lessons.id, parseInt(id)))
      .returning();

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

    const searchParams = request.nextUrl.searchParams;
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json({ 
        error: "Valid ID is required",
        code: "INVALID_ID" 
      }, { status: 400 });
    }

    // Check if lesson exists
    const existingLesson = await db.select()
      .from(lessons)
      .where(eq(lessons.id, parseInt(id)))
      .limit(1);

    if (existingLesson.length === 0) {
      return NextResponse.json({ 
        error: 'Lesson not found',
        code: 'LESSON_NOT_FOUND' 
      }, { status: 404 });
    }

    // Delete lesson
    const deleted = await db.delete(lessons)
      .where(eq(lessons.id, parseInt(id)))
      .returning();

    return NextResponse.json({
      message: 'Lesson deleted successfully',
      lesson: deleted[0]
    }, { status: 200 });
  } catch (error) {
    console.error('DELETE error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}