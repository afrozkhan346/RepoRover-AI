# 🔐 OAuth Configuration Guide

> **Fast Social Login Setup for RepoRover AI**

This guide helps you configure Google and GitHub OAuth for the modern, fast signup experience.

---

## 📋 Overview

RepoRover AI now supports **3 authentication methods**:

1. **🚀 Google OAuth** - One-click signup (Recommended)
2. **🐙 GitHub OAuth** - Perfect for developers
3. **📧 Email/Password** - Traditional signup (Fallback)

---

## 🎯 Google OAuth Setup

### **Step 1: Create Google OAuth App**

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Select your project (or create a new one)
3. Click **"Create Credentials"** → **"OAuth 2.0 Client ID"**
4. Configure OAuth consent screen (if first time):
   - User Type: **External**
   - App name: `RepoRover AI`
   - User support email: Your email
   - Developer contact: Your email
   - Scopes: `email`, `profile`, `openid`
   - Save and continue

### **Step 2: Create OAuth Client**

- Application type: **Web application**
- Name: `RepoRover AI - Production`
- Authorized JavaScript origins:
  ```
  http://localhost:3000
  https://yourdomain.com
  ```
- Authorized redirect URIs:
  ```
  http://localhost:3000/api/auth/callback/google
  https://yourdomain.com/api/auth/callback/google
  ```
- Click **"Create"**
- Copy the **Client ID** and **Client Secret**

### **Step 3: Add to Environment**

Update your `.env` file:

```bash
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

---

## 🐙 GitHub OAuth Setup

### **Step 1: Create GitHub OAuth App**

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click **"New OAuth App"**
3. Fill in the details:
   - Application name: `RepoRover AI`
   - Homepage URL: `https://yourdomain.com` (or `http://localhost:3000` for dev)
   - Application description: `AI-powered learning platform for GitHub repositories`
   - Authorization callback URL:
     ```
     http://localhost:3000/api/auth/callback/github
     ```
     (For production, use your domain)
4. Click **"Register application"**
5. Copy the **Client ID**
6. Click **"Generate a new client secret"**
7. Copy the **Client Secret** (shown only once!)

### **Step 2: Add to Environment**

Update your `.env` file:

```bash
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

---

## 🚀 Quick Start

### **For Development**

1. Create a `.env` file in the project root (copy from `.env.example`):
   ```bash
   cp .env.example .env
   ```

2. Add your OAuth credentials:
   ```bash
   # Google OAuth
   GOOGLE_CLIENT_ID=123456789-abc.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
   
   # GitHub OAuth
   GITHUB_CLIENT_ID=Iv1.abcdefghijklmnop
   GITHUB_CLIENT_SECRET=abcdefghijklmnopqrstuvwxyz1234567890abcd
   ```

3. Restart your development server:
   ```bash
   npm run dev
   ```

4. Visit `http://localhost:3000/register` to see the new fast signup!

### **For Production**

1. Set environment variables on your hosting platform:
   - Vercel: Project Settings → Environment Variables
   - Netlify: Site Settings → Environment Variables
   - Other platforms: Follow their documentation for secrets management

2. Add the same OAuth credentials:
   ```
   GOOGLE_CLIENT_ID=your-google-client-id
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   GITHUB_CLIENT_ID=your-github-client-id
   GITHUB_CLIENT_SECRET=your-github-client-secret
   BETTER_AUTH_SECRET=your-production-secret
   BETTER_AUTH_URL=https://your-domain.com
   ```

3. Deploy your application using your platform's deployment tools

---

## 🧪 Testing OAuth

### **Test Google Login**

1. Go to `/register`
2. Click **"Continue with Google"**
3. Sign in with your Google account
4. You should be redirected to `/dashboard`

### **Test GitHub Login**

1. Go to `/register`
2. Click **"Continue with GitHub"**
3. Authorize the app
4. You should be redirected to `/dashboard`

### **Test Email Signup (Fallback)**

1. Go to `/register`
2. Click **"Continue with Email"**
3. Fill in the form
4. Create account

---

## 🔧 Troubleshooting

### **"Redirect URI mismatch" Error**

**Cause**: The redirect URI in your OAuth app doesn't match the callback URL.

**Solution**: 
- Ensure your OAuth app's authorized redirect URIs include:
  - Development: `http://localhost:3000/api/auth/callback/google` (or `/github`)
  - Production: `https://yourdomain.com/api/auth/callback/google` (or `/github`)

### **"OAuth credentials not found" Error**

**Cause**: Environment variables are not loaded.

**Solution**:
- Check your `.env` file exists and has the correct variables
- Restart your development server after adding env vars
- Verify environment variables are properly configured in production

### **"Access blocked: This app's request is invalid" (Google)**

**Cause**: OAuth consent screen is not configured.

**Solution**:
- Complete the OAuth consent screen setup in Google Cloud Console
- Add your email as a test user (for development)
- Publish your app (for production)

### **"Application suspended" (GitHub)**

**Cause**: GitHub app has issues.

**Solution**:
- Check your GitHub OAuth app settings
- Ensure callback URL is correct
- Verify the app is not rate-limited

---

## 📊 OAuth User Data

When users sign in with Google or GitHub, we automatically:

- ✅ Create user account (if first time)
- ✅ Store email and name
- ✅ Link OAuth account to user profile
- ✅ Generate session token
- ✅ Redirect to dashboard

**Data we collect**:
- Email address
- Full name
- Profile picture (optional)
- OAuth provider ID

**Data we DON'T collect**:
- Passwords (OAuth users don't have passwords)
- Private repository data
- OAuth access tokens (only used for authentication)

---

## 🎨 UI Features

The new signup/login pages include:

- ✅ **Social login first** - Google and GitHub buttons prominently displayed
- ✅ **Email fallback** - Click "Continue with Email" to show traditional form
- ✅ **Loading states** - Spinners show while authenticating
- ✅ **Error handling** - Toast notifications for errors
- ✅ **Responsive design** - Works on all devices
- ✅ **Modern styling** - Gradient backgrounds, shadow effects
- ✅ **Accessibility** - Keyboard navigation, screen reader friendly

---

## 🔐 Security Best Practices

1. **Never commit OAuth secrets** - Add `.env` to `.gitignore` (already done)
2. **Use Secret Manager in production** - Don't hardcode credentials
3. **Rotate secrets regularly** - Change OAuth secrets every 90 days
4. **Restrict redirect URIs** - Only whitelist trusted domains
5. **Monitor OAuth usage** - Check for suspicious login patterns
6. **Use HTTPS in production** - Required for OAuth security

---

## 📚 Additional Resources

- [Better Auth Documentation](https://better-auth.vercel.app/)
- [Google OAuth 2.0 Guide](https://developers.google.com/identity/protocols/oauth2)
- [GitHub OAuth Apps Guide](https://docs.github.com/en/developers/apps/building-oauth-apps)

---

## 🆘 Need Help?

If you encounter issues:

1. Check the [Better Auth Discord](https://discord.gg/better-auth)
2. Review [OAuth troubleshooting docs](https://better-auth.vercel.app/docs/troubleshooting)
3. Open an issue on the RepoRover AI GitHub repo

---

**Built with ❤️ using Next.js and Better Auth**

*Modern, fast, secure authentication* ✨

