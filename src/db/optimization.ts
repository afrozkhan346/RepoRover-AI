/**
 * Database Optimization Utilities
 * 
 * This module provides utilities for database performance optimization including:
 * - Query performance monitoring
 * - Connection pooling management
 * - N+1 query detection and prevention
 * - Database statistics and analysis
 * - Index usage recommendations
 */

import { db } from './index';
import { sql } from 'drizzle-orm';

// Query performance tracker
class QueryPerformanceMonitor {
  private queryLogs: Array<{
    query: string;
    duration: number;
    timestamp: Date;
    stackTrace?: string;
  }> = [];

  private slowQueryThreshold = 100; // ms
  private maxLogSize = 1000;

  /**
   * Log a query execution
   */
  logQuery(query: string, duration: number, stackTrace?: string) {
    this.queryLogs.push({
      query,
      duration,
      timestamp: new Date(),
      stackTrace,
    });

    // Trim logs if too large
    if (this.queryLogs.length > this.maxLogSize) {
      this.queryLogs = this.queryLogs.slice(-this.maxLogSize);
    }

    // Warn on slow queries
    if (duration > this.slowQueryThreshold) {
      console.warn(`[SLOW QUERY] ${duration}ms: ${query.substring(0, 100)}...`);
      if (stackTrace) {
        console.warn('Stack trace:', stackTrace);
      }
    }
  }

  /**
   * Get slow queries
   */
  getSlowQueries(threshold = this.slowQueryThreshold) {
    return this.queryLogs
      .filter(log => log.duration > threshold)
      .sort((a, b) => b.duration - a.duration);
  }

  /**
   * Get query statistics
   */
  getStatistics() {
    if (this.queryLogs.length === 0) {
      return {
        totalQueries: 0,
        avgDuration: 0,
        maxDuration: 0,
        minDuration: 0,
        slowQueries: 0,
      };
    }

    const durations = this.queryLogs.map(log => log.duration);
    const slowQueries = this.queryLogs.filter(
      log => log.duration > this.slowQueryThreshold
    );

    return {
      totalQueries: this.queryLogs.length,
      avgDuration: durations.reduce((a, b) => a + b, 0) / durations.length,
      maxDuration: Math.max(...durations),
      minDuration: Math.min(...durations),
      slowQueries: slowQueries.length,
      slowQueryPercentage: (slowQueries.length / this.queryLogs.length) * 100,
    };
  }

  /**
   * Clear query logs
   */
  clear() {
    this.queryLogs = [];
  }

  /**
   * Export logs for analysis
   */
  export() {
    return JSON.stringify(this.queryLogs, null, 2);
  }
}

// Global query monitor instance
export const queryMonitor = new QueryPerformanceMonitor();

/**
 * Wrap database queries with performance monitoring
 */
export function monitoredQuery<T>(
  queryFn: () => Promise<T>,
  queryName: string
): Promise<T> {
  const startTime = Date.now();
  const stackTrace = new Error().stack;

  return queryFn()
    .then(result => {
      const duration = Date.now() - startTime;
      queryMonitor.logQuery(queryName, duration, stackTrace);
      return result;
    })
    .catch(error => {
      const duration = Date.now() - startTime;
      queryMonitor.logQuery(`[ERROR] ${queryName}`, duration, stackTrace);
      throw error;
    });
}

/**
 * Connection pool manager
 */
class ConnectionPoolManager {
  private activeConnections = 0;
  private maxConnections = 20;
  private connectionQueue: Array<() => void> = [];
  private stats = {
    totalConnections: 0,
    peakConnections: 0,
    queuedRequests: 0,
    timeouts: 0,
  };

  /**
   * Acquire a connection from the pool
   */
  async acquireConnection<T>(
    operation: () => Promise<T>,
    timeout = 5000
  ): Promise<T> {
    // If under limit, execute immediately
    if (this.activeConnections < this.maxConnections) {
      this.activeConnections++;
      this.stats.totalConnections++;
      this.stats.peakConnections = Math.max(
        this.stats.peakConnections,
        this.activeConnections
      );

      try {
        return await operation();
      } finally {
        this.activeConnections--;
        this.processQueue();
      }
    }

    // Otherwise, queue the request
    this.stats.queuedRequests++;
    return new Promise((resolve, reject) => {
      const timeoutId = setTimeout(() => {
        this.stats.timeouts++;
        reject(new Error('Connection pool timeout'));
      }, timeout);

      this.connectionQueue.push(async () => {
        clearTimeout(timeoutId);
        this.activeConnections++;
        this.stats.totalConnections++;
        this.stats.peakConnections = Math.max(
          this.stats.peakConnections,
          this.activeConnections
        );

        try {
          const result = await operation();
          resolve(result);
        } catch (error) {
          reject(error);
        } finally {
          this.activeConnections--;
          this.processQueue();
        }
      });
    });
  }

