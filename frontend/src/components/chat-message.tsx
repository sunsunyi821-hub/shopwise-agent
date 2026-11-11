"use client";
import { AlertTriangle, MessageCircleQuestion, Sparkles } from "lucide-react";
import { AgentTrace } from "@/components/agent-trace";
import { ChatTaskCard } from "@/components/chat-task-card";
import { MarketplaceCard } from "@/components/marketplace-card";
import { Markdown } from "@/components/markdown";
import { ProductGrid } from "@/components/product-card";
import type { ScoredProduct, UiMessage } from "@/lib/types";
function providerLabel(provider?: string) {
    if (provider === "mock")
        return "Mock demo";
    if (provider === "anthropic")
        return "Claude";
    if (provider === "openai")
        return "OpenAI-compatible";
    return provider ?? "Agent";
}
export function ChatMessage({ message, onProductOpen, onConfirmTask, confirmingTaskId, }: {
    message: UiMessage;
    onProductOpen: (item: ScoredProduct) => void;
    onConfirmTask: (messageId: string, taskId: string) => void;
    confirmingTaskId?: string | null;
}) {
    if (message.role === "user") {
        return (<div className="flex animate-fade-up justify-end">
        <div className="max-w-[82%] rounded-2xl rounded-br-md bg-brand px-4 py-2.5 text-sm leading-relaxed text-white shadow-sm">
          {message.content}
        </div>
      </div>);
    }
    const response = message.response;
    return (<div className="flex animate-fade-up gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-brand-soft text-brand">
        <Sparkles className="h-4 w-4"/>
      </div>

      <div className="min-w-0 flex-1 space-y-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-ink">ShopWise</span>
          <span className="rounded-full bg-paper px-2 py-0.5 text-[10px] font-medium text-muted">
            {providerLabel(response?.provider)}
          </span>
          {response?.degraded ? (<span className="flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700">
              <AlertTriangle className="h-3 w-3"/>
              Fell back to rule-based recommendation
            </span>) : null}
        </div>

        {!message.marketplace && (response || message.pending) ? (<AgentTrace intent={response?.intent} products={response?.products} provider={response?.provider} loading={message.pending} stage={message.stage} stageStatus={message.stageStatus}/>) : null}

        {message.marketplace ? (<MarketplaceCard result={message.marketplace}/>) : null}

        {response?.clarification ? (<div className="flex gap-3 rounded-2xl border border-accent/20 bg-accent-soft/60 p-4">
            <MessageCircleQuestion className="mt-0.5 h-4 w-4 shrink-0 text-accent"/>
            <div>
              <p className="text-xs font-semibold text-ink">Need a bit more information</p>
              <p className="mt-1 text-sm leading-relaxed text-ink-soft">
                {response.clarification}
              </p>
            </div>
          </div>) : null}

        {response?.recommendation ? (<div className="rounded-2xl border border-line bg-card p-5 shadow-[0_2px_14px_rgba(23,33,29,0.04)]">
            <Markdown>{response.recommendation}</Markdown>
          </div>) : null}

        {response?.products?.length ? (<div className="rounded-2xl border border-line bg-card/70 p-3">
            <div className="mb-2 flex items-center justify-between px-1">
              <p className="text-[11px] font-semibold uppercase tracking-wide text-muted">
                Candidates · ranked by overall match
              </p>
              <span className="text-[10px] text-muted">
                Open a card to see the score breakdown
              </span>
            </div>
            <ProductGrid items={response.products} onOpen={onProductOpen}/>
          </div>) : null}

        {message.task ? (<ChatTaskCard task={message.task} confirming={confirmingTaskId === message.task.id} onConfirm={() => onConfirmTask(message.id, message.task!.id)}/>) : null}

        {message.pending &&
            !response?.clarification &&
            !response?.recommendation &&
            !response?.products?.length ? (<div className="rounded-2xl border border-line bg-card p-4">
            <div className="skeleton h-3 w-2/3 rounded-full"/>
            <div className="skeleton mt-2 h-3 w-5/6 rounded-full"/>
            <div className="skeleton mt-2 h-3 w-1/2 rounded-full"/>
          </div>) : null}

        {!response && !message.pending && message.content ? (<div className="rounded-2xl border border-line bg-card p-5">
            <Markdown>{message.content}</Markdown>
          </div>) : null}
      </div>
    </div>);
}
