import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { learningPaths } from '@/db/schema';
import { eq, like, and, or, desc, asc } from 'drizzle-orm';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const search = searchParams.get('search');
    const difficulty = searchParams.get('difficulty');
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '10'), 100);
    const offset = parseInt(searchParams.get('offset') ?? '0');
    const sort = searchParams.get('sort') ?? 'orderIndex';
    const order = searchParams.get('order') ?? 'asc';

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
        .from(learningPaths)
        .where(eq(learningPaths.id, parseInt(id)))
        .limit(1);

      if (record.length === 0) {
        return NextResponse.json(
          { error: 'Learning path not found', code: 'NOT_FOUND' },
          { status: 404 }
        );
      }

      return NextResponse.json(record[0], { status: 200 });
    }

    // List with filtering and search
    let query = db.select().from(learningPaths);

    // Build where conditions
    const conditions = [];

    if (search) {
      conditions.push(
        or(
          like(learningPaths.title, `%${search}%`),
          like(learningPaths.description, `%${search}%`)
        )
      );
    }

    if (difficulty) {
      conditions.push(eq(learningPaths.difficulty, difficulty));
    }

    if (conditions.length > 0) {
      query = query.where(conditions.length === 1 ? conditions[0] : and(...conditions));
    }

    // Apply sorting
    const orderColumn = sort === 'createdAt' ? learningPaths.createdAt :
                       sort === 'title' ? learningPaths.title :
                       sort === 'difficulty' ? learningPaths.difficulty :
                       sort === 'estimatedHours' ? learningPaths.estimatedHours :
                       learningPaths.orderIndex;

    query = query.orderBy(order === 'desc' ? desc(orderColumn) : asc(orderColumn));

    // Apply pagination
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
    const body = await request.json();
    const { title, description, difficulty, estimatedHours, icon, orderIndex } = body;

    // Validate required fields
    if (!title) {
      return NextResponse.json(
        { error: 'Title is required', code: 'MISSING_TITLE' },
        { status: 400 }
      );
    }

    if (!difficulty) {
      return NextResponse.json(
        { error: 'Difficulty is required', code: 'MISSING_DIFFICULTY' },
        { status: 400 }
      );
    }

    if (estimatedHours === undefined || estimatedHours === null) {
      return NextResponse.json(
        { error: 'Estimated hours is required', code: 'MISSING_ESTIMATED_HOURS' },
        { status: 400 }
      );
    }

    if (orderIndex === undefined || orderIndex === null) {
      return NextResponse.json(
        { error: 'Order index is required', code: 'MISSING_ORDER_INDEX' },
        { status: 400 }
      );
    }

    // Validate data types
    if (typeof title !== 'string' || title.trim().length === 0) {
      return NextResponse.json(
        { error: 'Title must be a non-empty string', code: 'INVALID_TITLE' },
        { status: 400 }
      );
    }

    if (typeof difficulty !== 'string' || difficulty.trim().length === 0) {
      return NextResponse.json(
        { error: 'Difficulty must be a non-empty string', code: 'INVALID_DIFFICULTY' },
        { status: 400 }
      );
    }

    if (typeof estimatedHours !== 'number' || estimatedHours <= 0) {
      return NextResponse.json(
        { error: 'Estimated hours must be a positive number', code: 'INVALID_ESTIMATED_HOURS' },
        { status: 400 }
      );
    }

    if (typeof orderIndex !== 'number' || orderIndex < 0) {
      return NextResponse.json(
        { error: 'Order index must be a non-negative number', code: 'INVALID_ORDER_INDEX' },
        { status: 400 }
      );
    }

    // Sanitize inputs
    const sanitizedTitle = title.trim();
    const sanitizedDifficulty = difficulty.trim();
    const sanitizedDescription = description ? description.trim() : null;
    const sanitizedIcon = icon ? icon.trim() : null;

    // Create new learning path
    const newLearningPath = await db
      .insert(learningPaths)
      .values({
        title: sanitizedTitle,
        description: sanitizedDescription,
        difficulty: sanitizedDifficulty,
        estimatedHours,
        icon: sanitizedIcon,
        orderIndex,
        createdAt: new Date().toISOString(),
      })
      .returning();

    return NextResponse.json(newLearningPath[0], { status: 201 });
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
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json(
        { error: 'Valid ID is required', code: 'INVALID_ID' },
        { status: 400 }
      );
    }

    // Check if record exists
    const existing = await db
      .select()
      .from(learningPaths)
      .where(eq(learningPaths.id, parseInt(id)))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json(
        { error: 'Learning path not found', code: 'NOT_FOUND' },
        { status: 404 }
      );
    }

    const body = await request.json();
    const { title, description, difficulty, estimatedHours, icon, orderIndex } = body;

    // Build update object with only provided fields
    const updates: Record<string, any> = {};

    if (title !== undefined) {
      if (typeof title !== 'string' || title.trim().length === 0) {
        return NextResponse.json(
          { error: 'Title must be a non-empty string', code: 'INVALID_TITLE' },
          { status: 400 }
        );
      }
      updates.title = title.trim();
    }

    if (description !== undefined) {
      updates.description = description ? description.trim() : null;
    }

    if (difficulty !== undefined) {
      if (typeof difficulty !== 'string' || difficulty.trim().length === 0) {
        return NextResponse.json(
          { error: 'Difficulty must be a non-empty string', code: 'INVALID_DIFFICULTY' },
          { status: 400 }
        );
      }
      updates.difficulty = difficulty.trim();
    }

    if (estimatedHours !== undefined) {
      if (typeof estimatedHours !== 'number' || estimatedHours <= 0) {
        return NextResponse.json(
          { error: 'Estimated hours must be a positive number', code: 'INVALID_ESTIMATED_HOURS' },
          { status: 400 }
        );
      }
      updates.estimatedHours = estimatedHours;
    }

    if (icon !== undefined) {
      updates.icon = icon ? icon.trim() : null;
    }

    if (orderIndex !== undefined) {
      if (typeof orderIndex !== 'number' || orderIndex < 0) {
        return NextResponse.json(
          { error: 'Order index must be a non-negative number', code: 'INVALID_ORDER_INDEX' },
          { status: 400 }
        );
      }
      updates.orderIndex = orderIndex;
    }

    // If no fields to update, return current record
    if (Object.keys(updates).length === 0) {
      return NextResponse.json(existing[0], { status: 200 });
    }

    // Update the record
    const updated = await db
      .update(learningPaths)
      .set(updates)
      .where(eq(learningPaths.id, parseInt(id)))
      .returning();

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
    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json(
        { error: 'Valid ID is required', code: 'INVALID_ID' },
        { status: 400 }
      );
    }

    // Check if record exists
    const existing = await db
      .select()
      .from(learningPaths)
      .where(eq(learningPaths.id, parseInt(id)))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json(
        { error: 'Learning path not found', code: 'NOT_FOUND' },
        { status: 404 }
      );
    }

    // Delete the record
    const deleted = await db
      .delete(learningPaths)
      .where(eq(learningPaths.id, parseInt(id)))
      .returning();

    return NextResponse.json(
      {
        message: 'Learning path deleted successfully',
        data: deleted[0],
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