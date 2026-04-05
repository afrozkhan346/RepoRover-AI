"use client";

import { useEffect, useState } from "react";
import { BACKEND_API_BASE } from "@/lib/backend";

type BackendAuthUser = {
   id: string;
   name: string;
   email: string;
   email_verified: boolean;
   image: string | null;
   created_at: string;
   updated_at: string;
};

type BackendAuthSessionResponse = {
   token: string;
   user: BackendAuthUser;
};

type BackendSessionResponse = {
   token: string | null;
   user: BackendAuthUser | null;
};

type FrontendAuthUser = {
   id: string;
   name: string;
   email: string;
   emailVerified: boolean;
   image: string | null;
   createdAt: string;
   updatedAt: string;
};

export type FrontendSession = {
   token: string | null;
   user: FrontendAuthUser | null;
};

type AuthResult<T = unknown> = {
   data: T | null;
   error: { code: string } | null;
};

function mapUser(user: BackendAuthUser): FrontendAuthUser {
   return {
      id: user.id,
      name: user.name,
      email: user.email,
      emailVerified: user.email_verified,
      image: user.image,
      createdAt: user.created_at,
      updatedAt: user.updated_at,
   };
}

function getStoredToken(): string | null {
   if (typeof window === "undefined") {
      return null;
   }
   return localStorage.getItem("bearer_token");
}

async function parseApiError(response: Response): Promise<string> {
   try {
      const payload = (await response.json()) as { detail?: string | { detail?: string; code?: string } };
      if (typeof payload.detail === "string") {
         return payload.detail;
      }
      if (payload.detail && typeof payload.detail === "object" && typeof payload.detail.detail === "string") {
         return payload.detail.detail;
      }
   } catch {
      // ignore JSON parse failure
   }
   return `Request failed with status ${response.status}`;
}

async function registerWithBackend(name: string, email: string, password: string): Promise<BackendAuthSessionResponse> {
   const response = await fetch(`${BACKEND_API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name, email, password }),
   });

   if (!response.ok) {
      throw new Error(await parseApiError(response));
   }

   return (await response.json()) as BackendAuthSessionResponse;
}

async function loginWithBackend(email: string, password: string): Promise<BackendAuthSessionResponse> {
   const response = await fetch(`${BACKEND_API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
   });

   if (!response.ok) {
      throw new Error(await parseApiError(response));
   }

   return (await response.json()) as BackendAuthSessionResponse;
}

async function getBackendSession(token: string | null): Promise<FrontendSession> {
   const response = await fetch(`${BACKEND_API_BASE}/auth/session`, {
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
      cache: "no-store",
   });

   if (!response.ok) {
      throw new Error(await parseApiError(response));
   }

   const payload = (await response.json()) as BackendSessionResponse;
   return {
      token: payload.token,
      user: payload.user ? mapUser(payload.user) : null,
   };
}

async function logoutBackendSession(token: string | null): Promise<void> {
   await fetch(`${BACKEND_API_BASE}/auth/logout`, {
      method: "POST",
      headers: token ? { Authorization: `Bearer ${token}` } : undefined,
   });
}

export const authClient = {
   signIn: {
      email: async ({ email, password }: { email: string; password: string; rememberMe?: boolean; callbackURL?: string }): Promise<AuthResult<FrontendSession>> => {
         try {
            const payload = await loginWithBackend(email, password);
            const session: FrontendSession = { token: payload.token, user: mapUser(payload.user) };
            if (typeof window !== "undefined") {
               localStorage.setItem("bearer_token", payload.token);
            }
            return { data: session, error: null };
         } catch {
            return { data: null, error: { code: "INVALID_CREDENTIALS" } };
         }
      },
      social: async (_input: { provider: string; callbackURL?: string }): Promise<AuthResult<null>> => {
         return { data: null, error: { code: "SOCIAL_AUTH_NOT_AVAILABLE" } };
      },
   },
   signUp: {
      email: async ({ name, email, password }: { name: string; email: string; password: string }): Promise<AuthResult<FrontendSession>> => {
         try {
            const payload = await registerWithBackend(name, email, password);
            const session: FrontendSession = { token: payload.token, user: mapUser(payload.user) };
            if (typeof window !== "undefined") {
               localStorage.setItem("bearer_token", payload.token);
            }
            return { data: session, error: null };
         } catch (error) {
            const message = error instanceof Error ? error.message : "Registration failed";
            const code = message.toUpperCase().includes("ALREADY") ? "USER_ALREADY_EXISTS" : "REGISTRATION_FAILED";
            return { data: null, error: { code } };
         }
      },
   },
   getSession: async (): Promise<{ data: FrontendSession }> => {
      const session = await getBackendSession(getStoredToken());
      return { data: session };
   },
   signOut: async (): Promise<AuthResult<null>> => {
      try {
         await logoutBackendSession(getStoredToken());
         if (typeof window !== "undefined") {
            localStorage.removeItem("bearer_token");
         }
         return { data: null, error: null };
      } catch {
         if (typeof window !== "undefined") {
            localStorage.removeItem("bearer_token");
         }
         return { data: null, error: null };
      }
   },
};

type SessionData = {
   data: FrontendSession | null;
   isPending: boolean;
   error: unknown;
   refetch: () => void;
};

export function useSession(): SessionData {
   const [session, setSession] = useState<FrontendSession | null>(null);
   const [isPending, setIsPending] = useState(true);
   const [error, setError] = useState<unknown>(null);

   const fetchSession = async () => {
      try {
         const token = getStoredToken();
         if (!token) {
            setSession({ user: null, token: null });
            setError(null);
            return;
         }

         const nextSession = await getBackendSession(token);
         setSession(nextSession);
         setError(null);
      } catch (err) {
         setSession({ user: null, token: null });
         setError(err);
      } finally {
         setIsPending(false);
      }
   };

   const refetch = () => {
      setIsPending(true);
      void fetchSession();
   };

   useEffect(() => {
      void fetchSession();
   }, []);

   return { data: session, isPending, error, refetch };
}