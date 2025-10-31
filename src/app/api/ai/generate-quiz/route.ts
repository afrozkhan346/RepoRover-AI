import { NextRequest, NextResponse } from 'next/server';
import { GoogleGenerativeAI } from '@google/generative-ai';
import { getCurrentUser } from '@/lib/auth';

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '');

export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { code, language, topic, difficulty = 'medium' } = await request.json();

    if (!code && !topic) {
      return NextResponse.json({ error: 'Either code or topic is required' }, { status: 400 });
    }

    const model = genAI.getGenerativeModel({ model: 'gemini-pro' });

    const prompt = code
      ? `Generate 3 multiple-choice quiz questions about the following ${language || ''} code. Make the questions ${difficulty} difficulty level.

Code:
\`\`\`${language || ''}
${code}
\`\`\`

Return ONLY a valid JSON array of questions in this exact format:
[
  {
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correctAnswer": 0,
    "explanation": "Why this answer is correct"
  }
]

Make sure:
- Questions test understanding of the code
- All 4 options are plausible
- correctAnswer is the index (0-3) of the correct option
- Explanations are clear and educational`
      : `Generate 3 multiple-choice quiz questions about ${topic}. Make the questions ${difficulty} difficulty level.

Return ONLY a valid JSON array of questions in this exact format:
[
  {
    "question": "Question text here?",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correctAnswer": 0,
    "explanation": "Why this answer is correct"
  }
]

Make sure:
- Questions cover key concepts
- All 4 options are plausible
- correctAnswer is the index (0-3) of the correct option
- Explanations are clear and educational`;

    const result = await model.generateContent(prompt);
    const response = result.response;
    const text = response.text();

    // Extract JSON from response
    const jsonMatch = text.match(/\[[\s\S]*\]/);
    if (!jsonMatch) {
      throw new Error('Failed to parse quiz questions from AI response');
    }

    const questions = JSON.parse(jsonMatch[0]);

    return NextResponse.json({ 
      questions,
      metadata: {
        topic: topic || `${language} code analysis`,
        difficulty,
        generatedAt: new Date().toISOString()
      }
    }, { status: 200 });

  } catch (error) {
    console.error('Quiz generation error:', error);
    return NextResponse.json({ 
      error: 'Failed to generate quiz: ' + (error as Error).message 
    }, { status: 500 });
  }
}