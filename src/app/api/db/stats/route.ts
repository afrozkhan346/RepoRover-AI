import { NextRequest, NextResponse } from 'next/server';
import { getCurrentUser } from '@/lib/auth';
import { dbOptimization } from '@/db/optimization';

/**
 * GET /api/db/stats
 * Get database performance statistics and optimization suggestions
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

    const {
      queryMonitor,
      connectionPool,
      n1Detector,
      dbAnalytics,
    } = dbOptimization;

    // Gather all statistics
    const stats = {
      queryPerformance: {
        ...queryMonitor.getStatistics(),
        slowQueries: queryMonitor.getSlowQueries(100).slice(0, 10),
      },
      connectionPool: connectionPool.getStats(),
      n1Patterns: n1Detector.getPatterns(),
      optimizationSuggestions: await dbAnalytics.analyzeAndSuggest(),
      timestamp: new Date().toISOString(),
    };

    return NextResponse.json(stats);
  } catch (error) {
    console.error('Error fetching database stats:', error);
    return NextResponse.json(
      { error: 'Failed to fetch database statistics' },
      { status: 500 }
    );
  }
}

/**
 * POST /api/db/stats
 * Run database maintenance operations
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
    // if (user.role !== 'admin') {
    //   return NextResponse.json(
    //     { error: 'Admin access required' },
    //     { status: 403 }
    //   );
    // }

    const body = await request.json();
    const { operation } = body;

    const { dbAnalytics } = dbOptimization;

    let result;
    switch (operation) {
      case 'vacuum':
        result = await dbAnalytics.vacuum();
        break;
      case 'analyze':
        result = await dbAnalytics.analyze();
        break;
      case 'integrity-check':
        result = await dbAnalytics.integrityCheck();
        break;
      case 'get-table-sizes':
        result = await dbAnalytics.getTableSizes();
        break;
      case 'get-index-stats':
        result = await dbAnalytics.getIndexStats();
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
    console.error('Error running database operation:', error);
    return NextResponse.json(
      { error: 'Failed to run database operation' },
      { status: 500 }
    );
  }
}

/**
 * DELETE /api/db/stats
 * Clear performance monitoring logs
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

    const { queryMonitor, connectionPool } = dbOptimization;

    queryMonitor.clear();
    connectionPool.resetStats();

    return NextResponse.json({
      message: 'Performance logs cleared',
      timestamp: new Date().toISOString(),
    });
  } catch (error) {
    console.error('Error clearing stats:', error);
    return NextResponse.json(
      { error: 'Failed to clear statistics' },
      { status: 500 }
    );
  }
}