  /**
   * Process queued connection requests
   */
  private processQueue() {
    if (
      this.connectionQueue.length > 0 &&
      this.activeConnections < this.maxConnections
    ) {
      const nextRequest = this.connectionQueue.shift();
      if (nextRequest) {
        nextRequest();
      }
    }
  }

  /**
   * Get connection pool statistics
   */
  getStats() {
    return {
      ...this.stats,
      activeConnections: this.activeConnections,
      queueLength: this.connectionQueue.length,
      utilizationRate:
        (this.activeConnections / this.maxConnections) * 100,
    };
  }

  /**
   * Reset statistics
   */
  resetStats() {
    this.stats = {
      totalConnections: 0,
      peakConnections: 0,
      queuedRequests: 0,
      timeouts: 0,
    };
  }
}

// Global connection pool instance
export const connectionPool = new ConnectionPoolManager();

/**
 * N+1 Query detector and preventer
 */
class N1QueryDetector {
  private queryPatterns: Map<string, number> = new Map();
  private threshold = 5; // Warn if same query pattern repeats more than this
  private resetInterval = 1000; // Reset counters every second

  constructor() {
    // Reset counters periodically
    setInterval(() => {
      this.queryPatterns.clear();
    }, this.resetInterval);
  }

  /**
   * Track a query and detect potential N+1 patterns
   */
  trackQuery(query: string) {
    // Extract query pattern (remove specific values)
    const pattern = this.normalizeQuery(query);
    const count = (this.queryPatterns.get(pattern) || 0) + 1;
    this.queryPatterns.set(pattern, count);

    if (count > this.threshold) {
      console.warn(
        `[N+1 QUERY DETECTED] Query pattern repeated ${count} times:`,
        pattern.substring(0, 100) + '...'
      );
      console.warn('Consider using JOIN or batch queries to optimize.');
    }
  }

  /**
   * Normalize query to detect patterns
   */
  private normalizeQuery(query: string): string {
    return query
      .replace(/\d+/g, '?') // Replace numbers
      .replace(/'[^']*'/g, '?') // Replace string literals
      .replace(/"[^"]*"/g, '?') // Replace quoted identifiers
      .toLowerCase()
      .trim();
  }

  /**
   * Get detected patterns
   */
  getPatterns() {
    return Array.from(this.queryPatterns.entries())
      .filter(([_, count]) => count > this.threshold)
      .sort((a, b) => b[1] - a[1])
      .map(([pattern, count]) => ({ pattern, count }));
  }
}

// Global N+1 detector instance
export const n1Detector = new N1QueryDetector();

/**
 * Database statistics and analysis
 */
export class DatabaseAnalytics {
  /**
   * Get table sizes
   */
  async getTableSizes() {
    try {
      const result = await db.all(sql`
        SELECT 
          name as tableName,
          (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as rowCount
        FROM sqlite_master m
        WHERE type='table'
        ORDER BY name
      `);
      return result;
    } catch (error) {
      console.error('Error getting table sizes:', error);
      return [];
    }
  }

  /**
   * Get index usage statistics
   */
  async getIndexStats() {
    try {
      const result = await db.all(sql`
        SELECT 
          name,
          tbl_name as tableName,
          sql
        FROM sqlite_master
        WHERE type='index' AND sql IS NOT NULL
        ORDER BY tbl_name, name
      `);
      return result;
    } catch (error) {
      console.error('Error getting index stats:', error);
      return [];
    }
  }

  /**
   * Analyze database and suggest optimizations
   */
  async analyzeAndSuggest() {
    const suggestions = [];

    // Check for missing indexes on foreign keys
    const tables = await db.all(sql`
      SELECT name FROM sqlite_master WHERE type='table'
    `);

    for (const table of tables as any[]) {
      const tableName = table.name as string;
      const tableInfo = await db.all(
        sql`PRAGMA foreign_key_list(${sql.raw(tableName)})`
      );
      
      if (tableInfo.length > 0) {
        suggestions.push({
          type: 'info',
          message: `Table ${tableName} has ${tableInfo.length} foreign key(s)`,
          recommendation: 'Ensure indexes exist on foreign key columns for optimal JOIN performance',
        });
      }
    }

    // Check query performance
    const slowQueries = queryMonitor.getSlowQueries();
    if (slowQueries.length > 0) {
      suggestions.push({
        type: 'warning',
        message: `Found ${slowQueries.length} slow queries`,
        recommendation: 'Review slow queries and add appropriate indexes',
        details: slowQueries.slice(0, 5),
      });
    }

    // Check for N+1 patterns
    const n1Patterns = n1Detector.getPatterns();
    if (n1Patterns.length > 0) {
      suggestions.push({
        type: 'warning',
        message: `Detected ${n1Patterns.length} potential N+1 query patterns`,
        recommendation: 'Use JOIN queries or batch loading to reduce query count',
        details: n1Patterns.slice(0, 3),
      });
    }

    // Check connection pool utilization
    const poolStats = connectionPool.getStats();
    if (poolStats.utilizationRate > 80) {
      suggestions.push({
        type: 'warning',
        message: `Connection pool utilization at ${poolStats.utilizationRate.toFixed(1)}%`,
        recommendation: 'Consider increasing connection pool size or optimizing queries',
        stats: poolStats,
      });
    }

    return suggestions;
  }

