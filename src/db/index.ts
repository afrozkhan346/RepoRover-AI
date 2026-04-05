
import { drizzle } from 'drizzle-orm/libsql';
import { createClient } from '@libsql/client';
import * as schema from '@/db/schema';

const databaseUrl = process.env.TURSO_CONNECTION_URL;

const dbUnavailable = new Proxy(
  {},
  {
    get() {
      throw new Error('TURSO_CONNECTION_URL is not configured');
    },
  },
);

export const db = databaseUrl
  ? drizzle(
      createClient({
        url: databaseUrl,
        authToken: process.env.TURSO_AUTH_TOKEN ?? '',
      }),
      { schema },
    )
  : (dbUnavailable as unknown as ReturnType<typeof drizzle>);

export type Database = typeof db;