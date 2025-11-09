/**
 * Cache Index - Export all caching utilities
 */

export {
  RedisCache,
  CacheKeys,
  CacheTags,
  initializeCache,
  getCache,
  type CacheConfig,
  type CacheOptions,
  type CacheStats,
} from './redis';

export {
  withCache,
  invalidateCache,
  invalidateCacheTags,
  Cached,
  revalidateCache,
  getWithRevalidate,
  type CacheMiddlewareOptions,
} from './middleware';
