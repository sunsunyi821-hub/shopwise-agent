"use client";

import {
  Bot,
  CheckCircle2,
  Loader2,
  Play,
  ShieldAlert,
  Sparkles,
  X,
} from "lucide-react";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";
import type { AgentTask, ScoredProduct } from "@/lib/types";
import { cn, formatPrice } from "@/lib/utils";

const STATUS_LABELS: Record<string, string> = {
  planned: "Planning",
  awaiting_confirmation: "Awaiting confirmation",
  completed: "Completed",
  failed: "Failed",
  needs_input: "Needs input",
};

const RISK_LABELS: Record<string, string> = {
  read: "Read-only",
  write: "Write",
  high_risk: "High risk",
};

const SKILL_LABELS: Record<string, string> = {
  recommend: "Recommend products",
  order: "Create order",
  sell: "List product",
  flash_sale: "Flash purchase",
  error: "Error",
  planner: "Planner",
};

const EXAMPLES = [
  "帮我推荐一款适合敏感肌的沐浴露，预算 100 以内",
  "帮我找一款适合敏感肌的沐浴露，100 元以内，合适的话我想买两瓶",
  "帮我把这瓶闲置洗发水挂到二手平台，价格定在 60 元",
  "帮我抢购一瓶洗发水，预算 100 以内",
];

function StatusBadge({ status }: { status: string }) {
  const tone =
    status === "completed"
      ? "bg-brand-soft text-brand-dark"
      : status === "awaiting_confirmation"
        ? "bg-amber-50 text-amber-800"
        : status === "failed"
          ? "bg-red-50 text-red-700"
          : "bg-paper text-muted";
  return (
    <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", tone)}>
      {STATUS_LABELS[status] ?? status}
    </span>
  );
}

function ResultCard({ result }: { result: Record<string, unknown> }) {
  const skill = String(result.skill ?? "");
  const products = Array.isArray(result.products)
    ? (result.products as ScoredProduct[])
    : [];
  const order =
    result.order && typeof result.order === "object"
      ? (result.order as Record<string, unknown>)
      : null;
  const product =
    result.product && typeof result.product === "object"
      ? (result.product as Record<string, unknown>)
      : null;

  return (
    <div className="rounded-xl border border-line bg-paper/40 p-3">
      <div className="flex items-center justify-between gap-2">
        <span className="text-[11px] font-semibold text-ink">
          {SKILL_LABELS[skill] ?? skill}
        </span>
        {skill === "error" ? (
          <span className="text-[10px] text-red-600">Not executed</span>
        ) : (
          <CheckCircle2 className="h-3.5 w-3.5 text-brand" />
        )}
      </div>

      {typeof result.summary === "string" && result.summary ? (
        <p className="mt-1.5 line-clamp-4 whitespace-pre-wrap text-[11px] leading-relaxed text-ink-soft">
          {result.summary}
        </p>
      ) : null}

      {products.length ? (
        <div className="mt-2 space-y-1">
          {products.slice(0, 3).map((item) => (
            <div
              key={item.product.id}
              className="flex items-center justify-between gap-2 text-[11px]"
            >
              <span className="truncate text-ink-soft">
                {item.product.name}
              </span>
              <span className="shrink-0 font-semibold text-brand">
                {formatPrice(item.product.price)}
              </span>
            </div>
          ))}
        </div>
      ) : null}

      {order ? (
        <div className="mt-2 rounded-lg bg-card px-2.5 py-2 text-[11px] text-ink-soft">
          Order {String(order.id)} · {String(order.product_name)} ·{" "}
          {String(order.quantity)} items · {formatPrice(Number(order.total_price))}
        </div>
      ) : null}

      {product ? (
        <div className="mt-2 rounded-lg bg-card px-2.5 py-2 text-[11px] text-ink-soft">
          {String(product.name)} · {formatPrice(Number(product.price))}
        </div>
      ) : null}

      {typeof result.message === "string" && result.message ? (
        <p className="mt-1.5 text-[11px] leading-relaxed text-red-600">
          {result.message}
        </p>
      ) : null}

      {typeof result.note === "string" && result.note ? (
        <p className="mt-1.5 text-[10px] leading-relaxed text-amber-700">
          {result.note}
        </p>
      ) : null}
    </div>
  );
}

