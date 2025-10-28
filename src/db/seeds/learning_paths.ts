import { db } from '@/db';
import { learningPaths } from '@/db/schema';

async function main() {
    const sampleLearningPaths = [
        {
            title: 'JavaScript Basics',
            description: 'Master the fundamentals of JavaScript programming including variables, functions, loops, and DOM manipulation',
            difficulty: 'beginner',
            estimatedHours: 12,
            icon: '🟨',
            orderIndex: 1,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Python Fundamentals',
            description: 'Learn Python from scratch with hands-on exercises covering data types, control flow, functions, and object-oriented programming',
            difficulty: 'beginner',
            estimatedHours: 15,
            icon: '🐍',
            orderIndex: 2,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'React Mastery',
            description: 'Build modern web applications with React including hooks, state management, routing, and performance optimization',
            difficulty: 'intermediate',
            estimatedHours: 20,
            icon: '⚛️',
            orderIndex: 3,
            createdAt: new Date().toISOString(),
        },
    ];

    await db.insert(learningPaths).values(sampleLearningPaths);
    
    console.log('✅ Learning paths seeder completed successfully');
}

main().catch((error) => {
    console.error('❌ Seeder failed:', error);
});