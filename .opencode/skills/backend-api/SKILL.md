---
name: backend-api
description: This skill should be used when creating or modifying backend API endpoints, service layer classes, or integrating external APIs (Reddit, OpenAI) in the ClaudeCode Sentiment Monitor project. Specifically trigger this skill for tasks involving Next.js App Router API routes, singleton services, authentication, validation, or business logic implementation.
---

# Backend API Development

## Overview

Guide for developing backend API endpoints and service layer classes in the ClaudeCode Sentiment Monitor project using Next.js 15 App Router, TypeScript, and Prisma ORM.

## When to Use This Skill

Use this skill when:
- Creating new API endpoints
- Modifying existing API routes
- Creating or updating service layer classes
- Integrating with Reddit or OpenAI APIs
- Adding authentication or validation
- Implementing business logic
- Debugging backend errors

## Architecture

### Three-Layer Pattern

```
API Routes (app/api/)          ← Thin HTTP adapters
    ↓
Service Layer (lib/services/)  ← Business logic (singletons)
    ↓
Database (Prisma ORM)          ← Data persistence
```

**Key principle**: API routes are thin adapters. All business logic lives in service classes.

## Quick Start

### Create a New Endpoint

Use the bundled script:

```bash
# From project root
.claude/skills/backend-api/scripts/create_endpoint.py dashboard/stats GET
.claude/skills/backend-api/scripts/create_endpoint.py ingest/refresh POST --protected
```

This generates:
- Route file at `app/api/{endpoint-path}/route.ts`
- Zod validation schema
- Error handling boilerplate
- Authentication check (if `--protected`)
- Cache headers (for GET)

Then customize:
1. Update validation schema
2. Import and call appropriate service
3. Test locally

### Manual Endpoint Creation

If not using the script, follow this structure:

```typescript
// app/api/endpoint/route.ts
import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { exampleService } from "@/lib/services/example.service";

const QuerySchema = z.object({
  param: z.string(),
});

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const params = QuerySchema.parse({
      param: searchParams.get("param"),
    });

    const result = await exampleService.doSomething(params.param);

    return NextResponse.json(result, {
      headers: {
        "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
      },
    });
  } catch (error) {
    console.error("Error in GET /api/endpoint:", error);

    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "Invalid parameters", details: error.errors },
        { status: 400 }
      );
    }

    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
```

## Service Layer

### Creating a Service

All services **must** follow the singleton pattern. See `references/service-patterns.md` for complete examples and existing services (RedditService, SentimentService, AggregationService).

**Template**:
```typescript
// lib/services/example.service.ts
import { PrismaClient } from "@/generated/prisma/client";

export class ExampleService {
  private static instance: ExampleService;
  private prisma: PrismaClient;

  private constructor() {
    this.prisma = new PrismaClient();
  }

  public static getInstance(): ExampleService {
    if (!ExampleService.instance) {
      ExampleService.instance = new ExampleService();
    }
    return ExampleService.instance;
  }

  public async doSomething(param: string): Promise<Result> {
    // Business logic here
  }
}

export const exampleService = ExampleService.getInstance();
```

### Existing Services

Review `references/service-patterns.md` for details on:
- **RedditService** - Reddit API with OAuth, rate limiting, caching
- **SentimentService** - OpenAI analysis with 7-day cache
- **AggregationService** - Daily stats and drill-down queries

## Authentication

Protected endpoints (e.g., `/api/ingest/*`) require `CRON_SECRET`:

```typescript
function verifyAuth(request: NextRequest): boolean {
  const authHeader = request.headers.get("authorization");
  const token = authHeader?.replace("Bearer ", "");
  return token === process.env.CRON_SECRET;
}

export async function POST(request: NextRequest) {
  if (!verifyAuth(request)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  // Protected logic
}
```

**Public endpoints**: `/api/dashboard/*`, `/api/drill-down`, `/api/export/*`

## Validation with Zod

Always validate inputs:

```typescript
import { z } from "zod";

// Define schema
const RequestSchema = z.object({
  range: z.enum(["7d", "30d", "90d"]).default("7d"),
  subreddit: z.enum(["all", "ClaudeAI", "ClaudeCode", "Anthropic"]).default("all"),
});

// Validate query params
const { searchParams } = new URL(request.url);
const params = RequestSchema.parse({
  range: searchParams.get("range"),
  subreddit: searchParams.get("subreddit"),
});

// Validate request body (POST)
const body = await request.json();
const params = RequestSchema.parse(body);
```

## Error Handling

Comprehensive error handling pattern:

