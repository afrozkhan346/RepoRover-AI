import { db } from '@/db';
import { achievements } from '@/db/schema';

async function main() {
    const sampleAchievements = [
        {
            title: 'First Steps',
            description: 'Complete your first lesson',
            icon: '🎯',
            xpReward: 50,
            requirementType: 'lessons_completed',
            requirementValue: 1,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Early Bird',
            description: 'Complete 5 lessons',
            icon: '🌅',
            xpReward: 100,
            requirementType: 'lessons_completed',
            requirementValue: 5,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Dedicated Learner',
            description: 'Complete 10 lessons',
            icon: '📚',
            xpReward: 200,
            requirementType: 'lessons_completed',
            requirementValue: 10,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Week Warrior',
            description: 'Maintain a 7-day learning streak',
            icon: '🔥',
            xpReward: 150,
            requirementType: 'streak_days',
            requirementValue: 7,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Consistency King',
            description: 'Maintain a 30-day learning streak',
            icon: '👑',
            xpReward: 500,
            requirementType: 'streak_days',
            requirementValue: 30,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Quiz Master',
            description: 'Complete 20 quizzes',
            icon: '🧠',
            xpReward: 200,
            requirementType: 'quizzes_completed',
            requirementValue: 20,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Perfect Score',
            description: 'Get 10 quiz questions correct in a row',
            icon: '💯',
            xpReward: 250,
            requirementType: 'correct_answers_streak',
            requirementValue: 10,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'XP Hunter',
            description: 'Earn 1000 total XP',
            icon: '⭐',
            xpReward: 300,
            requirementType: 'total_xp',
            requirementValue: 1000,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Level Up',
            description: 'Reach level 5',
            icon: '🚀',
            xpReward: 200,
            requirementType: 'level_reached',
            requirementValue: 5,
            createdAt: new Date().toISOString(),
        },
        {
            title: 'Path Completed',
            description: 'Complete an entire learning path',
            icon: '🏆',
            xpReward: 400,
            requirementType: 'paths_completed',
            requirementValue: 1,
            createdAt: new Date().toISOString(),
        },
    ];

    await db.insert(achievements).values(sampleAchievements);
    
    console.log('✅ Achievements seeder completed successfully');
}

main().catch((error) => {
    console.error('❌ Seeder failed:', error);
});