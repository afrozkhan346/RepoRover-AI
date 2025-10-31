import { NextRequest, NextResponse } from 'next/server';
import { db } from '@/db';
import { quizzes, lessons } from '@/db/schema';
import { eq, and } from 'drizzle-orm';
import { getCurrentUser } from '@/lib/auth';

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { searchParams } = new URL(request.url);
    const id = searchParams.get('id');
    const lessonId = searchParams.get('lessonId');

    // Single record fetch by ID
    if (id) {
      if (!id || isNaN(parseInt(id))) {
        return NextResponse.json({ 
          error: "Valid ID is required",
          code: "INVALID_ID" 
        }, { status: 400 });
      }

      const quiz = await db.select()
        .from(quizzes)
        .where(eq(quizzes.id, parseInt(id)))
        .limit(1);

      if (quiz.length === 0) {
        return NextResponse.json({ 
          error: 'Quiz not found',
          code: "NOT_FOUND" 
        }, { status: 404 });
      }

      return NextResponse.json(quiz[0], { status: 200 });
    }

    // List with pagination and filtering
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '10'), 100);
    const offset = parseInt(searchParams.get('offset') ?? '0');

    let query = db.select().from(quizzes);

    // Filter by lessonId if provided
    if (lessonId) {
      if (isNaN(parseInt(lessonId))) {
        return NextResponse.json({ 
          error: "Valid lessonId is required",
          code: "INVALID_LESSON_ID" 
        }, { status: 400 });
      }
      query = query.where(eq(quizzes.lessonId, parseInt(lessonId)));
    }

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
    const { lessonId, question, options, correctAnswer, explanation, difficulty, xpReward } = body;

    // Validate required fields
    if (!lessonId) {
      return NextResponse.json({ 
        error: "lessonId is required",
        code: "MISSING_LESSON_ID" 
      }, { status: 400 });
    }

    if (!question || typeof question !== 'string' || question.trim() === '') {
      return NextResponse.json({ 
        error: "Valid question is required",
        code: "MISSING_QUESTION" 
      }, { status: 400 });
    }

    if (!options) {
      return NextResponse.json({ 
        error: "options are required",
        code: "MISSING_OPTIONS" 
      }, { status: 400 });
    }

    if (!correctAnswer || typeof correctAnswer !== 'string' || correctAnswer.trim() === '') {
      return NextResponse.json({ 
        error: "correctAnswer is required",
        code: "MISSING_CORRECT_ANSWER" 
      }, { status: 400 });
    }

    if (!difficulty || typeof difficulty !== 'string' || difficulty.trim() === '') {
      return NextResponse.json({ 
        error: "difficulty is required",
        code: "MISSING_DIFFICULTY" 
      }, { status: 400 });
    }

    if (xpReward === undefined || xpReward === null || typeof xpReward !== 'number') {
      return NextResponse.json({ 
        error: "xpReward is required and must be a number",
        code: "MISSING_XP_REWARD" 
      }, { status: 400 });
    }

    // Validate lessonId is a valid integer
    if (isNaN(parseInt(lessonId))) {
      return NextResponse.json({ 
        error: "Valid lessonId is required",
        code: "INVALID_LESSON_ID" 
      }, { status: 400 });
    }

    // Verify that the referenced lesson exists
    const lessonExists = await db.select()
      .from(lessons)
      .where(eq(lessons.id, parseInt(lessonId)))
      .limit(1);

    if (lessonExists.length === 0) {
      return NextResponse.json({ 
        error: "Referenced lesson does not exist",
        code: "LESSON_NOT_FOUND" 
      }, { status: 400 });
    }

    // Validate options is a string (should be JSON string)
    let optionsString = options;
    if (typeof options !== 'string') {
      try {
        optionsString = JSON.stringify(options);
      } catch (e) {
        return NextResponse.json({ 
          error: "options must be a valid JSON string or serializable object",
          code: "INVALID_OPTIONS_FORMAT" 
        }, { status: 400 });
      }
    }

    // Create new quiz
    const newQuiz = await db.insert(quizzes)
      .values({
        lessonId: parseInt(lessonId),
        question: question.trim(),
        options: optionsString,
        correctAnswer: correctAnswer.trim(),
        explanation: explanation ? explanation.trim() : null,
        difficulty: difficulty.trim(),
        xpReward: parseInt(xpReward),
        createdAt: new Date().toISOString()
      })
      .returning();

    return NextResponse.json(newQuiz[0], { status: 201 });
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

    // Check if record exists
    const existingQuiz = await db.select()
      .from(quizzes)
      .where(eq(quizzes.id, parseInt(id)))
      .limit(1);

    if (existingQuiz.length === 0) {
      return NextResponse.json({ 
        error: 'Quiz not found',
        code: "NOT_FOUND" 
      }, { status: 404 });
    }

    const body = await request.json();
    const { lessonId, question, options, correctAnswer, explanation, difficulty, xpReward } = body;

    // Build update object with only provided fields
    const updates: Record<string, unknown> = {};

    if (lessonId !== undefined) {
      if (isNaN(parseInt(lessonId))) {
        return NextResponse.json({ 
          error: "Valid lessonId is required",
          code: "INVALID_LESSON_ID" 
        }, { status: 400 });
      }

      // Verify that the referenced lesson exists
      const lessonExists = await db.select()
        .from(lessons)
        .where(eq(lessons.id, parseInt(lessonId)))
        .limit(1);

      if (lessonExists.length === 0) {
        return NextResponse.json({ 
          error: "Referenced lesson does not exist",
          code: "LESSON_NOT_FOUND" 
        }, { status: 400 });
      }

      updates.lessonId = parseInt(lessonId);
    }

    if (question !== undefined) {
      if (typeof question !== 'string' || question.trim() === '') {
        return NextResponse.json({ 
          error: "Valid question is required",
          code: "INVALID_QUESTION" 
        }, { status: 400 });
      }
      updates.question = question.trim();
    }

    if (options !== undefined) {
      let optionsString = options;
      if (typeof options !== 'string') {
        try {
          optionsString = JSON.stringify(options);
        } catch (e) {
          return NextResponse.json({ 
            error: "options must be a valid JSON string or serializable object",
            code: "INVALID_OPTIONS_FORMAT" 
          }, { status: 400 });
        }
      }
      updates.options = optionsString;
    }

    if (correctAnswer !== undefined) {
      if (typeof correctAnswer !== 'string' || correctAnswer.trim() === '') {
        return NextResponse.json({ 
          error: "Valid correctAnswer is required",
          code: "INVALID_CORRECT_ANSWER" 
        }, { status: 400 });
      }
      updates.correctAnswer = correctAnswer.trim();
    }

    if (explanation !== undefined) {
      updates.explanation = explanation ? explanation.trim() : null;
    }

    if (difficulty !== undefined) {
      if (typeof difficulty !== 'string' || difficulty.trim() === '') {
        return NextResponse.json({ 
          error: "Valid difficulty is required",
          code: "INVALID_DIFFICULTY" 
        }, { status: 400 });
      }
      updates.difficulty = difficulty.trim();
    }

    if (xpReward !== undefined) {
      if (typeof xpReward !== 'number') {
        return NextResponse.json({ 
          error: "xpReward must be a number",
          code: "INVALID_XP_REWARD" 
        }, { status: 400 });
      }
      updates.xpReward = parseInt(xpReward);
    }

    // Update the quiz
    const updatedQuiz = await db.update(quizzes)
      .set(updates)
      .where(eq(quizzes.id, parseInt(id)))
      .returning();

    return NextResponse.json(updatedQuiz[0], { status: 200 });
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

    // Check if record exists
    const existingQuiz = await db.select()
      .from(quizzes)
      .where(eq(quizzes.id, parseInt(id)))
      .limit(1);

    if (existingQuiz.length === 0) {
      return NextResponse.json({ 
        error: 'Quiz not found',
        code: "NOT_FOUND" 
      }, { status: 404 });
    }

    // Delete the quiz
    const deletedQuiz = await db.delete(quizzes)
      .where(eq(quizzes.id, parseInt(id)))
      .returning();

    return NextResponse.json({
      message: 'Quiz deleted successfully',
      quiz: deletedQuiz[0]
    }, { status: 200 });
  } catch (error) {
    console.error('DELETE error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}