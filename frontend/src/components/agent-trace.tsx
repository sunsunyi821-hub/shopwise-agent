"use client";
import { BarChart3, Check, Loader2, ScanSearch, Search, Sparkles, } from "lucide-react";
import type { ScoredProduct, ShoppingIntent, StreamStage, StreamStageStatus, } from "@/lib/types";
import { cn } from "@/lib/utils";
type StepState = "done" | "active" | "waiting";
const STAGE_ORDER: StreamStage[] = [
    "parse_intent",
    "search",
    "analyze",
    "rank",
    "recommend",
];
const ATTRIBUTE_LABELS: Record<string, string> = {
    skin_type: "Skin type",
    scent: "Scent",
    hair_type: "Hair type",
    function: "Benefit",
    texture: "Texture",
    volume_ml: "Volume",
    spf: "SPF",
    pa: "PA",
    flavor: "Flavor",
};
function intentDetail(intent?: ShoppingIntent | null) {
    if (!intent)
        return "Parsing your request…";
    const parts: string[] = [];
    if (intent.category)
        parts.push(intent.category);
    if (intent.budget_max)
        parts.push(`Budget ≤ ¥${intent.budget_max}`);
    if (intent.min_rating)
        parts.push(`Rating ≥ ${intent.min_rating}`);
    for (const [key, value] of Object.entries(intent.attributes ?? {})) {
        parts.push(`${ATTRIBUTE_LABELS[key] ?? key}：${String(value)}`);
    }
    if (intent.priorities.length)
        parts.push(`Priority: ${intent.priorities.join(", ")}`);
    return parts.length ? parts.join(" · ") : "Request understood";
}
export function AgentTrace({ intent, products, loading, provider, stage, stageStatus, }: {
    intent?: ShoppingIntent | null;
    products?: ScoredProduct[];
    loading?: boolean;
    provider?: string;
    stage?: StreamStage;
    stageStatus?: StreamStageStatus;
}) {
    const done = !loading && Boolean(intent);
    const hasSemantic = products?.some((item) => "semantic" in item.breakdown);
    const stageIndex = stage ? STAGE_ORDER.indexOf(stage) : -1;
    const stageActive = stageStatus !== "done";
    const stepState = (index: number, fallback: StepState): StepState => {
        if (!loading || !stage || stageIndex === -1)
            return fallback;
        if (stage === "done")
            return "done";
        if (stageStatus === "done") {
            return index <= stageIndex ? "done" : "waiting";
        }
        if (index < stageIndex)
            return "done";
        if (index === stageIndex)
            return "active";
        return "waiting";
    };
    const steps = [
        {
            label: "Understand request",
            detail: intentDetail(intent),
            icon: ScanSearch,
            state: stepState(0, intent ? "done" : loading ? "active" : "waiting"),
        },
        {
            label: "Search products",
            detail: products?.length
                ? hasSemantic
                    ? `Semantic retrieval + structured filters: ${products.length} candidates`
                    : `${products.length} candidates found in the catalog`
                : stage === "search" && stageActive
                    ? "Semantic retrieval + structured filters…"
                    : "Waiting for request",
            icon: Search,
            state: stepState(1, products?.length ? "done" : loading && intent ? "active" : "waiting"),
        },
        {
            label: "Analyze reviews",
            detail: products?.length
                ? `Summarizing ratings, review counts, pros, and cons for ${products.length} products`
                : stage === "analyze" && stageActive
                    ? "Summarizing ratings, review counts, pros, and cons…"
                    : "Waiting for candidates",
            icon: BarChart3,
            state: stepState(2, products?.length ? "done" : "waiting"),
        },
        {
            label: "Rank products",
            detail: products?.length
                ? hasSemantic
                    ? "Price · Rating · Reviews · Preference · Semantic relevance"
                    : "Price · Rating · Reviews · Preference match"
                : stage === "rank" && stageActive
                    ? "Calculating weighted scores…"
                    : "Waiting for review analysis",
            icon: BarChart3,
            state: stepState(3, products?.length ? "done" : "waiting"),
        },
        {
            label: "Write recommendation",
            detail: stage === "recommend" && stageActive
                ? "Model is writing the recommendation…"
                : done
                    ? provider === "mock"
                        ? "Mock mode generated an explainable recommendation"
                        : "Model generated the recommendation and notes"
                    : "Waiting for ranking",
            icon: Sparkles,
            state: stepState(4, done
                ? "done"
                : stage === "recommend" && stageActive
                    ? "active"
                    : "waiting"),
        },
    ];
    return (<div className="rounded-2xl border border-line bg-card/80 p-4">
      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2 text-xs font-semibold tracking-wide text-ink">
          <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand text-white">
            <Sparkles className="h-3 w-3"/>
          </span>
          Agent trace
        </div>
        <span className="rounded-full bg-paper px-2 py-0.5 text-[10px] font-medium text-muted">
          {provider === "mock"
            ? "Mock demo"
            : provider === "openai"
                ? "OpenAI-compatible"
                : provider ?? "Agent"}
        </span>
      </div>

      <ol className="space-y-2.5">
        {steps.map((step) => {
            const Icon = step.icon;
            return (<li key={step.label} className="flex gap-2.5">
              <span className={cn("mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border", step.state === "done" &&
                    "border-brand/20 bg-brand-soft text-brand", step.state === "active" &&
                    "border-accent/30 bg-accent-soft text-accent", step.state === "waiting" &&
                    "border-line bg-paper text-muted/60")}>
                {step.state === "done" ? (<Check className="h-3 w-3"/>) : step.state === "active" ? (<Loader2 className="h-3 w-3 animate-spin"/>) : (<Icon className="h-3 w-3"/>)}
              </span>
              <div className="min-w-0">
                <p className={cn("text-xs font-semibold", step.state === "waiting" ? "text-muted" : "text-ink")}>
                  {step.label}
                </p>
                <p className="mt-0.5 truncate text-[11px] text-muted">
                  {step.detail}
                </p>
              </div>
            </li>);
        })}
      </ol>
    </div>);
}
