/**
 * Redis Cache Client for RepoRover AI
 * 
 * Provides caching functionality with automatic serialization,
 * TTL management, and connection pooling.
 */

import { Redis } from 'ioredis';

export interface CacheConfig {
  host: string;
  port: number;
  password?: string;
  db?: number;
  keyPrefix?: string;
  ttl?: number; // Default TTL in seconds
  maxRetriesPerRequest?: number;
  enableReadyCheck?: boolean;
  lazyConnect?: boolean;
}

export interface CacheOptions {
  ttl?: number; // Time to live in seconds
  tags?: string[]; // Tags for cache invalidation
}

export interface CacheStats {
  hits: number;
  misses: number;
  sets: number;
  deletes: number;
  errors: number;
  hitRate: number;
}

/**
 * Redis Cache Client with automatic serialization and TTL management
 */
export class RedisCache {
  private client: Redis;
  private config: CacheConfig;
  private stats: CacheStats = {
    hits: 0,
    misses: 0,
    sets: 0,
    deletes: 0,
    errors: 0,
    hitRate: 0,
  };

  constructor(config: CacheConfig) {
    this.config = {
      maxRetriesPerRequest: 3,
      enableReadyCheck: true,
      lazyConnect: false,
      ttl: 3600, // 1 hour default
      ...config,
    };

    this.client = new Redis({
      host: this.config.host,
      port: this.config.port,
      password: this.config.password,
      db: this.config.db || 0,
      keyPrefix: this.config.keyPrefix || 'reporover:',
      maxRetriesPerRequest: this.config.maxRetriesPerRequest,
      enableReadyCheck: this.config.enableReadyCheck,
      lazyConnect: this.config.lazyConnect,
      retryStrategy: (times: number) => {
        const delay = Math.min(times * 50, 2000);
        return delay;
      },
    });

    this.setupEventHandlers();
  }

  /**
   * Setup Redis event handlers
   */
  private setupEventHandlers(): void {
    this.client.on('error', (error: Error) => {
      console.error('Redis Client Error:', error);
      this.stats.errors++;
    });

    this.client.on('connect', () => {
      console.log('Redis Client Connected');
    });

    this.client.on('ready', () => {
      console.log('Redis Client Ready');
    });

    this.client.on('close', () => {
      console.log('Redis Client Connection Closed');
    });

    this.client.on('reconnecting', () => {
      console.log('Redis Client Reconnecting...');
    });
  }

  /**
   * Generate a cache key with prefix
   */
  private generateKey(key: string): string {
    return key;
  }

  /**
   * Get value from cache
   */
  async get<T>(key: string): Promise<T | null> {
    try {
      const cacheKey = this.generateKey(key);
      const value = await this.client.get(cacheKey);

      if (value === null) {
        this.stats.misses++;
        this.updateHitRate();
        return null;
      }

      this.stats.hits++;
      this.updateHitRate();

      return JSON.parse(value) as T;
    } catch (error) {
      console.error('Cache GET error:', error);
      this.stats.errors++;
      return null;
    }
  }

  /**
   * Set value in cache with optional TTL
   */
  async set<T>(key: string, value: T, options?: CacheOptions): Promise<boolean> {
    try {
      const cacheKey = this.generateKey(key);
      const serialized = JSON.stringify(value);
      const ttl = options?.ttl || this.config.ttl || 3600;

      await this.client.setex(cacheKey, ttl, serialized);

      // Store tags for invalidation
      if (options?.tags && options.tags.length > 0) {
        await this.addTagsToKey(cacheKey, options.tags);
      }

      this.stats.sets++;
      return true;
    } catch (error) {
      console.error('Cache SET error:', error);
      this.stats.errors++;
      return false;
    }
  }

  /**
   * Delete value from cache
   */
  async delete(key: string): Promise<boolean> {
    try {
      const cacheKey = this.generateKey(key);
      const result = await this.client.del(cacheKey);
      
      this.stats.deletes++;
      return result > 0;
    } catch (error) {
      console.error('Cache DELETE error:', error);
      this.stats.errors++;
      return false;
    }
  }

  /**
   * Delete multiple keys matching a pattern
   */
  async deletePattern(pattern: string): Promise<number> {
    try {
      const keys = await this.client.keys(this.generateKey(pattern));
      
      if (keys.length === 0) {
        return 0;
      }

      const result = await this.client.del(...keys);
      this.stats.deletes += result;
      
      return result;
    } catch (error) {
      console.error('Cache DELETE PATTERN error:', error);
      this.stats.errors++;
      return 0;
    }
  }

  /**
   * Check if key exists
   */
  async exists(key: string): Promise<boolean> {
    try {
      const cacheKey = this.generateKey(key);
      const result = await this.client.exists(cacheKey);
      return result === 1;
    } catch (error) {
      console.error('Cache EXISTS error:', error);
      this.stats.errors++;
      return false;
    }
  }

  /**
   * Get or set value (cache-aside pattern)
   */
  async getOrSet<T>(
    key: string,
    fetchFn: () => Promise<T>,
    options?: CacheOptions
  ): Promise<T> {
    // Try to get from cache
    const cached = await this.get<T>(key);
    if (cached !== null) {
      return cached;
    }

    // Fetch fresh data
    const fresh = await fetchFn();

    // Store in cache
    await this.set(key, fresh, options);

    return fresh;
  }

