# ShopWise Roadmap

> A 3-week project plan, updated to reflect the current MVP.

---

## Current status

Completed:

- [x] Backend skeleton, configuration, SQLite, seed catalog
- [x] Product API and structured search
- [x] Multi-criteria ranking with explainable breakdowns
- [x] LLM provider abstraction (Mock / Anthropic / OpenAI-compatible)
- [x] LangGraph `StateGraph` workflow with conditional branches
- [x] SSE streaming for stages, products, and recommendation tokens
- [x] Next.js chat UI with product cards, score breakdown, and agent trace
- [x] Demo checkout and order history
- [x] Post-purchase reviews with LLM structuring
- [x] Review viewing and editing
- [x] Session replay with persisted product snapshots
- [x] Backend tests and Playwright smoke test

Next:

- [ ] Evaluation set and recommendation-quality metrics
- [ ] Optional LLM tool calling for read-only tools
- [ ] Docker Compose
- [ ] GitHub Actions
- [ ] Public deployment

---

## Week 1 — Core agent

### Day 1: Skeleton

- FastAPI app, settings, database engine
- SQLModel tables
- Product seed data

### Day 2: Catalog and search

- Product API
- Category, budget, rating, and keyword filters
- Constraint relaxation

### Day 3: Ranking

- Price, rating, review count, preference match
- Explainable score breakdown
- Shortlist narrowing for exact preference matches

### Day 4: Intent parsing

- Mock rule parser
- Budget, category, attributes, exclusions, priorities
- Clarification when category is missing

### Day 5: LLM provider

- Provider protocol
- Anthropic and OpenAI-compatible clients
- JSON validation and fallback

### Day 6: Agent workflow

- LangGraph state and nodes
- Conditional branches for clarification and empty results
- Recommendation generation

### Day 7: Frontend shell

- Chat layout
- Session sidebar
- Product cards and details

---

## Week 2 — Streaming, reviews, and polish

### Day 8: SSE

- `POST /api/chat/stream`
- Stage, intent, products, token, recommendation, done events
- Frontend `ReadableStream` parser

### Day 9: Reviews

- Review table and fields
- LLM review analysis
- Product review display

### Day 10: Review editing

- Order ownership validation
- Duplicate prevention
- Re-analysis on edit
- Product aggregate replacement

### Day 11: Review and preference memory

- Multi-turn profile merging
- “Make it cheaper” behavior
- Session replay

### Day 12: UI quality

- Loading and empty states
- Error handling
- Responsive layout
- Screenshots

### Day 13: Testing

- Unit tests for ranking, semantic retrieval, and review analysis
- API tests for orders, reviews, and sessions
- Playwright checkout/review flow

### Day 14: Documentation

- README, architecture, LangGraph guide, walkthrough

---

## Week 3 — Evaluation and deployment

### Day 15: Evaluation set

- 20–30 realistic queries
- Expected category, budget behavior, and top-3 products
- Regression checks for ranking changes

### Day 16: Prompt robustness

- Invalid JSON handling
- Timeouts and retries
- Review-analysis language handling

### Day 17: Performance

- Measure p50/p95 latency for chat and streaming
- Cache embeddings
- Reduce unnecessary model calls

### Day 18: Docker

- Backend image
- Frontend image
- Compose file with SQLite volume

### Day 19: CI

- Backend tests and Ruff
- Frontend build
- Optional Playwright job

### Day 20: Deployment

- Deploy backend and frontend
- Configure environment variables and CORS
- Smoke test the public demo

### Day 21: Portfolio polish

- Record a demo GIF
- Add screenshots
- Update README and resume bullets
- Prepare interview talking points

---

## Interview talking points

- **Architecture**: LangGraph state machine + deterministic tools + LLM at the edges.
- **Retrieval**: structured filters for correctness, embeddings for soft relevance.
- **Explainability**: score breakdown and reasons for every recommendation.
- **Safety**: human confirmation before order creation; server-side prices.
- **Reviews**: LLM structuring with Pydantic validation and a rule-based fallback.
- **Trade-offs**: why not let the model choose products; how to scale to a vector database; how to evaluate quality.