function DraftCard({ draft }: { draft: Record<string, unknown> }) {
  const skill = String(draft.skill ?? "");
  const sellerDraft =
    draft.draft && typeof draft.draft === "object"
      ? (draft.draft as Record<string, unknown>)
      : null;

  return (
    <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-4">
      <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-800">
        <ShieldAlert className="h-3.5 w-3.5" />
        Pending write operation · {SKILL_LABELS[skill] ?? skill}
      </div>

      {sellerDraft ? (
        <div className="mt-2 text-xs leading-relaxed text-ink-soft">
          <p className="font-semibold text-ink">{String(sellerDraft.name)}</p>
          <p className="mt-1">
            {String(sellerDraft.brand)} · {String(draft.category)} ·{" "}
            {formatPrice(Number(draft.price))}
          </p>
          <p className="mt-1 line-clamp-3">{String(sellerDraft.description)}</p>
        </div>
      ) : (
        <div className="mt-2 text-xs leading-relaxed text-ink-soft">
          <p className="font-semibold text-ink">
            {String(draft.product_name)}
          </p>
          <p className="mt-1">
            Qty {String(draft.quantity)} · Total{" "}
            {formatPrice(Number(draft.total))}
          </p>
          <p className="mt-1 text-[11px] text-muted">
            Shipping address: {String(draft.address)}
          </p>
          {typeof draft.note === "string" ? (
            <p className="mt-1 text-[11px] text-amber-700">{draft.note}</p>
          ) : null}
        </div>
      )}

      <p className="mt-2 text-[10px] leading-relaxed text-amber-800">
        Nothing runs until you confirm. The server re-checks price, quantity, and execution state for orders and flash purchases.
      </p>
    </div>
  );
}