  /**
   * Add tags to a key for group invalidation
   */
  private async addTagsToKey(key: string, tags: string[]): Promise<void> {
    const pipeline = this.client.pipeline();

    for (const tag of tags) {
      const tagKey = `tag:${tag}`;
      pipeline.sadd(tagKey, key);
    }

    await pipeline.exec();
  }

  /**
   * Invalidate all keys with a specific tag
   */
  async invalidateTag(tag: string): Promise<number> {
    try {
      const tagKey = `tag:${tag}`;
      const keys = await this.client.smembers(tagKey);

      if (keys.length === 0) {
        return 0;
      }

      const pipeline = this.client.pipeline();
      
      // Delete all keys with this tag
      for (const key of keys) {
        pipeline.del(key);
      }

      // Delete the tag set
      pipeline.del(tagKey);

      const results = await pipeline.exec();
      const deletedCount = keys.length;

      this.stats.deletes += deletedCount;

      return deletedCount;
    } catch (error) {
      console.error('Cache INVALIDATE TAG error:', error);
      this.stats.errors++;
      return 0;
    }
  }

  /**
   * Invalidate multiple tags
   */
  async invalidateTags(tags: string[]): Promise<number> {
    let totalDeleted = 0;

    for (const tag of tags) {
      const deleted = await this.invalidateTag(tag);
      totalDeleted += deleted;
    }

    return totalDeleted;
  }

  /**
   * Update hit rate statistic
   */
  private updateHitRate(): void {
    const total = this.stats.hits + this.stats.misses;
    this.stats.hitRate = total > 0 ? this.stats.hits / total : 0;
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    return { ...this.stats };
  }

  /**
   * Reset statistics
   */
  resetStats(): void {
    this.stats = {
      hits: 0,
      misses: 0,
      sets: 0,
      deletes: 0,
      errors: 0,
      hitRate: 0,
    };
  }

  /**
   * Get Redis info
   */
  async getInfo(): Promise<string> {
    try {
      return await this.client.info();
    } catch (error) {
      console.error('Cache INFO error:', error);
      return '';
    }
  }

  /**
   * Get cache size (number of keys)
   */
  async getSize(): Promise<number> {
    try {
      return await this.client.dbsize();
    } catch (error) {
      console.error('Cache SIZE error:', error);
      return 0;
    }
  }

  /**
   * Flush all keys from the current database
   */
  async flush(): Promise<boolean> {
    try {
      await this.client.flushdb();
      return true;
    } catch (error) {
      console.error('Cache FLUSH error:', error);
      return false;
    }
  }

  /**
   * Check if Redis is connected
   */
  isConnected(): boolean {
    return this.client.status === 'ready';
  }

  /**
   * Ping Redis server
   */
  async ping(): Promise<boolean> {
    try {
      const result = await this.client.ping();
      return result === 'PONG';
    } catch (error) {
      console.error('Cache PING error:', error);
      return false;
    }
  }

  /**
   * Close Redis connection
   */
  async disconnect(): Promise<void> {
    await this.client.quit();
  }

  /**
   * Get the raw Redis client (for advanced operations)
   */
  getClient(): Redis {
    return this.client;
  }
}

/**
 * Cache key builders for consistency
 */
export const CacheKeys = {
  learningPath: (id: string | number) => `learning-path:${id}`,
  learningPaths: () => 'learning-paths:all',
  lesson: (id: string | number) => `lesson:${id}`,
  lessonsByPath: (pathId: string | number) => `lessons:path:${pathId}`,
  userProgress: (userId: string) => `user-progress:${userId}`,
  userAchievements: (userId: string) => `user-achievements:${userId}`,
  achievement: (id: string | number) => `achievement:${id}`,
  achievements: () => 'achievements:all',
  quiz: (id: string | number) => `quiz:${id}`,
  quizzesByLesson: (lessonId: string | number) => `quizzes:lesson:${lessonId}`,
  leaderboard: (limit: number = 100) => `leaderboard:top:${limit}`,
  userDashboard: (userId: string) => `dashboard:${userId}`,
  repository: (userId: string, repoId: string) => `repository:${userId}:${repoId}`,
  repositories: (userId: string) => `repositories:${userId}`,
};

/**
 * Cache tag constants for invalidation
 */
export const CacheTags = {
  LEARNING_PATHS: 'learning-paths',
  LESSONS: 'lessons',
  ACHIEVEMENTS: 'achievements',
  USER_PROGRESS: 'user-progress',
  QUIZZES: 'quizzes',
  LEADERBOARD: 'leaderboard',
  REPOSITORIES: 'repositories',
};

/**
 * Default cache instance (singleton)
 */
let defaultCache: RedisCache | null = null;

/**
 * Initialize default cache instance
 */
export function initializeCache(config?: Partial<CacheConfig>): RedisCache {
  const redisConfig: CacheConfig = {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379', 10),
    password: process.env.REDIS_PASSWORD,
    db: parseInt(process.env.REDIS_DB || '0', 10),
    keyPrefix: process.env.REDIS_KEY_PREFIX || 'reporover:',
    ttl: parseInt(process.env.REDIS_DEFAULT_TTL || '3600', 10),
    ...config,
  };

  defaultCache = new RedisCache(redisConfig);
  return defaultCache;
}

/**
 * Get default cache instance
 */
export function getCache(): RedisCache {
  if (!defaultCache) {
    defaultCache = initializeCache();
  }
  return defaultCache;
}

export default RedisCache;
