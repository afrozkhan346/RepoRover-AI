# 🌩️ RepoRover AI

> **AI-Powered Code Learning Platform**

[![Next.js](https://img.shields.io/badge/Next.js-15.3.5-black)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4-cyan)](https://tailwindcss.com/)
[![Drizzle ORM](https://img.shields.io/badge/Drizzle_ORM-0.44.6-orange)](https://orm.drizzle.team/)
[![Better Auth](https://img.shields.io/badge/Better_Auth-1.3.10-green)](https://www.better-auth.com/)
[![Google AI](https://img.shields.io/badge/Google_AI-0.24.1-red)](https://ai.google.dev/)

An AI-powered learning platform that revolutionizes coding education through interactive lessons, gamified experiences, and intelligent code analysis. Built with modern web technologies and designed for developers of all skill levels.

---

## 🧭 Overall Architecture (IMPORTANT)

RepoRover AI is organized around this flow:

Frontend (React + Vite)
   ↓
Backend API (FastAPI)
   ↓
Core Engine
 ├── Parser (AST)
 ├── Graph Builder
 ├── AI/NLP Layer
 └── Explanation Engine
   ↓
Database (optional)

### Core Engine module map

- `backend/app/engine/parser` - AST preview, AST structure, and token extraction wrappers
- `backend/app/engine/graph_builder` - dependency graph, call graph, and graph analytics wrappers
- `backend/app/engine/ai_nlp` - AI explanation, project summaries, quality analysis, and risk scoring
- `backend/app/engine/explanation_engine` - explainability trace generation
- `backend/app/engine/orchestrator.py` - unified orchestration entrypoint for end-to-end repository analysis

This engine layer isolates core analysis capabilities from transport concerns (FastAPI routes) so frontend clients can evolve independently.

### Migration status

- **Active UI**: The Vite frontend in `frontend/` is now the primary interface for all major features.
- **Pages migrated to Vite**:
  - Landing / Home
  - Dashboard (with project analysis summaries)
  - Learning Paths (with path browsing and lesson listing)
  - Lessons (browse and view lesson details)
  - AI Tutor (interactive code explanation and tutoring)
  - Authentication (Login, Register, Profile)  
  - Achievements (user progress and badges)
  - Code Analysis (project upload, clone, and analysis workflows)
- **Legacy Next.js pages**: All remaining Next.js pages are now minimal handoff screens that redirect to the Vite app.
- **Backend**: FastAPI provides all data via RESTful endpoints. Auth, achievements, lessons, and learning paths are seeded in memory for rapid iteration.
- **Startup**: `npm run dev` from the repo root starts the Vite frontend on `http://localhost:5173`. The FastAPI backend runs on `http://localhost:8000`.

---

## Project Parsing Engine Milestone

The backend now includes a project parsing engine that can:

- Scan local or cloned projects
- Extract folder and file structure
- Detect project language from discovered file extensions
- Produce structured metadata ready for AST parsing

### Example Output

```json
{
   "language": "Python",
   "total_files": 25,
   "files": [
      {
         "name": "main.py",
         "path": "backend/projects/demo/main.py",
         "extension": "py"
      }
   ]
}
```

### What You Achieved

- Project scanning engine
- Language detection
- File metadata extraction
- Ready for AST parsing

---

## 🌟 Features

### 🎓 Interactive Learning Platform

- **Structured Learning Paths**: Comprehensive courses from JavaScript basics to advanced React development
- **Hands-on Lessons**: Practical exercises with real-world examples and immediate feedback
- **Progress Tracking**: Detailed analytics and personalized learning insights

### 🤖 AI-Powered Features

- **Code Explanation**: Instant AI-generated explanations for any code snippet using Google Gemini
- **Smart Tutoring**: Context-aware assistance and personalized learning recommendations
- **GitHub Integration**: Analyze real-world repositories to understand production codebases
- **Quiz Generation**: Automatically create quizzes from code snippets

### 🎮 Gamification & Engagement

- **Achievement System**: Unlock badges and milestones as you progress
- **XP & Leveling**: Earn experience points for completing lessons and quizzes
- **Leaderboards**: Compete with other learners and track your ranking
- **Streaks & Challenges**: Maintain daily learning streaks and complete special challenges

### 📊 Advanced Analytics

- **Repository Analysis**: Deep insights into GitHub repositories and code quality
- **Learning Insights**: Track your strengths, weaknesses, and areas for improvement
- **Performance Metrics**: Detailed statistics on quiz scores, completion rates, and time spent

---

## 🏗️ Tech Stack

Current implementation details are listed below. The finalized target architecture is documented in docs/FINAL_TECH_STACK.md.

### **Frontend**
- **Framework**: Next.js 15.3.5 with App Router
- **Language**: TypeScript 5.7.3
- **Styling**: Tailwind CSS 4.0.9
- **UI Components**: shadcn/ui with Radix UI primitives
- **Animations**: Framer Motion 12.0.0
- **State Management**: React 19 hooks and context
- **Theme**: next-themes with dark mode support

### **Backend & Database**
- **Database**: Turso (SQLite/libSQL) with Drizzle ORM 0.44.6
- **Authentication**: Better Auth 1.3.10 with OAuth (Google, GitHub) and email/password
- **AI**: Google Gemini 2.0 Flash Experimental via @google/generative-ai 0.24.1
- **Caching**: Redis with optimization utilities
- **API**: RESTful endpoints with Next.js API routes

### **DevOps & Tools**
- **Package Manager**: npm/bun
- **Database Tools**: Drizzle Kit for migrations and schema management
- **Code Quality**: ESLint with Next.js config
- **Type Safety**: TypeScript strict mode
- **Version Control**: Git with GitHub integration

---

## 🚀 Getting Started

### **Prerequisites**

- Node.js 18+ or Bun 1.0+
- npm, yarn, or bun package manager
- Google Gemini API key ([Get one here](https://aistudio.google.com/app/apikey))
- Turso database account ([Sign up here](https://turso.tech))
- (Optional) OAuth credentials for Google and GitHub

### **Installation**

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/repoorover-ai.git
   cd repoorover-ai
   ```

2. **Install dependencies**:
   ```bash
   npm install
   # or
   bun install
   ```

3. **Set up environment variables**:
   
   Copy `.env.example` to `.env.development`:
   ```bash
   cp .env.example .env.development
   ```
   
   Update `.env.development` with your credentials:
   ```env
   # Gemini AI
   GEMINI_API_KEY=your_gemini_api_key
   
   # Turso Database
   TURSO_CONNECTION_URL=libsql://your-database.turso.io
   TURSO_AUTH_TOKEN=your_turso_token
   
   # Better Auth
   BETTER_AUTH_SECRET=your_auth_secret
   BETTER_AUTH_URL=http://localhost:3000
   
   # OAuth (optional)
   GOOGLE_CLIENT_ID=your_google_client_id
   GOOGLE_CLIENT_SECRET=your_google_client_secret
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret
   ```

4. **Set up the database**:
   ```bash
   # Generate database schema
   npm run db:generate
   
   # Push schema to Turso
   npm run db:push
   
   # Seed the database with initial data
   npm run db:seed
   ```

5. **Run the development server**:
   ```bash
   npm run dev
   # or
   bun dev
   ```

6. **Open in browser**:
   Navigate to `http://localhost:3000`

---

## 📁 Project Structure

```
RepoRover-AI/
├── src/
│   ├── app/                      # Next.js App Router pages
│   │   ├── api/                 # API routes
│   │   ├── achievements/        # Achievements page
│   │   ├── ai-tutor/            # AI tutor interface
│   │   ├── analyze/             # Repository analysis
│   │   ├── dashboard/           # User dashboard
│   │   ├── lessons/             # Learning lessons
│   │   ├── login/               # Authentication pages
│   │   ├── profile/             # User profile
│   │   └── register/            # User registration
│   ├── components/              # Reusable React components
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── navigation.tsx       # Navigation bar
│   │   ├── theme-provider.tsx   # Theme management
│   │   └── theme-toggle.tsx     # Dark mode toggle
│   ├── db/                      # Database configuration
│   │   ├── index.ts             # Drizzle client
│   │   ├── schema.ts            # Database schema
│   │   └── seeds/               # Seed data
│   ├── lib/                     # Utility functions
│   │   ├── auth.ts              # Authentication logic
│   │   ├── auth-client.ts       # Auth client
│   │   └── utils.ts             # Helper functions
│   └── hooks/                   # Custom React hooks
├── drizzle/                     # Drizzle migrations
├── public/                      # Static assets
├── docs/                        # Documentation
│   ├── OAUTH_SETUP.md           # OAuth configuration guide
│   ├── DATABASE_SETUP.md        # Database setup instructions
│   └── API_DOCUMENTATION.md     # API reference
├── .env.example                 # Environment variables template
├── drizzle.config.ts            # Drizzle ORM configuration
├── next.config.ts               # Next.js configuration
├── tailwind.config.ts           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
└── package.json                 # Dependencies and scripts
```

---

## 🎯 Core Features Explained

### **Learning Paths**
Pre-structured courses covering:
- JavaScript Fundamentals
- TypeScript Essentials
- React Development
- Next.js Advanced Concepts
- Algorithm Design Patterns

### **AI Tutor**
Get instant explanations for:
- Code snippets
- Error messages
- Best practices
- Performance optimization tips

### **GitHub Analysis**
Analyze repositories to:
- Understand codebase architecture
- Generate learning materials
- Create custom quizzes
- Track code quality metrics

### **Achievement System**
Earn badges for:
- Completing lessons
- Maintaining learning streaks
- High quiz scores
- Repository analysis
- Contributing to the community

---

## 📚 Database Schema

The app uses **Turso (SQLite)** with the following main tables:

- **users**: User accounts and profiles
- **learning_paths**: Structured learning courses
- **lessons**: Individual lesson content
- **quizzes**: Quiz questions and answers
- **achievements**: Available achievements
- **user_progress**: Lesson completion tracking
- **user_achievements**: Unlocked achievements
- **quiz_attempts**: Quiz submission records

---

## 🔐 Authentication

RepoRover AI uses **Better Auth** with support for:

1. **Email/Password**: Traditional authentication with secure password hashing
2. **Google OAuth**: One-click login with Google accounts
3. **GitHub OAuth**: Authenticate using GitHub credentials

For detailed OAuth setup, see [OAUTH_SETUP.md](docs/OAUTH_SETUP.md).

---

## 🛠️ Available Scripts

```bash
# Development
npm run dev              # Start development server
npm run build            # Build for production
npm run start            # Start production server

# Database
npm run db:generate      # Generate Drizzle migrations
npm run db:push          # Push schema to Turso
npm run db:seed          # Seed database with initial data
npm run db:studio        # Open Drizzle Studio (database UI)

# Code Quality
npm run lint             # Run ESLint
npm run type-check       # Run TypeScript compiler check
```

---

## 🌐 Deployment

### **Recommended Platforms**

- **Vercel**: Optimal for Next.js applications
- **Netlify**: Great for static site generation
- **Railway**: Good for full-stack deployments

### **Environment Variables for Production**

Make sure to set these in your deployment platform:

- `GEMINI_API_KEY`
- `TURSO_CONNECTION_URL`
- `TURSO_AUTH_TOKEN`
- `BETTER_AUTH_SECRET`
- `BETTER_AUTH_URL`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini AI** for powerful code analysis and explanation
- **Turso** for fast, distributed SQLite database
- **Better Auth** for secure authentication
- **shadcn/ui** for beautiful UI components
- **Vercel** for Next.js framework and hosting
- **Drizzle Team** for excellent TypeScript ORM

---

## 📧 Contact

For questions, suggestions, or support:

- **GitHub Issues**: [Report a bug](https://github.com/yourusername/repoorover-ai/issues)
- **Discussions**: [Join the conversation](https://github.com/yourusername/repoorover-ai/discussions)

---

**Built with ❤️ using Next.js and Google Gemini AI**

*Empowering developers to learn smarter, not harder* ✨
