export type Product = {
    id: string;
    name: string;
    brand: string;
    category: string;
    price: number;
    original_price: number | null;
    rating: number;
    review_count: number;
    description: string;
    attributes: Record<string, unknown>;
    pros: string[];
    cons: string[];
    tags: string[];
    image_key: string;
    seller_id: string | null;
};
export type SellerProductCreated = {
    product: Product;
    degraded: boolean;
};
export type AgentPlanStep = {
    skill: string;
    args: Record<string, unknown>;
    risk: string;
    requires_confirmation: boolean;
};
export type AgentTask = {
    id: string;
    user_id: string;
    goal: string;
    status: string;
    risk: string;
    plan: {
        goal?: string;
        summary?: string;
        steps?: AgentPlanStep[];
    };
    results: Array<Record<string, unknown>>;
    draft: Record<string, unknown> | null;
    created_at: string;
    updated_at: string;
};
export type ScoredProduct = {
    product: Product;
    score: number;
    breakdown: Record<string, number>;
    reasons: string[];
    warnings: string[];
};
export type MarketplaceProduct = {
    id: string;
    platform: "jd" | "taobao" | string;
    platform_label: string;
    name: string;
    brand: string;
    category: string;
    price: number;
    original_price: number | null;
    rating: number;
    review_count: number;
    sales: number;
    description: string;
    tags: string[];
    pros: string[];
    cons: string[];
    image_key: string;
    url: string;
    value_score: number;
    reasons: string[];
};
export type MCPToolCall = {
    name: string;
    arguments: Record<string, unknown>;
    ok: boolean;
    duration_ms?: number;
    error?: string | null;
};
export type MarketplaceResult = {
    query: string;
    platforms: string[];
    budget_max: number | null;
    products: MarketplaceProduct[];
    recommendation: string;
    tool_calls: MCPToolCall[];
    note: string;
};
export type MCPToolInfo = {
    name: string;
    description: string;
    input_schema: {
        properties?: Record<string, unknown>;
        required?: string[];
        [key: string]: unknown;
    };
};
export type MCPToolsStatus = {
    enabled: boolean;
    available: boolean;
    transport?: string;
    server?: string;
    tools: MCPToolInfo[];
    error?: string | null;
};
export type ShoppingIntent = {
    category: string | null;
    query: string | null;
    budget_max: number | null;
    budget_min: number | null;
    min_rating: number | null;
    attributes: Record<string, unknown>;
    brands_include: string[];
    brands_exclude: string[];
    exclude_keywords: string[];
    priorities: string[];
    needs_clarification: boolean;
    clarification_question: string | null;
    confidence: number;
};
export type PurchaseProposal = {
    product_id: string;
    product_name: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    currency: string;
};
export type ChatResponse = {
    session_id: string;
    provider: string;
    intent: ShoppingIntent | null;
    products: ScoredProduct[];
    recommendation: string;
    top_product_id: string | null;
    purchase_proposal: PurchaseProposal | null;
    clarification: string | null;
    degraded: boolean;
};
export type ChatMessage = {
    id: number;
    role: "user" | "assistant";
    content: string;
    meta: Record<string, unknown>;
    created_at: string;
};
export type SessionSummary = {
    id: string;
    user_id: string;
    title: string;
    profile: Record<string, unknown>;
    created_at: string;
    updated_at: string;
    messages: ChatMessage[];
};
export type SessionDetail = SessionSummary;
export type Order = {
    id: string;
    user_id: string;
    session_id: string | null;
    product_id: string;
    product_name: string;
    quantity: number;
    unit_price: number;
    total_price: number;
    status: string;
    address: string;
    created_at: string;
    reviewed: boolean;
};
export type Review = {
    id: number;
    product_id: string;
    order_id: string | null;
    rating: number;
    content: string;
    author: string;
    sentiment: "positive" | "neutral" | "negative" | string;
    summary: string;
    pros: string[];
    cons: string[];
    tags: string[];
    created_at: string;
    updated_at: string;
};
export type StreamStage = "parse_intent" | "search" | "analyze" | "rank" | "recommend" | "done";
export type StreamStageStatus = "active" | "done";
export type UiMessage = {
    id: string;
    role: "user" | "assistant";
    content: string;
    response?: ChatResponse;
    pending?: boolean;
    stage?: StreamStage;
    stageStatus?: StreamStageStatus;
    plan?: AgentTask["plan"];
    task?: AgentTask;
    marketplace?: MarketplaceResult;
};
