"use client";
import { ArrowRight, Package, PlugZap, Sparkles, Store } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { ChatMessage } from "@/components/chat-message";
import { Composer } from "@/components/composer";
import { McpToolsModal } from "@/components/mcp-tools-modal";
import { OrderModal } from "@/components/order-modal";
import { OrdersModal } from "@/components/orders-modal";
import { ProductModal } from "@/components/product-modal";
import { SellerModal } from "@/components/seller-modal";
import { Sidebar } from "@/components/sidebar";
import { api } from "@/lib/api";
import { buildHistoryResponse } from "@/lib/history";
import type { AgentTask, ChatResponse, MarketplaceResult, PurchaseProposal, ScoredProduct, SessionSummary, ShoppingIntent, StreamStage, UiMessage, } from "@/lib/types";
const USER_ID = "demo-user";
const DEMO_PROMPTS = [
    "我想买一瓶沐浴露，预算 100 以内，敏感肌，最好没有香味",
    "油头，想要控油蓬松的洗发水，评分 4.5 以上",
    "给敏感肌找一款 150 元以内的修护面霜",
    "帮我比价京东和淘宝 100 元以内的护肤霜，推荐三款性价比最高的",
];
function taskResultText(task: AgentTask): string {
    const last = task.results[task.results.length - 1] as Record<string, unknown> | undefined;
    if (!last)
        return task.plan.summary || "Task completed";
    const order = last.order as Record<string, unknown> | undefined;
    if (order) {
        return `Order ${String(order.id)} created: ${String(order.product_name)} × ${String(order.quantity)}`;
    }
    const product = last.product as Record<string, unknown> | undefined;
    if (product)
        return `Listing published: ${String(product.name)}`;
    return typeof last.summary === "string"
        ? last.summary
        : task.plan.summary || "Task completed";
}
function Hero({ onPrompt }: {
    onPrompt: (text: string) => void;
}) {
    return (<div className="flex min-h-[62vh] flex-col justify-center py-6">
      <div className="inline-flex w-fit items-center gap-2 rounded-full border border-brand/15 bg-brand-soft/70 px-3 py-1 text-[11px] font-semibold text-brand-dark">
        <Sparkles className="h-3 w-3"/>
        Agentic shopping · Explainable recommendations
      </div>

      <h1 className="mt-5 font-display text-4xl leading-[1.12] tracking-tight text-ink sm:text-5xl">
        Let an agent explain
        <br />
        what to buy
      </h1>
      <p className="mt-4 max-w-xl text-sm leading-relaxed text-ink-soft">
        Tell ShopWise the category, budget, skin type, or what matters most. It plans the task, searches products, summarizes reviews,
        and ranks them across multiple signals. Checkout happens only after you confirm. You can also ask it to compare JD and Taobao through MCP,
        bringing external prices and reviews into one view.
      </p>

      <div className="mt-7 grid gap-2 sm:grid-cols-2">
        {DEMO_PROMPTS.map((prompt) => (<button key={prompt} type="button" onClick={() => onPrompt(prompt)} className="group flex items-center justify-between gap-3 rounded-2xl border border-line bg-card px-4 py-3 text-left text-xs leading-relaxed text-ink-soft shadow-[0_2px_12px_rgba(23,33,29,0.03)] transition hover:-translate-y-0.5 hover:border-brand/30 hover:text-ink hover:shadow-[0_8px_24px_rgba(23,33,29,0.07)]">
            <span>{prompt}</span>
            <ArrowRight className="h-3.5 w-3.5 shrink-0 text-muted transition group-hover:translate-x-0.5 group-hover:text-brand"/>
          </button>))}
      </div>

      <div className="mt-7 flex flex-wrap items-center gap-x-4 gap-y-1 text-[11px] text-muted">
        <span>Price</span>
        <span className="h-1 w-1 rounded-full bg-line"/>
        <span>Rating</span>
        <span className="h-1 w-1 rounded-full bg-line"/>
        <span>Reviews</span>
        <span className="h-1 w-1 rounded-full bg-line"/>
        <span>Preference match</span>
        <span className="ml-auto">Demo catalog · Simulated checkout</span>
      </div>
    </div>);
}
export default function HomePage() {
    const [messages, setMessages] = useState<UiMessage[]>([]);
    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [sessionId, setSessionId] = useState<string | null>(null);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selected, setSelected] = useState<ScoredProduct | null>(null);
    const [orderItem, setOrderItem] = useState<ScoredProduct | null>(null);
    const [toast, setToast] = useState<string | null>(null);
    const [ordersOpen, setOrdersOpen] = useState(false);
    const [ordersVersion, setOrdersVersion] = useState(0);
    const [sellerVersion, setSellerVersion] = useState(0);
    const [sellerOpen, setSellerOpen] = useState(false);
    const [mcpOpen, setMcpOpen] = useState(false);
    const [confirmingTaskId, setConfirmingTaskId] = useState<string | null>(null);
    const bottomRef = useRef<HTMLDivElement>(null);
    const streamAbortRef = useRef<AbortController | null>(null);
    const refreshSessions = useCallback(async () => {
        try {
            const data = await api.sessions(USER_ID);
            setSessions(data);
        }
        catch {
        }
    }, []);
    useEffect(() => {
        void refreshSessions();
    }, [refreshSessions]);
    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    }, [messages, loading]);
    useEffect(() => {
        if (!toast)
            return;
        const timer = window.setTimeout(() => setToast(null), 3500);
        return () => window.clearTimeout(timer);
    }, [toast]);
    async function sendMessage(raw: string) {
        const text = raw.trim();
        if (!text || loading)
            return;
        const userMessage: UiMessage = {
            id: crypto.randomUUID(),
            role: "user",
            content: text,
        };
        const pendingId = crypto.randomUUID();
        setMessages((current) => [
            ...current,
            userMessage,
            {
                id: pendingId,
                role: "assistant",
                content: "",
                pending: true,
                stage: "parse_intent",
            },
        ]);
        setInput("");
        setError(null);
        setLoading(true);
        const controller = new AbortController();
        streamAbortRef.current = controller;
        const partial: ChatResponse = {
            session_id: "",
            provider: "unknown",
            intent: null,
            products: [],
            recommendation: "",
            top_product_id: null,
            purchase_proposal: null,
            clarification: null,
            degraded: false,
        };
        const patchPending = (updater: (message: UiMessage) => UiMessage) => {
            setMessages((current) => current.map((message) => message.id === pendingId ? updater(message) : message));
        };
        try {
            await api.chatStream({ message: text, session_id: sessionId, user_id: USER_ID }, ({ event, data }) => {
                if (event === "session") {
                    if (typeof data.session_id === "string") {
                        partial.session_id = data.session_id;
                        setSessionId(data.session_id);
                    }
                    if (typeof data.provider === "string") {
                        partial.provider = data.provider;
                    }
                    patchPending((message) => ({
                        ...message,
                        response: { ...partial },
                    }));
                    return;
                }
                if (event === "plan") {
                    const plan = data.plan as AgentTask["plan"] | undefined;
                    if (plan) {
                        patchPending((message) => ({ ...message, plan }));
                    }
                    return;
                }
                if (event === "task") {
                    const task = data.task as AgentTask | undefined;
                    if (task) {
                        patchPending((message) => ({
                            ...message,
                            task,
                            content: task.plan.summary || message.content,
                        }));
                    }
                    return;
                }
                if (event === "marketplace") {
                    const marketplace = data as unknown as MarketplaceResult;
                    partial.provider =
                        typeof data.provider === "string"
                            ? data.provider
                            : partial.provider;
                    partial.recommendation = marketplace.recommendation;
                    patchPending((message) => ({
                        ...message,
                        marketplace,
                        content: marketplace.recommendation,
                        response: { ...partial },
                    }));
                    return;
                }
                if (event === "stage") {
                    const stage = data.stage as StreamStage | undefined;
                    const stageStatus = data.status === "done" ? ("done" as const) : ("active" as const);
                    if (stage) {
                        patchPending((message) => ({
                            ...message,
                            stage,
                            stageStatus,
                        }));
                    }
                    return;
                }
                if (event === "intent") {
                    partial.intent = (data.intent as ShoppingIntent | null) ?? null;
                    patchPending((message) => ({
                        ...message,
                        response: { ...partial },
                    }));
                    return;
                }
                if (event === "products") {
                    partial.products = (data.products as ScoredProduct[]) ?? [];
                    patchPending((message) => ({
                        ...message,
                        response: { ...partial },
                    }));
                    return;
                }
                if (event === "token") {
                    const token = typeof data.text === "string" ? data.text : "";
                    if (!token)
                        return;
                    partial.recommendation += token;
                    patchPending((message) => ({
                        ...message,
                        content: partial.recommendation,
                        response: { ...partial },
                    }));
                    return;
                }
                if (event === "recommendation") {
                    partial.provider =
                        typeof data.provider === "string" ? data.provider : partial.provider;
                    partial.recommendation =
                        typeof data.recommendation === "string"
                            ? data.recommendation
                            : partial.recommendation;
                    partial.top_product_id =
                        typeof data.top_product_id === "string"
                            ? data.top_product_id
                            : null;
                    partial.purchase_proposal =
                        (data.purchase_proposal as PurchaseProposal | null) ?? null;
                    partial.clarification =
                        typeof data.clarification === "string" ? data.clarification : null;
                    partial.degraded = Boolean(data.degraded);
                    patchPending((message) => ({
                        ...message,
                        content: partial.clarification || partial.recommendation,
                        response: { ...partial },
                    }));
                    return;
                }
                if (event === "done") {
                    patchPending((message) => ({
                        ...message,
                        pending: false,
                        stage: "done",
                        stageStatus: "done",
                    }));
                    setLoading(false);
                    void refreshSessions();
                    return;
                }
                if (event === "error") {
                    const detail = typeof data.message === "string" ? data.message : "Streaming request failed";
                    throw new Error(detail);
                }
            }, controller.signal);
        }
        catch (err) {
            if (controller.signal.aborted)
                return;
            const message = err instanceof Error ? err.message : "Request failed. Make sure the backend is running.";
            setError(message);
            patchPending((item) => ({
                ...item,
                pending: false,
                stage: "done",
                stageStatus: "done",
                content: item.response?.recommendation ||
                    item.response?.clarification ||
                    "Sorry, the request did not complete. Make sure the backend is running at localhost:8000 and try again.",
            }));
        }
        finally {
            if (streamAbortRef.current === controller) {
                streamAbortRef.current = null;
                setLoading(false);
            }
            patchPending((message) => message.pending
                ? { ...message, pending: false, stage: "done", stageStatus: "done" }
                : message);
        }
    }
    async function confirmTask(messageId: string, taskId: string) {
        setConfirmingTaskId(taskId);
        setError(null);
        try {
            const task = await api.confirmAgentTask(taskId, USER_ID);
            setMessages((current) => current.map((message) => message.id === messageId
                ? { ...message, task, content: taskResultText(task) }
                : message));
            if (task.status === "completed") {
                setToast("Task completed");
                setOrdersVersion((value) => value + 1);
                setSellerVersion((value) => value + 1);
            }
            else {
                const last = task.results[task.results.length - 1] as Record<string, unknown> | undefined;
                setError(typeof last?.message === "string" ? last.message : "Task failed");
            }
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Task failed");
        }
        finally {
            setConfirmingTaskId(null);
        }
    }
    async function loadSession(id: string) {
        if (loading)
            return;
        setLoading(true);
        setError(null);
        try {
            const detail = await api.session(id, USER_ID);
            setSessionId(detail.id);
            setMessages(detail.messages.map((message) => ({
                id: `db-${message.id}`,
                role: message.role,
                content: message.content,
                response: buildHistoryResponse(message, detail.id),
                task: message.meta?.task
                    ? (message.meta.task as AgentTask)
                    : undefined,
                marketplace: message.meta?.marketplace
                    ? (message.meta.marketplace as MarketplaceResult)
                    : undefined,
            })));
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load session");
        }
        finally {
            setLoading(false);
        }
    }
    function newChat() {
        streamAbortRef.current?.abort();
        streamAbortRef.current = null;
        setMessages([]);
        setSessionId(null);
        setError(null);
        setInput("");
        setLoading(false);
    }
    return (<div className="flex h-screen overflow-hidden">
      <Sidebar sessions={sessions} activeSessionId={sessionId} onNew={newChat} onSelect={loadSession}/>

      <main className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 shrink-0 items-center justify-between border-b border-line/70 bg-paper/80 px-4 backdrop-blur md:px-8">
          <div className="flex items-center gap-2 md:hidden">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand text-white">
              <Sparkles className="h-3.5 w-3.5"/>
            </span>
            <span className="font-display text-base font-semibold">ShopWise</span>
          </div>
          <p className="hidden text-xs text-muted md:block">
            Shopping decisions · Full agent flow from request to checkout
          </p>
          <div className="flex items-center gap-2">
            <span className="rounded-full border border-line bg-card px-2.5 py-1 text-[10px] font-medium text-muted">
              Demo catalog
            </span>
            <span className="hidden rounded-full border border-brand/15 bg-brand-soft/70 px-2.5 py-1 text-[10px] font-medium text-brand-dark sm:inline">
              Simulated checkout
            </span>
            <button type="button" onClick={() => setMcpOpen(true)} className="flex items-center gap-1 rounded-full border border-line bg-card px-2.5 py-1 text-[10px] font-medium text-ink-soft transition hover:border-brand/30 hover:text-brand">
              <PlugZap className="h-3 w-3"/>
              MCP
            </button>
            <button type="button" onClick={() => setSellerOpen(true)} className="flex items-center gap-1 rounded-full border border-brand/20 bg-brand-soft/70 px-2.5 py-1 text-[10px] font-medium text-brand-dark transition hover:bg-brand-soft">
              <Store className="h-3 w-3"/>
              Sell
            </button>
            <button type="button" onClick={() => setOrdersOpen(true)} className="flex items-center gap-1 rounded-full border border-line bg-card px-2.5 py-1 text-[10px] font-medium text-ink-soft transition hover:border-brand/30 hover:text-brand">
              <Package className="h-3 w-3"/>
              Orders
            </button>
            <button type="button" onClick={newChat} className="rounded-full border border-line bg-card px-2.5 py-1 text-[10px] font-medium text-ink-soft transition hover:border-brand/30 hover:text-brand md:hidden">
              New chat
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="mx-auto w-full max-w-4xl px-4 py-6 md:px-8">
            {messages.length === 0 ? (<Hero onPrompt={sendMessage}/>) : (<div className="space-y-7 pb-4">
                {messages.map((message) => (<ChatMessage key={message.id} message={message} onProductOpen={setSelected} onConfirmTask={confirmTask} confirmingTaskId={confirmingTaskId}/>))}
              </div>)}
            <div ref={bottomRef}/>
          </div>
        </div>

        <div className="shrink-0 border-t border-line/60 bg-paper/85 px-4 pb-4 pt-3 backdrop-blur md:px-8">
          <div className="mx-auto max-w-4xl">
            {error ? (<p className="mb-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-xs text-red-700">
                {error}
              </p>) : null}
            <Composer value={input} onChange={setInput} onSend={() => void sendMessage(input)} disabled={loading}/>
            <p className="mt-2 text-center text-[10px] text-muted">
              Demo data only, not purchase advice · Checkout is simulated; no real payment
            </p>
          </div>
        </div>
      </main>

      <ProductModal item={selected} onClose={() => setSelected(null)} onOrder={(item) => {
            setSelected(null);
            setOrderItem(item);
        }}/>
      <OrderModal item={orderItem} sessionId={sessionId} onClose={() => setOrderItem(null)} onSuccess={(order) => {
            setToast(`Demo order ${order.id} created`);
            setOrdersVersion((value) => value + 1);
        }}/>
      <OrdersModal open={ordersOpen} userId={USER_ID} version={ordersVersion} onClose={() => setOrdersOpen(false)}/>
      <SellerModal open={sellerOpen} sellerId={USER_ID} version={sellerVersion} onClose={() => setSellerOpen(false)}/>
      <McpToolsModal open={mcpOpen} onClose={() => setMcpOpen(false)}/>
      {toast ? (<div className="fixed bottom-24 left-1/2 z-[70] -translate-x-1/2 rounded-full bg-ink px-4 py-2 text-xs font-medium text-white shadow-xl">
          {toast}
        </div>) : null}
    </div>);
}