```typescript
try {
  // Logic
} catch (error) {
  console.error("Error context:", error);

  // Zod validation errors (400)
  if (error instanceof z.ZodError) {
    return NextResponse.json(
      { error: "Invalid request", details: error.errors },
      { status: 400 }
    );
  }

  // Prisma errors
  if (error instanceof Prisma.PrismaClientKnownRequestError) {
    if (error.code === "P2002") {
      return NextResponse.json(
        { error: "Resource already exists" },
        { status: 409 }
      );
    }
  }

  // Generic error (500)
  return NextResponse.json(
    { error: "Internal server error" },
    { status: 500 }
  );
}
```

## Cache Headers

GET endpoints should use CDN-friendly caching:

```typescript
// Dashboard data (30 minutes)
return NextResponse.json(data, {
  headers: {
    "Cache-Control": "public, s-maxage=1800, stale-while-revalidate=3600",
  },
});

// Drill-down data (5 minutes)
return NextResponse.json(data, {
  headers: {
    "Cache-Control": "public, s-maxage=300, stale-while-revalidate=600",
  },
});
```

## Common Workflows

### Polling Endpoint Pattern

```typescript
export async function POST(request: NextRequest) {
  if (!verifyAuth(request)) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  const results = { /* ... */ };

  for (const subreddit of ["ClaudeAI", "ClaudeCode", "Anthropic"]) {
    try {
      // 1. Fetch new posts
      const posts = await redditService.fetchPosts(subreddit, { limit: 25 });

      // 2. Save to database
      for (const post of posts) {
        await prisma.rawPost.upsert({ /* ... */ });
        results[subreddit].newPosts++;
      }

      // 3. Analyze sentiment
      await sentimentService.analyzeBatch(items, { batchSize: 20 });

      // 4. Recompute aggregates
      await aggregationService.recomputeRange(yesterday, today, [subreddit]);
    } catch (error) {
      console.error(`Error polling ${subreddit}:`, error);
      // Continue to next subreddit
    }
  }

  return NextResponse.json({ success: true, results });
}
```

## Testing Locally

```bash
cd app
npm run dev  # Start server on http://localhost:3000

# Test GET endpoint
curl "http://localhost:3000/api/dashboard/data?range=7d&subreddit=all"

# Test protected POST
curl -X POST http://localhost:3000/api/ingest/poll \
  -H "Authorization: Bearer $CRON_SECRET" \
  -H "Content-Type: application/json"

# Test validation (should return 400)
curl "http://localhost:3000/api/dashboard/data?range=invalid"
```

## Environment Variables

Required in `app/.env.local`:

```bash
DATABASE_URL="postgresql://..."
REDDIT_CLIENT_ID="..."
REDDIT_CLIENT_SECRET="..."
REDDIT_USER_AGENT="ClaudeCodeMonitor/1.0"
OPENAI_API_KEY="sk-..."
CRON_SECRET="secure-random-string"
```

Access in code: `process.env.VARIABLE_NAME`

## Common Pitfalls

Avoid these mistakes:

1. **Business logic in routes** - Use service layer instead
2. **Multiple service instances** - Always use singleton pattern
3. **No input validation** - Always use Zod schemas
4. **Exposing CRON_SECRET** - Never log or return in responses
5. **Missing cache headers** - GET endpoints should be cached
6. **Not logging errors** - Always log with context
7. **Hardcoded values** - Use environment variables
8. **Skipping error handling** - Handle Zod, Prisma, external API errors

## Checklist

When creating/modifying an endpoint:

- [ ] Route file in correct directory (`app/api/endpoint/route.ts`)
- [ ] Exported function matches HTTP method (`GET`, `POST`, etc.)
- [ ] Input validation uses Zod schemas
- [ ] Protected endpoints verify CRON_SECRET
- [ ] Business logic in service layer (not route)
- [ ] Errors caught and logged with context
- [ ] Appropriate HTTP status codes
- [ ] GET endpoints have Cache-Control headers
- [ ] Response format is JSON
- [ ] Tested locally before committing

## Resources

- **Next.js API Routes**: https://nextjs.org/docs/app/building-your-application/routing/route-handlers
- **Zod Docs**: https://zod.dev/
- **Service Patterns**: See `references/service-patterns.md` in this skill
- **Prisma Docs**: https://www.prisma.io/docs

## Examples

See existing implementations:
- `app/api/dashboard/data/route.ts` - GET with caching
- `app/api/ingest/poll/route.ts` - Protected POST
- `app/lib/services/` - Service layer patterns
