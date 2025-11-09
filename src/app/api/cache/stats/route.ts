import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { getCache, invalidateCacheTags } from '@/lib/cache';

/**
 * GET /api/cache/stats
 * Get cache statistics and health
 * Admin only endpoint
 */
export async function GET(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    
    if (!user) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    // TODO: Add admin role check
    // if (user.role !== 'admin') {
    //   return NextResponse.json(
    //     { error: 'Admin access required' },
    //     { status: 403 }
    //   );
    // }

    const cache = getCache();

    // Get cache statistics
    const stats = cache.getStats();
    const isConnected = cache.isConnected();
    const size = await cache.getSize();
    const info = await cache.getInfo();

    // Parse Redis info for useful metrics
    const usedMemory = info.match(/used_memory_human:([^\r\n]+)/)?.[1] || 'N/A';
    const connectedClients = info.match(/connected_clients:(\d+)/)?.[1] || '0';
    const totalCommands = info.match(/total_commands_processed:(\d+)/)?.[1] || '0';

    return NextResponse.json({
      status: isConnected ? 'connected' : 'disconnected',
      stats: {
        ...stats,
        hitRatePercentage: (stats.hitRate * 100).toFixed(2) + '%',
      },
      redis: {
        connected: isConnected,
        keyCount: size,
        usedMemory,
        connectedClients: parseInt(connectedClients),
        totalCommands: parseInt(totalCommands),
      },
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error fetching cache stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch cache statistics' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/cache/stats
 * Invalidate cache by tag or pattern
 * Admin only endpoint
 */
export async function POST(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    
    if (!user) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    // TODO: Add admin role check

    const body = await request.json();
    const { operation, tags, pattern } = body;

    const cache = getCache();

    let result;
    switch (operation) {
      case 'invalidate-tags':
        if (!tags || !Array.isArray(tags)) {
          return NextResponse.json(
            { error: 'Tags array required for invalidate-tags operation' },
            { status: 400 }
          );
        }
        result = await invalidateCacheTags(tags);
        break;

      case 'invalidate-pattern':
        if (!pattern) {
          return NextResponse.json(
            { error: 'Pattern required for invalidate-pattern operation' },
            { status: 400 }
          );
        }
        result = await cache.deletePattern(pattern);
        break;

      case 'flush':
        result = await cache.flush();
        break;

      case 'reset-stats':
        cache.resetStats();
        result = true;
        break;

      case 'ping':
        result = await cache.ping();
        break;

      default:
        return NextResponse.json(
          { error: `Unknown operation: ${operation}` },
          { status: 400 }
        );
    }

    return NextResponse.json({
      operation,
      result,
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error executing cache operation:', error);
    return NextResponse.json(
      { error: 'Failed to execute cache operation' },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/cache/stats
 * Clear all cache data
 * Admin only endpoint
 */
export async function DELETE(request: NextRequest) {
  try {
    const user = await getCurrentUser(request);
    
    if (!user) {
      return NextResponse.json(
        { error: 'Authentication required' },
        { status: 401 }
      );
    }

    // TODO: Add admin role check

    const cache = getCache();
    const success = await cache.flush();

    if (!success) {
      return NextResponse.json(
        { error: 'Failed to flush cache' },
        { status: 500 }
      );
    }

    return NextResponse.json({
      message: 'Cache flushed successfully',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error flushing cache:', error);
    return NextResponse.json(
      { error: 'Failed to flush cache' },
      { status: 500 }
    );
  }
}
