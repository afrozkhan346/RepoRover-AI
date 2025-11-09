/**
 * Cache Middleware for Next.js API Routes
 * 
 * Provides automatic caching for API responses with configurable TTL
 * and cache invalidation strategies.
 */

import { NextRequest, NextResponse } from 'next/server';
import { getCache, CacheOptions } from './redis';

export interface CacheMiddlewareOptions extends CacheOptions {
  /**
   * Function to generate cache key from request
   */
  keyGenerator?: (req: NextRequest) => string;

  /**
   * Condition to determine if response should be cached
   */
  shouldCache?: (req: NextRequest, res: NextResponse) => boolean;

  /**
   * Transform response before caching
   */
  beforeCache?: (data: any) => any;

  /**
   * Transform cached data before returning
   */
  afterCache?: (data: any) => any;

  /**
   * Skip cache on specific conditions
   */
  skipCache?: (req: NextRequest) => boolean;
}

/**
 * Default cache key generator
 */
function defaultKeyGenerator(req: NextRequest): string {
  const url = new URL(req.url);
  const method = req.method;
  const pathname = url.pathname;
  const search = url.search;

  return `api:${method}:${pathname}${search}`;
}

/**
 * Cache middleware wrapper for API routes
 */
export function withCache(
  handler: (req: NextRequest) => Promise<NextResponse>,
  options: CacheMiddlewareOptions = {}
) {
  return async (req: NextRequest): Promise<NextResponse> => {
    const cache = getCache();

    // Skip cache for non-GET requests by default
    if (req.method !== 'GET') {
      return handler(req);
    }

    // Check if cache should be skipped
    if (options.skipCache && options.skipCache(req)) {
      return handler(req);
    }

    // Generate cache key
    const keyGenerator = options.keyGenerator || defaultKeyGenerator;
    const cacheKey = keyGenerator(req);

    try {
      // Try to get from cache
      const cached = await cache.get<any>(cacheKey);

      if (cached !== null) {
        // Transform cached data if needed
        const data = options.afterCache ? options.afterCache(cached) : cached;

        // Return cached response with cache headers
        return NextResponse.json(data, {
          status: 200,
          headers: {
            'X-Cache': 'HIT',
            'Cache-Control': `public, max-age=${options.ttl || 3600}`,
          },
        });
      }

      // Cache miss - execute handler
      const response = await handler(req);

      // Check if response should be cached
      const shouldCache =
        options.shouldCache === undefined
          ? response.status === 200
          : options.shouldCache(req, response);

      if (shouldCache && response.status === 200) {
        // Clone response to read body
        const clonedResponse = response.clone();
        const data = await clonedResponse.json();

        // Transform data before caching if needed
        const dataToCache = options.beforeCache ? options.beforeCache(data) : data;

        // Store in cache
        await cache.set(cacheKey, dataToCache, {
          ttl: options.ttl,
          tags: options.tags,
        });

        // Add cache headers to response
        const headers = new Headers(response.headers);
        headers.set('X-Cache', 'MISS');
        headers.set('Cache-Control', `public, max-age=${options.ttl || 3600}`);

        return new NextResponse(JSON.stringify(data), {
          status: response.status,
          headers,
        });
      }

      return response;
    } catch (error) {
      console.error('Cache middleware error:', error);
      // On error, fallback to handler
      return handler(req);
    }
  };
}

/**
 * Cache invalidation helper
 */
export async function invalidateCache(
  patterns: string | string[]
): Promise<number> {
  const cache = getCache();
  const patternArray = Array.isArray(patterns) ? patterns : [patterns];

  let totalInvalidated = 0;

  for (const pattern of patternArray) {
    const count = await cache.deletePattern(pattern);
    totalInvalidated += count;
  }

  return totalInvalidated;
}

/**
 * Tag-based cache invalidation
 */
export async function invalidateCacheTags(
  tags: string | string[]
): Promise<number> {
  const cache = getCache();
  const tagArray = Array.isArray(tags) ? tags : [tags];

  return cache.invalidateTags(tagArray);
}

/**
 * Response cache decorator (for class methods)
 */
export function Cached(options: CacheMiddlewareOptions = {}) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const cache = getCache();

      // Generate cache key from method name and arguments
      const cacheKey = `method:${target.constructor.name}:${propertyKey}:${JSON.stringify(
        args
      )}`;

      // Try to get from cache
      const cached = await cache.get(cacheKey);
      if (cached !== null) {
        return cached;
      }

      // Execute original method
      const result = await originalMethod.apply(this, args);

      // Store in cache
      await cache.set(cacheKey, result, options);

      return result;
    };

    return descriptor;
  };
}

/**
 * Revalidate cache on specific intervals
 */
export async function revalidateCache(
  key: string,
  fetchFn: () => Promise<any>,
  options?: CacheOptions
): Promise<any> {
  const cache = getCache();

  // Fetch fresh data
  const fresh = await fetchFn();

  // Update cache
  await cache.set(key, fresh, options);

  return fresh;
}

/**
 * Stale-while-revalidate pattern
 */
export async function getWithRevalidate<T>(
  key: string,
  fetchFn: () => Promise<T>,
  options: CacheOptions & { staleTime?: number } = {}
): Promise<T> {
  const cache = getCache();

  // Get cached data
  const cached = await cache.get<T>(key);

  if (cached !== null) {
    // Return stale data immediately
    const response = cached;

    // Revalidate in background
    setImmediate(async () => {
      try {
        const fresh = await fetchFn();
        await cache.set(key, fresh, options);
      } catch (error) {
        console.error('Background revalidation error:', error);
      }
    });

    return response;
  }

  // No cache - fetch and store
  const fresh = await fetchFn();
  await cache.set(key, fresh, options);

  return fresh;
}

export default withCache;