  /**
   * Run VACUUM to optimize database file
   */
  async vacuum() {
    try {
      await db.run(sql`VACUUM`);
      console.log('Database VACUUM completed successfully');
      return { success: true, message: 'Database optimized' };
    } catch (error) {
      console.error('Error running VACUUM:', error);
      return { success: false, error };
    }
  }

  /**
   * Run ANALYZE to update query planner statistics
   */
  async analyze() {
    try {
      await db.run(sql`ANALYZE`);
      console.log('Database ANALYZE completed successfully');
      return { success: true, message: 'Query planner statistics updated' };
    } catch (error) {
      console.error('Error running ANALYZE:', error);
      return { success: false, error };
    }
  }

  /**
   * Get database integrity check
   */
  async integrityCheck() {
    try {
      const result = await db.all(sql`PRAGMA integrity_check`) as any[];
      const firstResult = result[0] as any;
      return {
        success: firstResult?.integrity_check === 'ok',
        details: result,
      };
    } catch (error) {
      console.error('Error checking integrity:', error);
      return { success: false, error };
    }
  }
}

// Global analytics instance
export const dbAnalytics = new DatabaseAnalytics();

/**
 * Batch query executor to prevent N+1 queries
 */
export class BatchQueryExecutor {
  private batchSize = 50;
  private batchDelay = 10; // ms

  /**
   * Execute queries in batches
   */
  async executeBatch<T, R>(
    items: T[],
    queryFn: (batch: T[]) => Promise<R[]>
  ): Promise<R[]> {
    const results: R[] = [];
    
    for (let i = 0; i < items.length; i += this.batchSize) {
      const batch = items.slice(i, i + this.batchSize);
      const batchResults = await queryFn(batch);
      results.push(...batchResults);
      
      // Small delay between batches to prevent overwhelming the database
      if (i + this.batchSize < items.length) {
        await new Promise(resolve => setTimeout(resolve, this.batchDelay));
      }
    }
    
    return results;
  }

  /**
   * Data loader pattern for batching and caching
   */
  createDataLoader<K, V>(
    batchFn: (keys: K[]) => Promise<(V | Error)[]>,
    options?: {
      cache?: boolean;
      maxBatchSize?: number;
    }
  ) {
    const cache = options?.cache ? new Map<K, V>() : null;
    const maxBatchSize = options?.maxBatchSize || this.batchSize;
    let batchQueue: Array<{
      key: K;
      resolve: (value: V) => void;
      reject: (error: Error) => void;
    }> = [];
    let batchTimeout: NodeJS.Timeout | null = null;

    const executeBatch = async () => {
      const currentBatch = batchQueue;
      batchQueue = [];
      batchTimeout = null;

      try {
        const keys = currentBatch.map(item => item.key);
        const results = await batchFn(keys);

        currentBatch.forEach((item, index) => {
          const result = results[index];
          if (result instanceof Error) {
            item.reject(result);
          } else {
            if (cache) {
              cache.set(item.key, result);
            }
            item.resolve(result);
          }
        });
      } catch (error) {
        currentBatch.forEach(item => {
          item.reject(error as Error);
        });
      }
    };

    return async (key: K): Promise<V> => {
      // Check cache first
      if (cache?.has(key)) {
        return cache.get(key)!;
      }

      // Add to batch queue
      return new Promise<V>((resolve, reject) => {
        batchQueue.push({ key, resolve, reject });

        // Execute batch immediately if size limit reached
        if (batchQueue.length >= maxBatchSize) {
          if (batchTimeout) {
            clearTimeout(batchTimeout);
          }
          executeBatch();
        }
        // Otherwise schedule batch execution
        else if (!batchTimeout) {
          batchTimeout = setTimeout(executeBatch, this.batchDelay);
        }
      });
    };
  }
}

// Global batch executor instance
export const batchExecutor = new BatchQueryExecutor();

/**
 * Export optimization utilities
 */
export const dbOptimization = {
  queryMonitor,
  connectionPool,
  n1Detector,
  dbAnalytics,
  batchExecutor,
  monitoredQuery,
};

export default dbOptimization;