export function AgentConsole({
  open,
  userId,
  onClose,
}: {
  open: boolean;
  userId: string;
  onClose: () => void;
}) {
  const [goal, setGoal] = useState("");
  const [task, setTask] = useState<AgentTask | null>(null);
  const [loading, setLoading] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setGoal("");
      setTask(null);
      setError(null);
      setLoading(false);
      setConfirming(false);
    }
  }, [open]);

  if (!open) return null;

  async function run() {
    const text = goal.trim();
    if (text.length < 5) {
      setError("Please describe the task in at least 5 characters");
      return;
    }
    setLoading(true);
    setError(null);
    try {
      setTask(await api.runAgentTask(text, userId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Task planning failed");
    } finally {
      setLoading(false);
    }
  }

  async function confirm() {
    if (!task) return;
    setConfirming(true);
    setError(null);
    try {
      setTask(await api.confirmAgentTask(task.id, userId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Execution failed");
    } finally {
      setConfirming(false);
    }
  }

  const steps = task?.plan.steps ?? [];
  const awaiting = task?.status === "awaiting_confirmation" && task.draft;

  return (
    <div
      className="fixed inset-0 z-[66] flex items-end justify-center bg-ink/45 backdrop-blur-sm sm:items-center sm:p-6"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="flex max-h-[92vh] w-full max-w-2xl flex-col rounded-t-3xl bg-card shadow-2xl sm:rounded-3xl"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b border-line/70 px-5 py-4">
          <div>
            <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
              <Bot className="h-3.5 w-3.5" />
              Top-level Task Agent
            </p>
            <h2 className="mt-0.5 text-lg font-bold text-ink">
              Plan, choose skills, confirm execution
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-full p-1.5 text-muted transition hover:bg-paper"
            aria-label="Close"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="scrollbar-thin flex-1 overflow-y-auto px-5 py-4">
          <div className="rounded-xl bg-brand-soft/60 px-3 py-2 text-[11px] leading-relaxed text-brand-dark">
            <span className="flex items-center gap-1 font-semibold">
              <Sparkles className="h-3 w-3" />
              Agent plans; workflows execute
            </span>
            Recommendation is read-only. Ordering, listing, and flash purchases are write operations and only run after you confirm.
          </div>

          <div className="mt-3 flex flex-wrap gap-1.5">
            {EXAMPLES.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => setGoal(example)}
                className="rounded-full border border-line bg-paper px-2.5 py-1 text-left text-[10px] text-ink-soft transition hover:border-brand/30 hover:text-brand"
              >
                {example}
              </button>
            ))}
          </div>

          <label className="mt-3 block">
            <span className="text-xs font-medium text-ink-soft">Task goal</span>
            <textarea
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
              rows={3}
              maxLength={1000}
              className="mt-1.5 w-full resize-none rounded-xl border border-line bg-paper/50 px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:bg-white"
              placeholder="e.g. find a body wash for sensitive skin under ¥100 and buy two bottles if it fits"
            />
          </label>

          <button
            type="button"
            onClick={() => void run()}
            disabled={loading}
            className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Play className="h-4 w-4" />
            )}
            {loading ? "Agent is planning and running read-only steps…" : "Plan and run"}
          </button>

          {error ? (
            <p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
              {error}
            </p>
          ) : null}

          {task ? (
            <div className="mt-4 space-y-3">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-semibold text-ink">Task plan</span>
                  <StatusBadge status={task.status} />
                  <span className="rounded-full bg-paper px-2 py-0.5 text-[10px] text-muted">
                    {RISK_LABELS[task.risk] ?? task.risk}
                  </span>
                </div>
                <span className="text-[10px] text-muted">
                  {task.id.slice(0, 8)}
                </span>
              </div>

              {task.plan.summary ? (
                <p className="text-[11px] leading-relaxed text-ink-soft">
                  {task.plan.summary}
                </p>
              ) : null}

              <div className="space-y-1.5">
                {steps.map((step, index) => (
                  <div
                    key={`${step.skill}-${index}`}
                    className="flex items-center justify-between gap-2 rounded-xl border border-line bg-card px-3 py-2"
                  >
                    <div className="flex items-center gap-2">
                      <span className="flex h-5 w-5 items-center justify-center rounded-full bg-brand-soft text-[10px] font-semibold text-brand-dark">
                        {index + 1}
                      </span>
                      <span className="text-xs font-medium text-ink">
                        {SKILL_LABELS[step.skill] ?? step.skill}
                      </span>
                    </div>
                    <span
                      className={cn(
                        "rounded-full px-2 py-0.5 text-[10px]",
                        step.risk === "read"
                          ? "bg-paper text-muted"
                          : step.risk === "high_risk"
                            ? "bg-red-50 text-red-700"
                            : "bg-amber-50 text-amber-800",
                      )}
                    >
                      {RISK_LABELS[step.risk] ?? step.risk}
                      {step.requires_confirmation ? " · confirmation required" : ""}
                    </span>
                  </div>
                ))}
              </div>

              {task.results.length ? (
                <div className="space-y-2">
                  <p className="text-xs font-semibold text-ink">Results</p>
                  {task.results.map((result, index) => (
                    <ResultCard key={index} result={result} />
                  ))}
                </div>
              ) : null}

              {awaiting ? (
                <div>
                  <DraftCard draft={task.draft!} />
                  <button
                    type="button"
                    onClick={() => void confirm()}
                    disabled={confirming}
                    className="mt-2 flex w-full items-center justify-center gap-2 rounded-xl bg-ink py-2.5 text-sm font-semibold text-white transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60"
                  >
                    {confirming ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <CheckCircle2 className="h-4 w-4" />
                    )}
                    {confirming ? "Executing…" : "Confirm and execute"}
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
