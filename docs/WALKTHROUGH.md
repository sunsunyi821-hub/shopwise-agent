# Code Walkthrough: One Shopping Request End to End

> Goal: be able to explain what happens after a user types a shopping request.

---

## 0. Run the project

Backend:

```bash
cd backend
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm run dev
```

Open <http://localhost:3000>.

If `next dev` hits a Turbopack panic on Windows, delete `.next` and retry, or use `npm run build && npm run start`.

---

## 1. The request journey

User input:

> 我想买一瓶沐浴露，预算 100 以内，敏感肌，最好没有香味

### Station 1: Frontend input

File: `frontend/src/app/page.tsx`, function `sendMessage`

1. Append the user message.
2. Insert a pending assistant message with an agent trace and skeleton.
3. Call `api.chatStream(...)` using `fetch` + `ReadableStream`.
4. Append each `token` event; stop loading on `done`.

### Station 2: API layer

File: `backend/app/api/routes_chat.py`

There are two endpoints:

- `POST /api/chat` — non-streaming JSON.
- `POST /api/chat/stream` — SSE; used by the frontend.

The streaming generator owns its database session:

1. `get_or_create_session()`.
2. Save the user message.
3. Send the `session` event.
4. Iterate `stream_shopping_agent(...)` and forward `stage`, `intent`, `products`, and `token` events.
5. Save the assistant message and product snapshot, then send `recommendation` and `done`.

### Station 3: LangGraph workflow

File: `backend/app/agent/orchestrator.py`

The workflow is a `StateGraph`:

```text
START → parse_intent ─┬→ clarify → END
                      └→ search ─┬→ no_results → END
                                 └→ analyze → rank → recommend → END
```

- `ShoppingGraphState` holds message, profile, intent, products, scored, and recommendation.
- Nodes return partial state updates.
- Conditional edges choose clarification or search, and no-results or analysis.
- Runtime dependencies live in `config["configurable"]`.

Entry points:

- `run_shopping_agent`: `graph.ainvoke(...)`.
- `stream_shopping_agent`: `graph.astream(..., stream_mode="custom")`.

### Station 4: Intent parsing

File: `backend/app/agent/mock.py` for the rule-based version.

The mock parser extracts:

- Category from Chinese synonyms.
- Budget from patterns such as “预算 100”, “100 以内”, “不超过 100”.
- Attributes such as sensitive skin, fragrance-free, oil control, SPF.
- Exclusions such as “不要含香精”.
- Priorities such as “便宜/性价比”.

The real provider uses `INTENT_SYSTEM` in `backend/app/agent/prompts.py` and returns JSON validated by `ShoppingIntent`.

### Station 5: Product search

File: `backend/app/services/catalog.py`, function `search_for_profile`

1. SQL filters: category, budget, minimum rating, excluded brands.
2. Python filters: excluded keywords, included brands, query.
3. Relaxations: minimum rating → budget × 1.2 → category popularity.
4. Return `SearchResult(products, relaxations)`.

### Station 6: Semantic scoring and ranking

Files: `backend/app/services/semantic.py` and `ranking.py`

Semantic scoring:

1. Build a query from the user message and merged profile.
2. Embed the query once.
3. Compare it with cached product vectors using cosine similarity.
4. Pass `{product_id: score}` into ranking.

Ranking computes five scores:

```text
price_score = 1 - normalized price
rating_score = normalized rating
review_score = log(1 + review_count) / log(1 + max_review_count)
preference_score = matched attributes / total attributes
semantic_score = cosine(query, product)
```

Default weights: price 25%, rating 25%, reviews 10%, preference 20%, semantic 20%.
If embeddings are disabled, the semantic dimension is removed and the remaining weights are renormalized.

### Station 7: Recommendation

The `recommend_node` builds a `RecommendationContext` and either:

- streams tokens through `provider.stream_recommendation`, or
- calls `provider.write_recommendation` once.

The model only writes the explanation; ranking is already fixed.

### Station 8: Streaming response

The SSE route sends:

```text
session → stage(parse_intent) → intent
→ stage(search/analyze/rank) → products
→ stage(recommend) → token × N
→ recommendation → done
```

The frontend updates the pending message on every event:

- `stage`: update the agent trace.
- `intent`: show parsed preferences.
- `products`: render product cards early.
- `token`: append to the Markdown recommendation.
- `recommendation`: replace partial text with the final authoritative text.
- `done`: finish loading and refresh the sidebar.

### Station 9: Reviews

1. Open an order and click “Write a review”.
2. `POST /api/reviews` validates ownership, status, and duplicates.
3. `provider.analyze_review(...)` produces a `ReviewAnalysis`.
4. The review is saved and the product rating is updated incrementally.
5. Product details load reviews through `GET /api/products/{id}/reviews`.
6. An existing review can be loaded with `GET /api/orders/{id}/review` and edited with `PUT /api/reviews/{id}`.

### Station 10: Seller listing

