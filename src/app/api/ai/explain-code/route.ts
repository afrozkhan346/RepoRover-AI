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

    const { code, language, question } = await request.json();

    if (!code) {
      return NextResponse.json({ error: 'Code is required' }, { status: 400 });
    }

    const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });

    const prompt = question 
      ? `You are an expert code tutor. A student is learning ${language || 'programming'} and has the following question about this code:\n\nCode:\n\`\`\`${language || ''}\n${code}\n\`\`\`\n\nQuestion: ${question}\n\nProvide a clear, educational explanation that helps them understand the code and answers their question. Break down complex concepts into simple terms.`
      : `You are an expert code tutor. Explain the following ${language || ''} code in a clear, educational way. Break down what each part does, explain key concepts, and highlight any best practices or potential improvements:\n\n\`\`\`${language || ''}\n${code}\n\`\`\``;

    const result = await model.generateContent(prompt);
    const response = result.response;
    const explanation = response.text();

    return NextResponse.json({ 
      explanation,
      language,
      timestamp: new Date().toISOString()
    }, { status: 200 });

  } catch (error) {
    console.error('AI explanation error:', error);
    return NextResponse.json({ 
      error: 'Failed to generate explanation: ' + (error as Error).message 
    }, { status: 500 });
  }
}

export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    // Simple health check
    return NextResponse.json({ 
      status: 'ready',
      model: 'gemini-2.0-flash-exp',
      features: ['code-explanation', 'question-answering', 'concept-breakdown']
    }, { status: 200 });

  } catch (error) {
    console.error('AI service check error:', error);
    return NextResponse.json({ 
      error: 'Service unavailable: ' + (error as Error).message 
    }, { status: 500 });
  }
}