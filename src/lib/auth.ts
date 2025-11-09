import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { bearer } from "better-auth/plugins";
import { NextRequest } from 'next/server';
import { headers } from "next/headers"
import { db } from "@/db";
 
export const auth = betterAuth({
	database: drizzleAdapter(db, {
		provider: "sqlite",
	}),
	emailAndPassword: {    
		enabled: true
	},
	socialProviders: {
		google: {
			clientId: process.env.GOOGLE_CLIENT_ID || "",
			clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
			enabled: !!(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET),
		},
		github: {
			clientId: process.env.GITHUB_CLIENT_ID || "",
			clientSecret: process.env.GITHUB_CLIENT_SECRET || "",
			enabled: !!(process.env.GITHUB_CLIENT_ID && process.env.GITHUB_CLIENT_SECRET),
		},
	},
	plugins: [bearer()],
});

// Session validation helper
export async function getCurrentUser(request: NextRequest) {
  const session = await auth.api.getSession({ headers: await headers() });
  return session?.user || null;
}