1. Click “Sell” in the header and open the seller modal.
2. The seller writes a description, sets a price, chooses a catalog category, and optionally adds a brand.
3. `POST /api/seller/products` validates the category.
4. `provider.analyze_product_description(...)` returns a `SellerProductDraft`.
5. The product is saved with `seller_id`, `rating=0`, and `review_count=0`.
6. The listing is immediately available to buyer search and ranking.

### Station 11: Chat agent

1. Type a high-level goal directly into the bottom chat composer.
2. `/api/chat/stream` asks the supervisor for an `AgentPlan` (skills, args, risk).
3. `normalize_plan` forces read/write risk, confirmation, quantity limits, and order-after-recommendation.
4. Read/draft skills execute as tools; `recommend` reuses the shopping workflow.
5. The first write step becomes a task card in the conversation with status `awaiting_confirmation`.
6. Clicking “Confirm and run” calls `POST /api/agent/tasks/{id}/confirm`, which re-checks price/quantity and executes once.
7. Order, selling, and flash-purchase skills are confirmation-gated; flash purchase is simulated.

### Station 12: MCP marketplace comparison

1. At startup, `MCPMarketplaceClient` launches the bundled MCP server and runs `tools/list`.
2. A goal mentioning JD/Taobao is planned as `market_search`.
3. The workflow calls discovered tools with `tools/call` and receives structured products.
4. Price, rating, review volume, and explicit-need matches produce a value score.
5. SSE sends a `marketplace` event; the UI renders the comparison card and tool-call trace.
6. External products are read-only: policy drops any order step from the same plan.
7. `GET /api/mcp/tools` exposes the discovered tool catalog to the UI panel.

---

## 2. File map

| File | What to understand |
|---|---|
| `backend/app/main.py` | FastAPI assembly, lifespan, routers |
| `backend/app/models.py` | Product, Review, session, message, order tables |
| `backend/app/seed.py` | Why seed data is JSON and reproducible |
| `backend/app/agent/state.py` | Profile, intent, scored product, review analysis, seller draft |
| `backend/app/agent/orchestrator.py` | Recommendation subgraph, nodes, run/stream entry points |
| `backend/app/agent/supervisor.py` | Supervisor graph and task confirmation gate |
| `backend/app/agent/tools.py` | Workflows and MCP search wrapped as agent tools |
| `backend/app/mcp/client.py` | MCP tool discovery and invocation |
| `backend/app/mcp/service.py` | Cross-platform value ranking |
| `backend/app/agent/mock.py` | Rule-based parser and recommendation |
| `backend/app/agent/openai_provider.py` | OpenAI-compatible chat and review analysis |
| `backend/app/services/ranking.py` | Ranking formula and explainability |
| `backend/app/services/catalog.py` | Search and relaxation |
| `backend/app/services/semantic.py` | Vector cache and cosine similarity |
| `backend/app/services/reviews.py` | Review analysis, save, aggregate update |
| `backend/app/services/seller.py` | Seller description analysis and product persistence |
| `backend/app/api/routes_chat.py` | Chat and SSE routes |
| `backend/app/api/routes_reviews.py` | Review routes |
| `backend/app/api/routes_seller.py` | Seller listing routes |
| `backend/app/api/routes_agent.py` | Task agent plan/confirm routes |
| `backend/app/services/agent_policy.py` | Plan validation, risk, caps, and confirmation |
| `backend/app/services/agent_tasks.py` | Skill execution and confirmed write steps |
| `frontend/src/app/page.tsx` | Chat state and streaming orchestration |
| `frontend/src/lib/api.ts` | HTTP client and SSE parser |
| `frontend/src/lib/history.ts` | Replay stored messages into ChatResponse |
| `frontend/src/components/agent-trace.tsx` | Stage-driven trace |
| `frontend/src/components/product-modal.tsx` | Score breakdown and reviews |
| `frontend/src/components/orders-modal.tsx` | Order details and review actions |
| `frontend/src/components/review-modal.tsx` | Create/edit review form |
| `frontend/src/components/seller-modal.tsx` | Seller listing form and structured result |
| `frontend/src/components/agent-console.tsx` | Task plan, results, draft, and confirmation UI |

---

## 3. Exercises

1. Change the default ranking weights and observe the top result.
2. Add a product to `backend/scripts/generate_catalog.py`, regenerate, and reseed the database.
3. Add a new attribute to a product and use it in the intent parser.
4. Add a review-summary node to the LangGraph workflow.
5. Add an English keyword synonym to the mock parser.

---

## 4. Check your understanding

1. Why are filtering and ranking not delegated to the LLM?
2. What is the difference between `ShoppingProfile` and `ShoppingIntent`?
3. What happens when the user says “make it cheaper”?
4. Why is Mock mode important?
5. How are the five score components calculated?
6. Why is ordering a separate endpoint instead of an agent action?
7. How does `session_id` travel between frontend and backend?
8. What changes at one million products?
9. What happens when the LLM returns invalid JSON?
10. How does review editing avoid double-counting the review?

---

## 5. Next steps

1. **Evaluation set**: build a small set of queries and expected products.
2. **Add a review-summary node** to the graph.
3. **Add optional LLM tool calling** for read-only tools such as order status.
4. **Docker + CI**: reproducible deployment and automated checks.
