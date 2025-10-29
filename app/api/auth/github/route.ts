export async function GET() {
  const githubOAuthUrl = process.env.GITHUB_OAUTH_URL

  if (!githubOAuthUrl) {
    return new Response("GitHub OAuth URL not configured", { status: 500 })
  }

  return Response.redirect(githubOAuthUrl)
}
