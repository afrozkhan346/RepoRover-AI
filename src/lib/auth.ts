import { NextRequest } from "next/server";

type SessionUser = {
  id: string;
  email: string;
  name: string;
};

export const auth = {
  api: {
    getSession: async () => null,
  },
};

// Transitional helper retained for legacy Next route handlers.
export async function getCurrentUser(request: NextRequest): Promise<SessionUser | null> {
  const authHeader = request.headers.get("authorization") || "";
  if (!authHeader.toLowerCase().startsWith("bearer ")) {
    return null;
  }

  return {
    id: "unknown",
    email: "unknown@example.com",
    name: "unknown",
  };
}