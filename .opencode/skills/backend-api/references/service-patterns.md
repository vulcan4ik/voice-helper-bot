## Service Layer Patterns

Reference for service architecture in the ClaudeCode Sentiment Monitor project.

### Singleton Pattern (Required)

All services **must** use the singleton pattern:

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

  // Public methods
  public async doSomething(param: string): Promise<Result> {
    // Implementation
  }

  // Private helpers
  private async helperMethod(): Promise<void> {
    // Internal logic
  }
}

// Export singleton instance
export const exampleService = ExampleService.getInstance();
```

### Existing Services

#### RedditService (`lib/services/reddit.service.ts`)

**Purpose**: Reddit API integration with OAuth, rate limiting, and caching

**Key Methods**:
- `fetchPosts(subreddit, options)` - Fetch posts with pagination
- `fetchComments(subreddit, postId)` - Fetch comments for a post
- `backfill(subreddit, daysBack)` - Historical data fetch (up to 90 days)

**Features**:
- OAuth 2.0 with automatic token refresh
- Token bucket rate limiter (60 req/min)
- 3-tier caching (memory → HTTP → database)
- Content filtering (excludes bots, deleted posts)

**Usage**:
```typescript
import { redditService } from "@/lib/services/reddit.service";

const posts = await redditService.fetchPosts("ClaudeAI", {
  limit: 25,
  after: null,
  before: new Date(Date.now() - 24 * 60 * 60 * 1000),
});
```

#### SentimentService (`lib/services/sentiment.service.ts`)

**Purpose**: OpenAI sentiment analysis with intelligent caching

**Key Methods**:
- `analyzeSingle(item)` - Analyze one post/comment
- `analyzeBatch(items, options)` - Batch analyze (up to 20 in parallel)
- `getSentiment(itemId, itemType)` - Retrieve cached result
- `getStatistics(filters)` - Aggregate sentiment stats

**Features**:
- GPT-4o-mini with structured outputs (Zod validation)
- 7-day cache using SHA-256 keys (reduces costs by ~90%)
- Batch processing with progress tracking
- Returns: sentiment (-1 to +1), confidence, component scores, reasoning

**Usage**:
```typescript
import { sentimentService } from "@/lib/services/sentiment.service";

const results = await sentimentService.analyzeBatch(
  items.map(item => ({
    id: item.id,
    type: "post",
    context: item.title,
    text: item.body || "",
    subreddit: item.subreddit,
    createdAt: item.createdAt,
  })),
  {
    batchSize: 20,
    onProgress: (current, total) => console.log(`${current}/${total}`),
  }
);
```

#### AggregationService (`lib/services/aggregation.service.ts`)

**Purpose**: Daily aggregates and drill-down queries

**Key Methods**:
- `computeDailyAggregate(date, subreddit)` - Calculate daily stats
- `saveDailyAggregate(data)` - Upsert aggregate
- `recomputeRange(startDate, endDate, subreddits)` - Batch recomputation
- `getAggregatesForRange(startDate, endDate, subreddit)` - Time series
- `getCombinedAggregates(startDate, endDate, subreddits)` - Merge all
- `getDrillDownData(date, subreddit)` - Top 50 posts/comments
- `exportToCSV(startDate, endDate, subreddits)` - CSV export

**Features**:
- Pre-computed daily stats per subreddit
- Weighted averaging for multi-subreddit views
- Drill-down to daily post/comment details

**Usage**:
```typescript
import { aggregationService } from "@/lib/services/aggregation.service";

// Recompute after ingestion
await aggregationService.recomputeRange(
  new Date(Date.now() - 24 * 60 * 60 * 1000),
  new Date(),
  ["ClaudeAI", "ClaudeCode", "Anthropic"]
);

// Fetch for dashboard
const timeSeries = await aggregationService.getAggregatesForRange(
  startDate,
  endDate,
  "ClaudeAI"
);
```

### Service Best Practices

1. **Singleton only** - Never create multiple instances
2. **Private constructor** - Prevent direct instantiation
3. **Export instance** - `export const service = Service.getInstance()`
4. **Prisma in constructor** - Initialize database client
5. **Public methods** - Service interface (well-documented)
6. **Private helpers** - Internal logic (marked `private`)
7. **Error propagation** - Throw errors, don't swallow
8. **Typed promises** - Always return `Promise<Type>`

### Integration Patterns

#### Polling Workflow
```typescript
// 1. Fetch new content
const posts = await redditService.fetchPosts(subreddit, { limit: 25 });

// 2. Save to database
for (const post of posts) {
  await prisma.rawPost.upsert({ /* ... */ });
}

// 3. Analyze sentiment
const items = /* get unanalyzed */;
await sentimentService.analyzeBatch(items, { batchSize: 20 });

// 4. Recompute aggregates
await aggregationService.recomputeRange(yesterday, today, [subreddit]);
```

#### Backfill Workflow
```typescript
// 1. Historical fetch
const results = await redditService.backfill(subreddit, 90);

// 2. Analyze all
const items = /* all posts/comments */;
await sentimentService.analyzeBatch(items, { batchSize: 20 });

// 3. Recompute entire range
await aggregationService.recomputeRange(
  new Date(Date.now() - 90 * 24 * 60 * 60 * 1000),
  new Date(),
  [subreddit]
);
```

### Error Handling in Services

```typescript
public async methodName(param: string): Promise<Result> {
  try {
    // Service logic
    const data = await this.prisma.model.findMany();
    return { success: true, data };
  } catch (error) {
    // Log with context
    console.error(`Error in ${this.constructor.name}.methodName:`, error);

    // Re-throw for API route to handle
    throw error;
  }
}
```

### Caching Strategies

**RedditService**:
- In-memory: 15 min (posts), 6 hours (comments)
- Cache keys: `"posts:subreddit:cursor"` or `"comments:postId"`

**SentimentService**:
- Database: 7 days
- Cache key: `SHA256(context|text)`
- Cache hit rate: ~90% for repeat content

**AggregationService**:
- Daily aggregates stored in database
- No in-memory caching (fast queries on indexed tables)
