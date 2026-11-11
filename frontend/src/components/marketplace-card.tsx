"use client";
import { Activity, PlugZap, Star } from "lucide-react";
import type { MarketplaceProduct, MarketplaceResult } from "@/lib/types";
import { categoryEmoji, categoryGradient, cn, formatPrice, } from "@/lib/utils";
const PLATFORM_STYLES: Record<string, string> = {
    jd: "border-red-200 bg-red-50 text-red-700",
    taobao: "border-orange-200 bg-orange-50 text-orange-700",
};
function PlatformBadge({ platform, label }: {
    platform: string;
    label: string;
}) {
    return (<span className={cn("rounded-full border px-2 py-0.5 text-[10px] font-semibold", PLATFORM_STYLES[platform] ?? "border-line bg-paper text-muted")}>
      {label || platform}
    </span>);
}
function MarketplaceProductCard({ item, rank, budgetMax, }: {
    item: MarketplaceProduct;
    rank: number;
    budgetMax?: number;
}) {
    return (<article className="flex min-w-0 flex-col rounded-2xl border border-line bg-card p-3 shadow-[0_2px_12px_rgba(23,33,29,0.04)]">
      <div className={cn("relative flex h-20 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br", categoryGradient(item.category))}>
        <span className="text-3xl">{categoryEmoji(item.category)}</span>
        <span className="absolute left-2 top-2 flex h-6 w-6 items-center justify-center rounded-full bg-white/85 text-[11px] font-bold text-ink shadow-sm backdrop-blur">
          {rank}
        </span>
        <span className="absolute bottom-2 left-2 rounded-full bg-white/75 px-2 py-0.5 text-[10px] font-medium text-ink-soft backdrop-blur">
          {item.brand}
        </span>
        <span className="absolute right-2 top-2 rounded-full bg-ink/80 px-2 py-0.5 text-[10px] font-semibold text-white backdrop-blur">
          Value {Math.round(item.value_score)}%
        </span>
      </div>

      <div className="mt-2 flex items-center justify-between gap-2">
        <PlatformBadge platform={item.platform} label={item.platform_label}/>
        <span className="text-[10px] text-muted">{item.category}</span>
      </div>

      <h3 className="mt-1.5 line-clamp-2 min-h-[2.4rem] text-xs font-semibold leading-snug text-ink">
        {item.name}
      </h3>

      <div className="mt-1 flex items-baseline gap-1.5">
        <span className="text-base font-bold tracking-tight text-brand">
          {formatPrice(item.price)}
        </span>
        {item.original_price && item.original_price > item.price ? (<span className="text-[10px] text-muted line-through">
            {formatPrice(item.original_price)}
          </span>) : null}
        {budgetMax ? (<span className="ml-auto text-[9px] text-muted">Within budget</span>) : null}
      </div>

      <div className="mt-1 flex items-center gap-1 text-[10px] text-muted">
        <Star className="h-3 w-3 fill-amber-400 text-amber-400"/>
        <span className="font-medium text-ink-soft">{item.rating.toFixed(1)}</span>
        <span>· {item.review_count} reviews</span>
      </div>

      <div className="mt-1.5 flex flex-wrap gap-1">
        {item.tags.slice(0, 3).map((tag) => (<span key={tag} className="rounded-full bg-brand-soft px-1.5 py-0.5 text-[9px] font-medium text-brand-dark">
            {tag}
          </span>))}
      </div>

      <p className="mt-1.5 line-clamp-2 text-[10px] leading-relaxed text-ink-soft">
        {item.reasons[0] ?? item.description}
      </p>

      <p className="mt-1.5 text-[9px] text-muted">MCP demo product · No real transaction</p>
    </article>);
}
export function MarketplaceCard({ result }: {
    result: MarketplaceResult;
}) {
    const budgetMax = result.budget_max ?? undefined;
    const calls = result.tool_calls ?? [];
    const okCalls = calls.filter((call) => call.ok);
    return (<div className="overflow-hidden rounded-2xl border border-line bg-card">
      <div className="border-b border-line/70 bg-gradient-to-r from-brand-soft/70 via-card to-card px-4 py-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="flex h-6 w-6 items-center justify-center rounded-lg bg-ink text-white">
            <PlugZap className="h-3.5 w-3.5"/>
          </span>
          <span className="text-xs font-semibold text-ink">
            MCP marketplace comparison
          </span>
          <span className="rounded-full bg-card px-2 py-0.5 text-[10px] font-medium text-muted">
            {okCalls.length} tool calls
          </span>
          <span className="ml-auto text-[10px] text-muted">
            tools/list → tools/call
          </span>
        </div>

        <div className="mt-2 flex flex-wrap gap-1.5">
          {result.platforms.map((platform) => (<PlatformBadge key={platform} platform={platform} label={platform === "jd" ? "JD" : platform === "taobao" ? "Taobao" : platform}/>))}
          {result.products.length ? (<span className="rounded-full bg-card px-2 py-0.5 text-[10px] text-muted">
              Shortlisted {result.products.length} external products
            </span>) : null}
        </div>
      </div>

      <div className="p-3">
        {result.products.length ? (<div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {result.products.map((item, index) => (<MarketplaceProductCard key={`${item.platform}-${item.id}`} item={item} rank={index + 1} budgetMax={budgetMax}/>))}
          </div>) : (<p className="rounded-xl bg-paper/60 px-3 py-4 text-center text-xs text-muted">
            No external products matched the constraints.
          </p>)}

        {calls.length ? (<div className="mt-3 rounded-xl border border-line/70 bg-paper/40 px-3 py-2">
            <div className="flex items-center gap-1.5 text-[10px] font-semibold text-ink-soft">
              <Activity className="h-3 w-3 text-brand"/>
              MCP tool calls
            </div>
            <div className="mt-1.5 space-y-1">
              {calls.map((call, index) => (<div key={`${call.name}-${index}`} className="flex flex-wrap items-center gap-2 text-[10px] text-muted">
                  <code className="rounded bg-card px-1.5 py-0.5 font-mono text-[9px] text-ink-soft">
                    {call.name}
                  </code>
                  <span className={cn("rounded-full px-1.5 py-0.5 text-[9px] font-medium", call.ok
                    ? "bg-emerald-50 text-emerald-700"
                    : "bg-red-50 text-red-700")}>
                    {call.ok ? "ok" : "failed"}
                  </span>
                  {call.duration_ms != null ? (<span>{call.duration_ms}ms</span>) : null}
                  {!call.ok && call.error ? (<span className="truncate text-red-600">{call.error}</span>) : null}
                </div>))}
            </div>
          </div>) : null}

        <p className="mt-2 px-1 text-[9px] leading-relaxed text-muted">
          {result.note ||
            "MCP demo data; no live marketplace or payment connection."}
        </p>
      </div>
    </div>);
}
