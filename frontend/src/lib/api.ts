import type { ChatResponse, Order, Review, SellerProductCreated, SessionDetail, SessionSummary, } from "./types";
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";
export class ApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}
async function request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await fetch(`${BASE_URL}${path}`, {
        ...init,
        headers: {
            "Content-Type": "application/json",
            ...(init?.headers ?? {}),
        },
    });
    if (!response.ok) {
        let message = `Request failed (${response.status})`;
        try {
            const data = (await response.json()) as {
                detail?: string;
            };
            if (data.detail)
                message = data.detail;
        }
        catch {
        }
        throw new ApiError(message, response.status);
    }
    return (await response.json()) as T;
}
export type StreamEvent = {
    event: string;
    data: Record<string, unknown>;
};
function parseSseBlock(block: string): StreamEvent | null {
    let event = "message";
    const dataLines: string[] = [];
    for (const rawLine of block.split("\n")) {
        const line = rawLine.replace(/\r$/, "");
        if (!line || line.startsWith(":"))
            continue;
        const separator = line.indexOf(":");
        const field = separator === -1 ? line : line.slice(0, separator);
        let value = separator === -1 ? "" : line.slice(separator + 1);
        if (value.startsWith(" "))
            value = value.slice(1);
        if (field === "event")
            event = value;
        else if (field === "data")
            dataLines.push(value);
    }
    if (!dataLines.length)
        return null;
    try {
        return {
            event,
            data: JSON.parse(dataLines.join("\n")) as Record<string, unknown>,
        };
    }
    catch {
        return null;
    }
}
export const api = {
    chat(payload: {
        message: string;
        session_id?: string | null;
        user_id: string;
    }) {
        return request<ChatResponse>("/chat", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },
    sessions(userId: string) {
        return request<SessionSummary[]>(`/sessions?user_id=${encodeURIComponent(userId)}`);
    },
    session(sessionId: string, userId: string) {
        return request<SessionDetail>(`/sessions/${sessionId}?user_id=${encodeURIComponent(userId)}`);
    },
    createOrder(payload: {
        product_id: string;
        quantity: number;
        address: string;
        session_id?: string | null;
        user_id: string;
        confirm: boolean;
    }) {
        return request<Order>("/orders", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },
    orders(userId: string) {
        return request<Order[]>(`/orders?user_id=${encodeURIComponent(userId)}`);
    },
    order(orderId: string, userId: string) {
        return request<Order>(`/orders/${encodeURIComponent(orderId)}?user_id=${encodeURIComponent(userId)}`);
    },
    reviews(productId: string, limit = 20) {
        return request<Review[]>(`/products/${encodeURIComponent(productId)}/reviews?limit=${limit}`);
    },
    orderReview(orderId: string, userId: string) {
        return request<Review>(`/orders/${encodeURIComponent(orderId)}/review?user_id=${encodeURIComponent(userId)}`);
    },
    createReview(payload: {
        order_id: string;
        rating: number;
        content: string;
        author?: string;
        user_id: string;
    }) {
        return request<Review & {
            degraded: boolean;
        }>("/reviews", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },
    updateReview(reviewId: number, payload: {
        rating: number;
        content: string;
        author?: string;
        user_id: string;
    }) {
        return request<Review & {
            degraded: boolean;
        }>(`/reviews/${reviewId}`, {
            method: "PUT",
            body: JSON.stringify(payload),
        });
    },
    categories() {
        return request<string[]>("/products/categories");
    },
    createSellerProduct(payload: {
        description: string;
        price: number;
        category: string;
        brand?: string;
        seller_id: string;
    }) {
        return request<SellerProductCreated>("/seller/products", {
            method: "POST",
            body: JSON.stringify(payload),
        });
    },
    async chatStream(payload: {
        message: string;
        session_id?: string | null;
        user_id: string;
    }, onEvent: (event: StreamEvent) => void, signal?: AbortSignal) {
        const response = await fetch(`${BASE_URL}/chat/stream`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
            signal,
        });
        if (!response.ok) {
            let message = `Request failed (${response.status})`;
            try {
                const data = (await response.json()) as {
                    detail?: string;
                };
                if (data.detail)
                    message = data.detail;
            }
            catch {
            }
            throw new ApiError(message, response.status);
        }
        if (!response.body) {
            throw new ApiError("This browser does not support streaming responses", 0);
        }
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done)
                break;
            buffer += decoder.decode(value, { stream: true });
            buffer = buffer.replace(/\r\n/g, "\n");
            let boundary = buffer.indexOf("\n\n");
            while (boundary !== -1) {
                const block = buffer.slice(0, boundary);
                buffer = buffer.slice(boundary + 2);
                const parsed = parseSseBlock(block);
                if (parsed)
                    onEvent(parsed);
                boundary = buffer.indexOf("\n\n");
            }
        }
        buffer += decoder.decode();
        buffer = buffer.replace(/\r\n/g, "\n");
        const parsed = parseSseBlock(buffer);
        if (parsed)
            onEvent(parsed);
    },
};
