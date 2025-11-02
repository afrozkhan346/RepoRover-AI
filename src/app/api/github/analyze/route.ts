import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';

export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    if (!user) {
      return NextResponse.json({ error: 'Authentication required' }, { status: 401 });
    }

    const { githubUrl } = await request.json();

    if (!githubUrl) {
      return NextResponse.json({ error: 'GitHub URL is required' }, { status: 400 });
    }

    // Extract owner and repo from GitHub URL
    const urlPattern = /github\.com\/([^\/]+)\/([^\/]+)/;
    const match = githubUrl.match(urlPattern);

    if (!match) {
      return NextResponse.json({ error: 'Invalid GitHub URL format' }, { status: 400 });
    }

    const [, owner, repo] = match;
    const cleanRepo = repo.replace(/\.git$/, '');

    // Fetch repository data from GitHub API
    const token = process.env.GITHUB_TOKEN;
    const headers: HeadersInit = {
      'Accept': 'application/vnd.github.v3+json',
      'User-Agent': 'RepoRoverAI'
    };

    if (token) {
      headers['Authorization'] = `token ${token}`;
    }

    // Get repository info
    const repoResponse = await fetch(`https://api.github.com/repos/${owner}/${cleanRepo}`, {
      headers
    });

    if (!repoResponse.ok) {
      return NextResponse.json({ 
        error: 'Failed to fetch repository data',
        details: await repoResponse.text()
      }, { status: repoResponse.status });
    }

    const repoData = await repoResponse.json();

    // Get languages
    const languagesResponse = await fetch(`https://api.github.com/repos/${owner}/${cleanRepo}/languages`, {
      headers
    });

    const languages = languagesResponse.ok ? await languagesResponse.json() : {};
    const primaryLanguage = Object.keys(languages)[0] || 'Unknown';

    // Get README
    let readme = '';
    try {
      const readmeResponse = await fetch(`https://api.github.com/repos/${owner}/${cleanRepo}/readme`, {
        headers
      });
      if (readmeResponse.ok) {
        const readmeData = await readmeResponse.json();
        readme = Buffer.from(readmeData.content, 'base64').toString('utf-8');
      }
    } catch (error) {
      console.log('README not available');
    }

    // Get recent commits
    const commitsResponse = await fetch(`https://api.github.com/repos/${owner}/${cleanRepo}/commits?per_page=10`, {
      headers
    });
    const commits = commitsResponse.ok ? await commitsResponse.json() : [];

    // Get file structure (tree)
    const treeResponse = await fetch(`https://api.github.com/repos/${owner}/${cleanRepo}/git/trees/${repoData.default_branch}?recursive=1`, {
      headers
    });
    const tree = treeResponse.ok ? await treeResponse.json() : { tree: [] };

    const analysis = {
      name: repoData.name,
      fullName: repoData.full_name,
      description: repoData.description,
      owner: owner,
      stars: repoData.stargazers_count,
      forks: repoData.forks_count,
      watchers: repoData.watchers_count,
      openIssues: repoData.open_issues_count,
      language: primaryLanguage,
      languages: languages,
      topics: repoData.topics || [],
      license: repoData.license?.name || 'No license',
      createdAt: repoData.created_at,
      updatedAt: repoData.updated_at,
      size: repoData.size,
      defaultBranch: repoData.default_branch,
      readme: readme.substring(0, 5000), // Limit README size
      recentCommits: commits.slice(0, 5).map((commit: any) => ({
        sha: commit.sha,
        message: commit.commit.message,
        author: commit.commit.author.name,
        date: commit.commit.author.date
      })),
      fileCount: tree.tree?.length || 0,
      fileStructure: tree.tree?.slice(0, 100).map((file: any) => ({
        path: file.path,
        type: file.type,
        size: file.size
      })) || []
    };

    return NextResponse.json(analysis, { status: 200 });

  } catch (error) {
    console.error('GitHub analysis error:', error);
    return NextResponse.json({ 
      error: 'Internal server error: ' + (error as Error).message 
    }, { status: 500 });
  }
}