# Database Inventory

Date: 2026-04-03
Based on: [Migration Boundaries](MIGRATION_BOUNDARIES.md)

This inventory classifies the current database schema, seeds, and migration artifacts for conversion into the final Python data layer.

## Current Database Schema To Convert

### Auth and identity
- `src/db/schema.ts` - `user`
- `src/db/schema.ts` - `session`
- `src/db/schema.ts` - `account`
- `src/db/schema.ts` - `verification`

### Learning and progress
- `src/db/schema.ts` - `userProgress`
- `src/db/schema.ts` - `learningPaths`
- `src/db/schema.ts` - `lessons`
- `src/db/schema.ts` - `lessonProgress`
- `src/db/schema.ts` - `achievements`
- `src/db/schema.ts` - `userAchievements`
- `src/db/schema.ts` - `quizzes`
- `src/db/schema.ts` - `quizAttempts`

### Repository analysis data
- `src/db/schema.ts` - `repositories`

## Database Runtime And Helper Files To Replace

- `src/db/index.ts`
- `src/db/optimization.ts`
- `src/db/queries.optimized.ts`
- `src/db/schema.optimized.ts`
- `drizzle.config.ts`

## Seed Files To Convert

- `src/db/seeds/achievements.ts`
- `src/db/seeds/learning_paths.ts`
- `src/db/seeds/lessons.ts`
- `src/db/seeds/quizzes.ts`

## Migration Artifacts To Retire Or Recreate In Python

- `drizzle/0000_silly_iceman.sql`
- `drizzle/0001_wet_leech.sql`
- `drizzle/0002_add_performance_indexes.sql`
- `drizzle/meta/_journal.json`
- `drizzle/meta/0000_snapshot.json`
- `drizzle/meta/0001_snapshot.json`

## Data Layer Conversion Notes

### Keep as concept only
- Table naming and relationships are useful as a domain map
- Content model for learning paths, lessons, quizzes, achievements, progress, and repositories should remain

### Rebuild in Python
- Schema definitions
- Migrations
- Seed scripts
- Query helpers
- Optimization helpers

## Database Migration Rule

Use the current schema as a domain reference, not as runtime code. The final implementation should be expressed in Python with SQLite first and PostgreSQL as the production target.

## Notes

- Auth tables are only needed if the new backend keeps equivalent identity management.
- Performance helpers may inspire Python-side caching or query batching, but they should not be ported mechanically.
- The repository-analysis table should likely evolve to support richer graph and explanation metadata in the new architecture.