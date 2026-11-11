"use client";
import { CheckCircle2, Loader2, ShieldAlert } from "lucide-react";
import type { AgentTask } from "@/lib/types";
import { cn, formatPrice } from "@/lib/utils";
const STATUS_LABELS: Record<string, string> = {
    awaiting_confirmation: "Pending confirmation",
    completed: "Completed",
    failed: "Failed",
    needs_input: "Needs more info",
};
const SKILL_LABELS: Record<string, string> = {
    recommend: "Recommend",
    order: "Create order",
    sell: "Sell product",
    flash_sale: "Flash purchase",
    error: "Error",
    planner: "Plan",
};
const RISK_LABELS: Record<string, string> = {
    read: "Read-only",
    write: "Write",
    high_risk: "High risk",
};
export function ChatTaskCard({ task, confirming, onConfirm, }: {
    task: AgentTask;
    confirming: boolean;
    onConfirm: () => void;
}) {
    const steps = task.plan.steps ?? [];
    const draft = task.draft;
    const awaiting = task.status === "awaiting_confirmation" && draft;
    const sellerDraft = draft?.draft && typeof draft.draft === "object"
        ? (draft.draft as Record<string, unknown>)
        : null;
    return (<div className="rounded-2xl border border-line bg-card p-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-ink">Agent task plan</span>
        <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-semibold", task.status === "completed"
            ? "bg-brand-soft text-brand-dark"
            : task.status === "failed"
                ? "bg-red-50 text-red-700"
                : "bg-amber-50 text-amber-800")}>
          {STATUS_LABELS[task.status] ?? task.status}
        </span>
        <span className="rounded-full bg-paper px-2 py-0.5 text-[10px] text-muted">
          {RISK_LABELS[task.risk] ?? task.risk}
        </span>
      </div>

      {task.plan.summary ? (<p className="mt-2 text-[11px] leading-relaxed text-ink-soft">
          {task.plan.summary}
        </p>) : null}

      <div className="mt-2 space-y-1.5">
        {steps.map((step, index) => (<div key={`${step.skill}-${index}`} className="flex items-center justify-between gap-2 rounded-lg border border-line bg-paper/40 px-2.5 py-1.5">
            <span className="text-[11px] text-ink">
              {index + 1}. {SKILL_LABELS[step.skill] ?? step.skill}
            </span>
            <span className="text-[10px] text-muted">
              {step.requires_confirmation ? "Needs confirmation" : "Read-only"}
            </span>
          </div>))}
      </div>

      {task.results.length ? (<div className="mt-3 space-y-1">
          {task.results.map((result, index) => {
                const order = result.order && typeof result.order === "object"
                    ? (result.order as Record<string, unknown>)
                    : null;
                const product = result.product && typeof result.product === "object"
                    ? (result.product as Record<string, unknown>)
                    : null;
                return (<div key={index} className="text-[11px] leading-relaxed text-ink-soft">
                {typeof result.summary === "string" && result.summary ? (<p>{result.summary}</p>) : null}
                {order ? (<p>
                    Order {String(order.id)} · {String(order.product_name)} ×{" "}
                    {String(order.quantity)} ·{" "}
                    {formatPrice(Number(order.total_price))}
                  </p>) : null}
                {product ? (<p>
                    Listing published: {String(product.name)} ·{" "}
                    {formatPrice(Number(product.price))}
                  </p>) : null}
                {typeof result.note === "string" && result.note ? (<p className="text-amber-700">{result.note}</p>) : null}
                {typeof result.message === "string" && result.message ? (<p className="text-red-600">{result.message}</p>) : null}
              </div>);
            })}
        </div>) : null}

      {awaiting ? (<div className="mt-3 rounded-xl border border-amber-200 bg-amber-50/70 p-3">
          <p className="flex items-center gap-1.5 text-[11px] font-semibold text-amber-800">
            <ShieldAlert className="h-3.5 w-3.5"/>
            Write operation awaiting confirmation
          </p>

          {sellerDraft ? (<div className="mt-1.5 text-[11px] leading-relaxed text-ink-soft">
              <p className="font-semibold text-ink">
                {String(sellerDraft.name)}
              </p>
              <p className="mt-1">
                {String(draft?.category)} · {formatPrice(Number(draft?.price))}
              </p>
            </div>) : (<div className="mt-1.5 text-[11px] leading-relaxed text-ink-soft">
              <p className="font-semibold text-ink">
                {String(draft?.product_name)}
              </p>
              <p className="mt-1">
                Quantity {String(draft?.quantity)} · Total{" "}
                {formatPrice(Number(draft?.total))}
              </p>
              {typeof draft?.note === "string" ? (<p className="mt-1 text-amber-700">{draft.note}</p>) : null}
            </div>)}

          <button type="button" onClick={onConfirm} disabled={confirming} className="mt-2 flex w-full items-center justify-center gap-2 rounded-lg bg-ink py-2 text-xs font-semibold text-white transition hover:bg-ink/90 disabled:cursor-not-allowed disabled:opacity-60">
            {confirming ? (<Loader2 className="h-3.5 w-3.5 animate-spin"/>) : (<CheckCircle2 className="h-3.5 w-3.5"/>)}
            {confirming ? "Executing…" : "Confirm and run"}
          </button>
        </div>) : null}

      {task.status === "completed" ? (<p className="mt-2 flex items-center gap-1 text-[10px] text-brand">
          <CheckCircle2 className="h-3 w-3"/>
          Task completed
        </p>) : null}
    </div>);
}
