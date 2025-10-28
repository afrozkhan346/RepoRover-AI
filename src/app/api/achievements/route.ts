import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { achievements } from '@/db/schema';
import { eq, like, and, desc } from 'drizzle-orm';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const id = searchParams.get('id');

    // Single record fetch by ID
    if (id) {
      if (!id || isNaN(parseInt(id))) {
        return NextResponse.json(
          { error: 'Valid ID is required', code: 'INVALID_ID' },
          { status: 400 }
        );
      }

      const achievement = await db
        .select()
        .from(achievements)
        .where(eq(achievements.id, parseInt(id)))
        .limit(1);

      if (achievement.length === 0) {
        return NextResponse.json(
          { error: 'Achievement not found', code: 'NOT_FOUND' },
          { status: 404 }
        );
      }

      return NextResponse.json(achievement[0], { status: 200 });
    }

    // List with pagination, search, and filtering
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '10'), 100);
    const offset = parseInt(searchParams.get('offset') ?? '0');
    const search = searchParams.get('search');
    const requirementType = searchParams.get('requirementType');

    let query = db.select().from(achievements);

    // Build where conditions
    const conditions = [];

    if (search) {
      conditions.push(like(achievements.title, `%${search}%`));
    }

    if (requirementType) {
      conditions.push(eq(achievements.requirementType, requirementType));
    }

    if (conditions.length > 0) {
      query = query.where(and(...conditions));
    }

    const results = await query
      .orderBy(desc(achievements.createdAt))
      .limit(limit)
      .offset(offset);

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
    const { title, description, icon, xpReward, requirementType, requirementValue } = body;

    // Validate required fields
    if (!title || title.trim() === '') {
      return NextResponse.json(
        { error: 'Title is required', code: 'MISSING_TITLE' },
        { status: 400 }
      );
    }

    if (xpReward === undefined || xpReward === null) {
      return NextResponse.json(
        { error: 'XP reward is required', code: 'MISSING_XP_REWARD' },
        { status: 400 }
      );
    }

    if (typeof xpReward !== 'number' || isNaN(xpReward)) {
      return NextResponse.json(
        { error: 'XP reward must be a valid number', code: 'INVALID_XP_REWARD' },
        { status: 400 }
      );
    }

    if (!requirementType || requirementType.trim() === '') {
      return NextResponse.json(
        { error: 'Requirement type is required', code: 'MISSING_REQUIREMENT_TYPE' },
        { status: 400 }
      );
    }

    if (requirementValue === undefined || requirementValue === null) {
      return NextResponse.json(
        { error: 'Requirement value is required', code: 'MISSING_REQUIREMENT_VALUE' },
        { status: 400 }
      );
    }

    if (typeof requirementValue !== 'number' || isNaN(requirementValue)) {
      return NextResponse.json(
        { error: 'Requirement value must be a valid number', code: 'INVALID_REQUIREMENT_VALUE' },
        { status: 400 }
      );
    }

    // Prepare insert data
    const insertData = {
      title: title.trim(),
      description: description ? description.trim() : null,
      icon: icon ? icon.trim() : null,
      xpReward: parseInt(xpReward.toString()),
      requirementType: requirementType.trim(),
      requirementValue: parseInt(requirementValue.toString()),
      createdAt: new Date().toISOString(),
    };

    const newAchievement = await db
      .insert(achievements)
      .values(insertData)
      .returning();

    return NextResponse.json(newAchievement[0], { status: 201 });
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
    const searchParams = request.nextUrl.searchParams;
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json(
        { error: 'Valid ID is required', code: 'INVALID_ID' },
        { status: 400 }
      );
    }

    // Check if record exists
    const existingRecord = await db
      .select()
      .from(achievements)
      .where(eq(achievements.id, parseInt(id)))
      .limit(1);

    if (existingRecord.length === 0) {
      return NextResponse.json(
        { error: 'Achievement not found', code: 'NOT_FOUND' },
        { status: 404 }
      );
    }

    const body = await request.json();
    const { title, description, icon, xpReward, requirementType, requirementValue } = body;

    // Build update object with only provided fields
    const updates: Record<string, string | number | null> = {};

    if (title !== undefined) {
      if (title.trim() === '') {
        return NextResponse.json(
          { error: 'Title cannot be empty', code: 'INVALID_TITLE' },
          { status: 400 }
        );
      }
      updates.title = title.trim();
    }

    if (description !== undefined) {
      updates.description = description ? description.trim() : null;
    }

    if (icon !== undefined) {
      updates.icon = icon ? icon.trim() : null;
    }

    if (xpReward !== undefined) {
      if (typeof xpReward !== 'number' || isNaN(xpReward)) {
        return NextResponse.json(
          { error: 'XP reward must be a valid number', code: 'INVALID_XP_REWARD' },
          { status: 400 }
        );
      }
      updates.xpReward = parseInt(xpReward.toString());
    }

    if (requirementType !== undefined) {
      if (requirementType.trim() === '') {
        return NextResponse.json(
          { error: 'Requirement type cannot be empty', code: 'INVALID_REQUIREMENT_TYPE' },
          { status: 400 }
        );
      }
      updates.requirementType = requirementType.trim();
    }

    if (requirementValue !== undefined) {
      if (typeof requirementValue !== 'number' || isNaN(requirementValue)) {
        return NextResponse.json(
          { error: 'Requirement value must be a valid number', code: 'INVALID_REQUIREMENT_VALUE' },
          { status: 400 }
        );
      }
      updates.requirementValue = parseInt(requirementValue.toString());
    }

    const updated = await db
      .update(achievements)
      .set(updates)
      .where(eq(achievements.id, parseInt(id)))
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
    const searchParams = request.nextUrl.searchParams;
    const id = searchParams.get('id');

    if (!id || isNaN(parseInt(id))) {
      return NextResponse.json(
        { error: 'Valid ID is required', code: 'INVALID_ID' },
        { status: 400 }
      );
    }

    // Check if record exists
    const existingRecord = await db
      .select()
      .from(achievements)
      .where(eq(achievements.id, parseInt(id)))
      .limit(1);

    if (existingRecord.length === 0) {
      return NextResponse.json(
        { error: 'Achievement not found', code: 'NOT_FOUND' },
        { status: 404 }
      );
    }

    const deleted = await db
      .delete(achievements)
      .where(eq(achievements.id, parseInt(id)))
      .returning();

    return NextResponse.json(
      {
        message: 'Achievement deleted successfully',
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