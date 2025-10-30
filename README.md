# RepoRover AI

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Next.js](https://img.shields.io/badge/Next.js-14.0+-black)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-4.0+-38B2AC)](https://tailwindcss.com/)
[![Google Generative AI](https://img.shields.io/badge/Google_Generative_AI-0.24+-orange)](https://ai.google.dev/)

An AI-powered GitHub repository analysis tool that helps developers understand, learn from, and build upon any repository instantly. Get intelligent insights, step-by-step learning guides, and accelerate your development journey.

![RepoRover AI Preview](./public/placeholder.jpg)

## ✨ Features

### 🤖 AI-Powered Analysis
- **Instant Repository Insights**: Get comprehensive analysis of any GitHub repository
- **Code Structure Understanding**: AI-powered breakdown of architecture and patterns
- **Best Practices Detection**: Identify modern development practices and conventions
- **Technology Stack Recognition**: Automatic detection of frameworks, libraries, and tools

### 📚 Learn by Building
- **Interactive Learning Projects**: Step-by-step guides to understand repository patterns
- **Difficulty Levels**: Projects categorized by estimated time and complexity
- **Code Examples**: Practical implementations with copy-paste ready code
- **Verification Commands**: Built-in testing to ensure correct implementation

### ⚡ Quick Projects
- **Time-Efficient Learning**: Projects designed for 1-3 hour completion
- **Skill Progression**: From beginner to advanced difficulty levels
- **Real-World Application**: Learn through practical, production-ready examples

### 📸 Repository Snapshots
- **Export Analysis**: Save and share repository analysis snapshots
- **Team Collaboration**: Share insights with your development team
- **Historical Tracking**: Keep track of repository evolution over time

## 🚀 Quick Start

### Prerequisites
- Node.js 18.0 or later
- npm, yarn, or pnpm
- GitHub account (optional, for authentication)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/afrozkhan346/RepoRover-AI.git
   cd RepoRover-AI
   ```

2. **Install dependencies**
   ```bash
   npm install
   # or
   yarn install
   # or
   pnpm install
   ```

3. **Environment Setup**
   ```bash
   cp .env.example .env.local
   ```

   Configure the following environment variables:
   ```env
   # Google Generative AI API Key (for AI analysis)
   GOOGLE_GENERATIVE_AI_API_KEY=your_api_key_here

   # GitHub OAuth (optional, for enhanced features)
   GITHUB_CLIENT_ID=your_github_client_id
   GITHUB_CLIENT_SECRET=your_github_client_secret

   # Analysis endpoints (optional, for backend integration)
   NEXT_PUBLIC_ANALYZE_ENDPOINT=https://your-api-endpoint.com/analyze
   NEXT_PUBLIC_CHAT_ENDPOINT=https://your-api-endpoint.com/chat
   ```

4. **Run the development server**
   ```bash
   npm run dev
   # or
   yarn dev
   # or
   pnpm dev
   ```

5. **Open your browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

## 🏗️ Project Structure

```
RepoRover-AI/
├── app/                          # Next.js app directory
│   ├── api/                      # API routes
│   │   └── auth/                 # Authentication endpoints
│   ├── analyze/                  # Repository analysis page
│   ├── project/                  # Learning project pages
│   ├── globals.css               # Global styles
│   └── layout.tsx                # Root layout
├── components/                   # React components
│   ├── ui/                       # Shadcn/ui components
│   ├── chat-panel.tsx            # AI chat interface
│   ├── dashboard-cards.tsx       # Analytics dashboard
│   ├── file-tree.tsx             # Repository file structure
│   └── ...
├── hooks/                        # Custom React hooks
├── lib/                          # Utility functions
├── mock_data/                    # Sample data for development
├── public/                       # Static assets
├── styles/                       # Additional stylesheets
├── package.json                  # Dependencies and scripts
├── next.config.mjs              # Next.js configuration
├── tailwind.config.js           # Tailwind CSS configuration
└── tsconfig.json                # TypeScript configuration
```

## 🛠️ Tech Stack

### Frontend
- **Framework**: [Next.js 16](https://nextjs.org/) - React framework with App Router
- **Language**: [TypeScript 5](https://www.typescriptlang.org/) - Type-safe JavaScript
- **Styling**: [Tailwind CSS 4](https://tailwindcss.com/) - Utility-first CSS framework
- **UI Components**: [Shadcn/ui](https://ui.shadcn.com/) - Modern component library
- **Icons**: [Lucide React](https://lucide.dev/) - Beautiful icon library

### AI & APIs
- **AI Engine**: [Google Generative AI](https://ai.google.dev/) - For repository analysis
- **Authentication**: GitHub OAuth integration
- **Analytics**: [Vercel Analytics](https://vercel.com/analytics) - Usage tracking

### Development Tools
- **Package Manager**: npm/pnpm/yarn
- **Linting**: ESLint with Next.js rules
- **Code Quality**: Prettier for code formatting
- **Version Control**: Git with conventional commits

## 📖 Usage Guide

### Analyzing a Repository

1. **Enter Repository URL**: Paste any GitHub repository URL in the input field
2. **Choose Analysis Type**:
   - **Quick Analysis**: Basic overview and structure
   - **Deep Analysis**: Comprehensive code review and insights
3. **View Results**: Explore AI-generated insights, file structure, and learning projects

### Learning Projects

1. **Browse Available Projects**: Check the project grid for learning opportunities
2. **Select Difficulty Level**: Choose projects matching your skill level
3. **Follow Step-by-Step Guide**: Complete each step with provided code examples
4. **Verify Implementation**: Use built-in verification commands

### AI Chat Support

- **Ask Questions**: Get help understanding repository concepts
- **Code Explanations**: Request detailed explanations of specific code sections
- **Best Practices**: Learn about development best practices and patterns

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_GENERATIVE_AI_API_KEY` | Google AI API key for analysis | Yes |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID | No |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth client secret | No |
| `NEXT_PUBLIC_ANALYZE_ENDPOINT` | Backend analysis API endpoint | No |
| `NEXT_PUBLIC_CHAT_ENDPOINT` | Backend chat API endpoint | No |

### Build Configuration

The project uses Next.js with the following key configurations:

- **TypeScript**: Strict mode enabled for type safety
- **Images**: Unoptimized for static deployment
- **Build Errors**: Ignored during development for faster iteration

## 🚀 Deployment

### Vercel (Recommended)

1. **Connect Repository**: Link your GitHub repo to Vercel
2. **Configure Environment Variables**: Set up required env vars in Vercel dashboard
3. **Deploy**: Automatic deployments on push to main branch

### Other Platforms

The app can be deployed to any platform supporting Next.js:

```bash
# Build for production
npm run build

# Start production server
npm start
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and test thoroughly
4. Commit with conventional commits: `git commit -m 'feat: add amazing feature'`
5. Push to your branch: `git push origin feature/amazing-feature`
6. Open a Pull Request

### Code Style

- **TypeScript**: Strict typing required
- **ESLint**: All linting rules must pass
- **Prettier**: Code formatting enforced
- **Conventional Commits**: Required for all commits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Next.js Team** for the amazing React framework
- **Shadcn** for the beautiful UI components
- **Google AI** for the powerful Generative AI capabilities
- **Vercel** for hosting and analytics
- **Open Source Community** for inspiration and tools

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/afrozkhan346/RepoRover-AI/issues)
- **Discussions**: [GitHub Discussions](https://github.com/afrozkhan346/RepoRover-AI/discussions)
- **Documentation**: [Wiki](https://github.com/afrozkhan346/RepoRover-AI/wiki)

---

**Built with ❤️ for developers, by developers**

[![Star History Chart](https://api.star-history.com/svg?repos=afrozkhan346/RepoRover-AI&type=Date)](https://star-history.com/#afrozkhan346/RepoRover-AI&Date)
