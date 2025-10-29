# RepoRoverAI

A modern, AI-powered GitHub repository analyzer built with Next.js, TypeScript, and Tailwind CSS.

## Features

- 🤖 AI-powered repository analysis
- 📚 Learn-by-building guides
- ⚡ Quick and deep analysis modes
- 📸 Export repository snapshots
- 💬 AI-powered chat for questions
- 🌓 Dark/light theme support
- 📱 Fully responsive design

## Getting Started

### Environment Variables

Create a `.env.local` file with the following variables:

\`\`\`
NEXT_PUBLIC_GITHUB_OAUTH_URL=https://github.com/login/oauth/authorize?client_id=YOUR_CLIENT_ID
NEXT_PUBLIC_ANALYZE_ENDPOINT=http://localhost:3001/api/analyze
NEXT_PUBLIC_CHAT_ENDPOINT=http://localhost:3001/api/chat
NEXT_PUBLIC_PROJECTS_ENDPOINT=http://localhost:3001/api/projects
\`\`\`

If these endpoints are not provided, the app will use mock data from `/public/mock_data/demo_repo_response.json`.

### Installation

\`\`\`bash
npm install
npm run dev
\`\`\`

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Project Structure

\`\`\`
app/
├── page.tsx              # Home page
├── analyze/
│   └── page.tsx         # Analyze page
├── project/
│   └── [id]/
│       └── page.tsx     # Project detail page
└── layout.tsx           # Root layout

components/
├── top-nav.tsx          # Navigation bar
├── feature-card.tsx     # Feature cards
├── repo-input-modal.tsx # Repository input modal
├── repo-input-bar.tsx   # Repository input bar
├── dashboard-cards.tsx  # Dashboard statistics
├── file-tree.tsx        # File structure tree
├── repo-overview.tsx    # Repository overview
├── project-grid.tsx     # Project grid
├── code-modal.tsx       # Code snippet modal
├── code-diff.tsx        # Diff viewer
└── chat-panel.tsx       # Chat interface
\`\`\`

## Customization

### Connecting Real Endpoints

Replace the mock data by setting the environment variables to point to your backend API:

1. **Analyze Endpoint**: POST request that accepts `{ repoUrl, analysisType }`
2. **Chat Endpoint**: POST request that accepts `{ projectId, message }`
3. **Projects Endpoint**: GET request that returns project data

### Styling

The app uses Tailwind CSS with custom glass morphism utilities. Edit `app/globals.css` to customize colors and effects.

## Deployment

Deploy to Vercel with one click:

\`\`\`bash
vercel deploy
\`\`\`

## License

MIT
