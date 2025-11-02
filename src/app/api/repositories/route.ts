import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { repositories } from '@/db/schema';
import { eq, like, and, or, desc } from 'drizzle-orm';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const search = searchParams.get('search');
    const language = searchParams.get('language');
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

      const record = await db.select()
        .from(repositories)
        .where(and(
          eq(repositories.id, parseInt(id)),
          eq(repositories.userId, user.id)
        ))
        .limit(1);

      if (record.length === 0) {
        return NextResponse.json({ 
          error: 'Repository not found',
          code: 'REPOSITORY_NOT_FOUND' 
        }, { status: 404 });
      }

      return NextResponse.json(record[0], { status: 200 });
    }

    // List with filters, search, and pagination
    let query = db.select().from(repositories);
    const conditions = [eq(repositories.userId, user.id)];

    // Search by repository name
    if (search) {
      conditions.push(like(repositories.repoName, `%${search}%`));
    }

    // Filter by language
    if (language) {
      conditions.push(eq(repositories.language, language));
    }

    query = query.where(and(...conditions));
    query = query.orderBy(desc(repositories.createdAt));
    
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

    const { githubUrl, repoName, description, language, stars, analyzedAt, analysisData } = body;

    // Validate required fields
    if (!githubUrl || !githubUrl.trim()) {
      return NextResponse.json({ 
        error: "GitHub URL is required",
        code: "MISSING_GITHUB_URL" 
      }, { status: 400 });
    }

    if (!repoName || !repoName.trim()) {
      return NextResponse.json({ 
        error: "Repository name is required",
        code: "MISSING_REPO_NAME" 
      }, { status: 400 });
    }

    // Prepare insert data with sanitization
    const insertData = {
      userId: user.id,
      githubUrl: githubUrl.trim(),
      repoName: repoName.trim(),
      description: description ? description.trim() : null,
      language: language ? language.trim() : null,
      stars: stars !== undefined ? parseInt(stars) : 0,
      analyzedAt: analyzedAt || null,
      analysisData: analysisData || null,
      createdAt: new Date().toISOString(),
    };

    const newRepository = await db.insert(repositories)
      .values(insertData)
      .returning();

    return NextResponse.json(newRepository[0], { status: 201 });

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

    // Check if repository exists and belongs to user
    const existing = await db.select()
      .from(repositories)
      .where(and(
        eq(repositories.id, parseInt(id)),
        eq(repositories.userId, user.id)
      ))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json({ 
        error: 'Repository not found',
        code: 'REPOSITORY_NOT_FOUND' 
      }, { status: 404 });
    }

    // Prepare update data
    const updates: Record<string, any> = {};

    if (body.githubUrl !== undefined) {
      updates.githubUrl = body.githubUrl.trim();
    }
    if (body.repoName !== undefined) {
      updates.repoName = body.repoName.trim();
    }
    if (body.description !== undefined) {
      updates.description = body.description ? body.description.trim() : null;
    }
    if (body.language !== undefined) {
      updates.language = body.language ? body.language.trim() : null;
    }
    if (body.stars !== undefined) {
      updates.stars = parseInt(body.stars);
    }
    if (body.analyzedAt !== undefined) {
      updates.analyzedAt = body.analyzedAt;
    }
    if (body.analysisData !== undefined) {
      updates.analysisData = body.analysisData;
    }

    const updated = await db.update(repositories)
      .set(updates)
      .where(and(
        eq(repositories.id, parseInt(id)),
        eq(repositories.userId, user.id)
      ))
      .returning();

    if (updated.length === 0) {
      return NextResponse.json({ 
        error: 'Repository not found',
        code: 'REPOSITORY_NOT_FOUND' 
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

    // Check if repository exists and belongs to user
    const existing = await db.select()
      .from(repositories)
      .where(and(
        eq(repositories.id, parseInt(id)),
        eq(repositories.userId, user.id)
      ))
      .limit(1);

    if (existing.length === 0) {
      return NextResponse.json({ 
        error: 'Repository not found',
        code: 'REPOSITORY_NOT_FOUND' 
      }, { status: 404 });
    }

    const deleted = await db.delete(repositories)
      .where(and(
        eq(repositories.id, parseInt(id)),
        eq(repositories.userId, user.id)
      ))
      .returning();

    if (deleted.length === 0) {
      return NextResponse.json({ 
        error: 'Repository not found',
        code: 'REPOSITORY_NOT_FOUND' 
      }, { status: 404 });
    }

    return NextResponse.json({ 
      message: 'Repository deleted successfully',
      repository: deleted[0]
    }, { status: 200 });

  } catch (error) {
    console.error('DELETE error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}