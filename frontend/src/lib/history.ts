import type { ChatMessage, ChatResponse, MarketplaceResult, PurchaseProposal, ScoredProduct, ShoppingIntent, } from "./types";
type StoredMeta = {
    provider?: string;
    intent?: ShoppingIntent | null;
    products?: ScoredProduct[];
    top_product_id?: string | null;
    purchase_proposal?: PurchaseProposal | null;
    recommendation?: string | null;
    clarification?: string | null;
    degraded?: boolean;
    marketplace?: MarketplaceResult;
};
export function buildHistoryResponse(message: ChatMessage, sessionId: string): ChatResponse | undefined {
    if (message.role !== "assistant")
        return undefined;
    const meta = (message.meta ?? {}) as StoredMeta;
    const products = Array.isArray(meta.products) ? meta.products : [];
    if (!meta.intent && products.length === 0 && !meta.marketplace)
        return undefined;
    const top = products.find((item) => item.product.id === meta.top_product_id)?.product ??
        products[0]?.product;
    const proposal = meta.purchase_proposal ??
        (top
            ? {
                product_id: top.id,
                product_name: top.name,
                quantity: 1,
                unit_price: top.price,
                total_price: top.price,
                currency: "CNY",
            }
            : null);
    const clarification = meta.clarification ?? null;
    return {
        session_id: sessionId,
        provider: meta.provider ?? "unknown",
        intent: meta.intent ?? null,
        products,
        recommendation: clarification
            ? ""
            : meta.recommendation || message.content,
        top_product_id: meta.top_product_id ?? top?.id ?? null,
        purchase_proposal: proposal,
        clarification,
        degraded: Boolean(meta.degraded),
    };
}
