# RepoRover AI

[![Next.js](https://img.shields.io/badge/Next.js-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white)](https://tailwindcss.com/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://ai.google.dev/)
[![Vercel](https://img.shields.io/badge/Vercel-000000?style=for-the-badge&logo=vercel&logoColor=white)](https://vercel.com/)

A cutting-edge, AI-powered GitHub repository analyzer that provides deep insights into codebases using advanced machine learning and natural language processing. Built with modern web technologies for a seamless developer experience.

## ✨ Features

### 🚀 Core Functionality
- **AI-Powered Analysis**: Leverages Google Gemini AI for intelligent code analysis and insights
- **Repository Visualization**: Interactive file tree and code structure exploration
- **Real-time Chat**: AI-powered Q&A system for codebase understanding
- **Code Diff Viewer**: Advanced diff visualization with syntax highlighting
- **Project Snapshots**: Export and share repository analysis reports

### 🎨 User Experience
- **Modern UI**: Glass morphism design with smooth animations
- **Dark/Light Themes**: Automatic theme switching with system preference detection
- **Fully Responsive**: Optimized for desktop, tablet, and mobile devices
- **Accessibility**: WCAG compliant with keyboard navigation support

### 🔧 Developer Tools
- **Quick Analysis**: Fast repository scanning for immediate insights
- **Deep Analysis**: Comprehensive codebase evaluation with detailed metrics
- **Learn-by-Building**: Interactive guides for understanding complex codebases
- **Export Capabilities**: Generate PDF reports and shareable links

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 16 with App Router
- **Language**: TypeScript for type safety
- **Styling**: Tailwind CSS with custom animations
- **UI Components**: Radix UI primitives with shadcn/ui
- **State Management**: React hooks with context API
- **Charts**: Recharts for data visualization

### Backend & AI
- **AI Engine**: Google Generative AI (Gemini)
- **Authentication**: GitHub OAuth integration
- **Database**: Firebase Admin SDK
- **API**: RESTful endpoints with Next.js API routes

### Development Tools
- **Build Tool**: Next.js with SWC compiler
- **Linting**: ESLint with TypeScript rules
- **Package Manager**: npm/pnpm support
- **Deployment**: Vercel platform optimized

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ installed
- npm or pnpm package manager
- GitHub account for OAuth (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/rushikesh-bobade/RepoRover-AI.git
   cd RepoRover-AI
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   pnpm install
   ```

3. **Environment Setup**
   Create a `.env.local` file in the root directory:
   ```env
   # GitHub OAuth (Optional - for authentication)
   NEXT_PUBLIC_GITHUB_OAUTH_URL=https://github.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID

   # API Endpoints (Optional - uses mock data if not provided)
   NEXT_PUBLIC_ANALYZE_ENDPOINT=http://localhost:3000/api/analyze
   NEXT_PUBLIC_CHAT_ENDPOINT=http://localhost:3000/api/chat
   NEXT_PUBLIC_PROJECTS_ENDPOINT=http://localhost:3000/api/projects

   # Google Gemini AI (Required for AI features)
   GOOGLE_GEMINI_API_KEY=your_gemini_api_key_here

   # Firebase (Optional - for data persistence)
   FIREBASE_PROJECT_ID=your_project_id
   FIREBASE_PRIVATE_KEY=your_private_key
   FIREBASE_CLIENT_EMAIL=your_client_email
   ```

4. **Run the development server**
   ```bash
   npm run dev
   # or
   pnpm dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 📁 Project Structure

```
RepoRover-AI/
├── app/                          # Next.js App Router
│   ├── api/                      # API routes
│   │   ├── auth/                 # Authentication endpoints
│   │   ├── analyze/              # Analysis endpoints
│   │   └── chat/                 # Chat endpoints
│   ├── analyze/                  # Analysis page
│   ├── project/[id]/             # Dynamic project pages
│   ├── globals.css               # Global styles
│   ├── layout.tsx                # Root layout
│   └── page.tsx                  # Home page
├── components/                   # Reusable UI components
│   ├── ui/                       # shadcn/ui components
│   ├── chat-panel.tsx            # AI chat interface
│   ├── code-diff.tsx             # Code diff viewer
│   ├── file-tree.tsx             # Repository file tree
│   ├── repo-overview.tsx         # Repository overview
│   └── ...
├── hooks/                        # Custom React hooks
├── lib/                          # Utility functions
├── mock_data/                    # Mock data for development
├── public/                       # Static assets
├── styles/                       # Additional stylesheets
└── types/                        # TypeScript type definitions
```

## 🔧 Configuration

### Customizing Themes
Edit `app/globals.css` to modify color schemes and glass morphism effects:

```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  /* ... other CSS variables */
}
```

### API Integration
The app supports both mock data and real API endpoints. To connect real services:

1. **Analysis API**: Expects `{ repoUrl: string, analysisType: 'quick' | 'deep' }`
2. **Chat API**: Expects `{ projectId: string, message: string }`
3. **Projects API**: Returns array of project objects

## 🚀 Deployment

### Vercel (Recommended)
1. Push your code to GitHub
2. Connect your repository to Vercel
3. Add environment variables in Vercel dashboard
4. Deploy automatically on every push

### Manual Deployment
```bash
npm run build
npm start
```

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Use TypeScript for all new code
- Follow ESLint configuration
- Write meaningful commit messages
- Test your changes thoroughly
- Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Google Gemini AI** for powering the intelligent analysis
- **Vercel** for hosting and deployment platform
- **shadcn/ui** for beautiful UI components
- **Radix UI** for accessible primitives
- **Tailwind CSS** for utility-first styling

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/rushikesh-bobade/RepoRover-AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/rushikesh-bobade/RepoRover-AI/discussions)
- **Email**: support@reporover.ai

---

<div align="center">
  <p>Built with ❤️ using Next.js and TypeScript</p>
  <p>
    <a href="#features">Features</a> •
    <a href="#getting-started">Getting Started</a> •
    <a href="#contributing">Contributing</a> •
    <a href="#license">License</a>
  </p>
</div>
