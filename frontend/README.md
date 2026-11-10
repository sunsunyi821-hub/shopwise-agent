# ShopWise Frontend

Next.js 16 (App Router) + TypeScript + Tailwind CSS 4.

```bash
npm install
cp .env.local.example .env.local
npm run dev
```

- `src/app/page.tsx`：聊天页与交互状态
- `src/components/agent-trace.tsx`：Agent 执行轨迹
- `src/components/product-card.tsx` / `product-modal.tsx`：商品卡片与分数拆解
- `src/components/order-modal.tsx`：模拟下单
- `scripts/screenshot.mjs`：生成 README 截图
- `scripts/e2e-smoke.mjs`：完整下单流程冒烟测试

后端 API 默认地址：`http://localhost:8000/api`，可通过
`NEXT_PUBLIC_API_BASE_URL` 覆盖。
