# RepoRover AI

[![Next.js](https://img.shields.io/badge/Next.js-15.3.5-black)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-cyan)](https://tailwindcss.com/)
[![Drizzle ORM](https://img.shields.io/badge/Drizzle_ORM-0.44.6-orange)](https://orm.drizzle.team/)
[![Better Auth](https://img.shields.io/badge/Better_Auth-1.3.10-green)](https://www.better-auth.com/)
[![Google AI](https://img.shields.io/badge/Google_AI-0.24.1-red)](https://ai.google.dev/)

An AI-powered learning platform that revolutionizes coding education through interactive lessons, gamified experiences, and intelligent code analysis. Built with modern web technologies and designed for developers of all skill levels.

## 🌟 Features

### 🎓 Interactive Learning Platform
- **Structured Learning Paths**: Comprehensive courses from JavaScript basics to advanced React development
- **Hands-on Lessons**: Practical exercises with real-world examples and immediate feedback
- **Progress Tracking**: Detailed analytics and personalized learning insights

### 🤖 AI-Powered Features
- **Code Explanation**: Instant AI-generated explanations for any code snippet
- **Smart Tutoring**: Context-aware assistance and personalized learning recommendations
- **GitHub Integration**: Analyze real-world repositories to understand production codebases

### 🎮 Gamification & Engagement
- **XP System**: Earn experience points and level up through learning activities
- **Achievements**: Unlock badges and rewards for milestones and challenges
- **Streak Tracking**: Maintain learning consistency with daily progress monitoring

### 📊 Advanced Analytics
- **Performance Metrics**: Comprehensive statistics on learning progress and patterns
- **Interactive Quizzes**: Multiple-choice questions and coding challenges
- **Repository Analysis**: Deep insights into GitHub repositories and code quality

## 🚀 Tech Stack

### Frontend
- **Framework**: Next.js 15.3.5 with App Router
- **Language**: TypeScript 5
- **Styling**: Tailwind CSS 4 with custom design system
- **UI Components**: Radix UI primitives with custom implementations
- **Animations**: Framer Motion for smooth interactions
- **Icons**: Lucide React for consistent iconography

### Backend & Database
- **Database**: Turso (SQLite-compatible) with Drizzle ORM
- **Authentication**: Better Auth with email/password and session management
- **API**: RESTful endpoints with Next.js API routes
- **Validation**: Zod for type-safe data validation

### AI & Integrations
- **AI Engine**: Google Generative AI (Gemini) for code analysis
- **GitHub API**: Repository analysis and metadata extraction
- **External APIs**: Integration with various development tools

### Development Tools
- **Package Manager**: npm with legacy peer deps support
- **Linting**: ESLint with Next.js configuration
- **Build Tool**: Next.js with Turbopack for fast development
- **Database Management**: Drizzle Kit for migrations

## 📁 Project Structure

```
RepoRover-AI/
├── src/
│   ├── app/                    # Next.js App Router pages
│   │   ├── (auth)/            # Authentication pages
│   │   ├── (dashboard)/       # Protected dashboard routes
│   │   ├── api/               # API endpoints
│   │   ├── globals.css        # Global styles
│   │   └── layout.tsx         # Root layout
│   ├── components/            # Reusable UI components
│   │   ├── ui/               # Base UI components (shadcn/ui)
│   │   └── navigation.tsx    # Main navigation
│   ├── db/                   # Database configuration
│   │   ├── schema.ts         # Drizzle schema definitions
│   │   └── index.ts          # Database client
│   ├── lib/                  # Utility libraries
│   │   ├── auth.ts           # Authentication setup
│   │   └── utils.ts          # Helper functions
│   └── hooks/                # Custom React hooks
├── public/                   # Static assets
├── drizzle/                  # Database migrations
├── components.json           # shadcn/ui configuration
└── package.json              # Dependencies and scripts
```

## 🛠️ Installation & Setup

### Prerequisites
- Node.js 18+ and npm
- Turso account and database URL
- Google AI API key
- GitHub Personal Access Token (optional, for enhanced features)

### 1. Clone the Repository
```bash
git clone https://github.com/afrozkhan346/RepoRover-AI.git
cd RepoRover-AI
```

### 2. Install Dependencies
```bash
npm install --legacy-peer-deps
```

### 3. Environment Configuration
Create a `.env.local` file in the root directory:

```env
# Database Configuration
TURSO_CONNECTION_URL=your_turso_database_url
TURSO_AUTH_TOKEN=your_turso_auth_token

# AI Configuration
GOOGLE_AI_API_KEY=your_google_ai_api_key

# Authentication (Optional - Better Auth handles most of this)
NEXTAUTH_SECRET=your_nextauth_secret
NEXTAUTH_URL=http://localhost:3000

# GitHub Integration (Optional)
GITHUB_ACCESS_TOKEN=your_github_token
```

### 4. Database Setup
```bash
# Generate and run migrations
npm run db:generate
npm run db:migrate

# (Optional) Seed the database with sample data
npm run db:seed
```

### 5. Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## 📊 Database Schema

The application uses a comprehensive database schema with the following main entities:

- **Users**: Authentication and profile management
- **Learning Paths**: Structured course content
- **Lessons**: Individual learning modules
- **Quizzes**: Assessment questions and answers
- **User Progress**: Learning analytics and tracking
- **Achievements**: Gamification rewards system
- **Repositories**: GitHub repository analysis storage

## 🔧 Available Scripts

```bash
# Development
npm run dev          # Start development server with Turbopack
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint

# Database
npm run db:generate  # Generate Drizzle migrations
npm run db:migrate   # Run database migrations
npm run db:studio    # Open Drizzle Studio
npm run db:seed      # Seed database with sample data

# Code Quality
npm run type-check   # TypeScript type checking
npm run format       # Code formatting with Prettier
```

## 🌐 API Endpoints

### Authentication
- `POST /api/auth/sign-in` - User login
- `POST /api/auth/sign-up` - User registration
- `POST /api/auth/sign-out` - User logout
- `GET /api/auth/session` - Get current session

### Learning Platform
- `GET /api/learning-paths` - Get all learning paths
- `GET /api/lessons` - Get lessons with filtering
- `GET /api/user-progress` - Get user learning progress
- `POST /api/lesson-progress` - Update lesson completion

### AI Features
- `POST /api/ai/explain-code` - Get AI code explanations
- `POST /api/ai/generate-quiz` - Generate quiz questions

### GitHub Integration
- `POST /api/github/analyze` - Analyze GitHub repository
- `GET /api/repositories` - Get user's saved repositories

## 🎨 UI/UX Design

### Design System
- **Color Palette**: Modern dark/light theme with primary accent colors
- **Typography**: Geist font family with responsive scaling
- **Components**: Consistent design system using Radix UI primitives
- **Animations**: Smooth transitions and micro-interactions

### Responsive Design
- **Mobile-First**: Optimized for all device sizes
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Accessibility**: WCAG 2.1 AA compliant with proper ARIA labels

## 🚀 Deployment

### Vercel (Recommended)
1. Connect your GitHub repository to Vercel
2. Add environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Manual Deployment
```bash
# Build the application
npm run build

# Start production server
npm run start
```

### Environment Variables for Production
Ensure all environment variables are set in your deployment platform:
- `TURSO_CONNECTION_URL`
- `TURSO_AUTH_TOKEN`
- `GOOGLE_AI_API_KEY`
- `NEXTAUTH_SECRET`
- `NEXTAUTH_URL`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow TypeScript strict mode
- Use conventional commits
- Write comprehensive tests
- Update documentation for API changes
- Ensure accessibility compliance

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Next.js Team** for the amazing React framework
- **Vercel** for hosting and deployment platform
- **shadcn/ui** for the beautiful component library
- **Google AI** for powerful language models
- **Turso** for the excellent SQLite platform

## 📞 Support

For support, email support@reporover.ai or join our Discord community.

---

**Built with ❤️ for the developer community**
