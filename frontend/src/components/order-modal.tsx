"use client";
import { CheckCircle2, Loader2, Minus, Plus, X } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Order, ScoredProduct } from "@/lib/types";
import { formatPrice } from "@/lib/utils";
export function OrderModal({ item, sessionId, onClose, onSuccess, }: {
    item: ScoredProduct | null;
    sessionId: string | null;
    onClose: () => void;
    onSuccess?: (order: Order) => void;
}) {
    const [address, setAddress] = useState("1 Demo Road, Shanghai");
    const [quantity, setQuantity] = useState(1);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [order, setOrder] = useState<Order | null>(null);
    if (!item)
        return null;
    const { product } = item;
    const total = product.price * quantity;
    async function submit() {
        if (address.trim().length < 5) {
            setError("Please enter an address with at least 5 characters");
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            const created = await api.createOrder({
                product_id: product.id,
                quantity,
                address: address.trim(),
                session_id: sessionId,
                user_id: "demo-user",
                confirm: true,
            });
            setOrder(created);
            onSuccess?.(created);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Order failed. Please try again.");
        }
        finally {
            setSubmitting(false);
        }
    }
    return (<div className="fixed inset-0 z-[60] flex items-end justify-center bg-ink/45 backdrop-blur-sm sm:items-center sm:p-6" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="w-full max-w-md rounded-t-3xl bg-card p-6 shadow-2xl sm:rounded-3xl" onClick={(event) => event.stopPropagation()}>
        {order ? (<div className="py-4 text-center">
            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-brand-soft">
              <CheckCircle2 className="h-7 w-7 text-brand"/>
            </div>
            <h2 className="mt-4 text-lg font-bold text-ink">Demo order created</h2>
            <p className="mt-1 text-sm text-muted">Order ID {order.id}</p>
            <div className="mt-4 rounded-xl bg-paper p-4 text-left text-sm">
              <div className="flex justify-between">
                <span className="text-muted">Product</span>
                <span className="font-medium text-ink">{order.product_name}</span>
              </div>
              <div className="mt-2 flex justify-between">
                <span className="text-muted">Quantity</span>
                <span className="font-medium text-ink">{order.quantity}</span>
              </div>
              <div className="mt-2 flex justify-between">
                <span className="text-muted">Total</span>
                <span className="font-semibold text-brand">
                  {formatPrice(order.total_price)}
                </span>
              </div>
            </div>
            <p className="mt-3 text-[11px] text-muted">
              This is a demo order. No real payment or shipping.
            </p>
            <button type="button" onClick={onClose} className="mt-5 w-full rounded-xl bg-brand py-2.5 text-sm font-semibold text-white hover:bg-brand-dark">
              Done
            </button>
          </div>) : (<>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                  Confirm order
                </p>
                <h2 className="mt-1 text-lg font-bold text-ink">{product.name}</h2>
              </div>
              <button type="button" onClick={onClose} className="rounded-full p-1.5 text-muted hover:bg-paper" aria-label="Close">
                <X className="h-4 w-4"/>
              </button>
            </div>

            <div className="mt-4 rounded-xl bg-paper p-4">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted">Unit price</span>
                <span className="font-medium text-ink">{formatPrice(product.price)}</span>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-muted">Quantity</span>
                <div className="flex items-center gap-2">
                  <button type="button" onClick={() => setQuantity((value) => Math.max(1, value - 1))} className="rounded-lg border border-line bg-card p-1 hover:bg-brand-soft" aria-label="Decrease quantity">
                    <Minus className="h-3.5 w-3.5"/>
                  </button>
                  <span className="w-6 text-center font-semibold">{quantity}</span>
                  <button type="button" onClick={() => setQuantity((value) => Math.min(5, value + 1))} className="rounded-lg border border-line bg-card p-1 hover:bg-brand-soft" aria-label="Increase quantity">
                    <Plus className="h-3.5 w-3.5"/>
                  </button>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between border-t border-line pt-3 text-sm">
                <span className="text-muted">Total</span>
                <span className="text-lg font-bold text-brand">{formatPrice(total)}</span>
              </div>
            </div>

            <label className="mt-4 block">
              <span className="text-xs font-medium text-ink-soft">Shipping address</span>
              <textarea value={address} onChange={(event) => setAddress(event.target.value)} rows={2} className="mt-1.5 w-full resize-none rounded-xl border border-line bg-paper/50 px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:bg-white" placeholder="Enter a demo address"/>
            </label>

            {error ? (<p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
                {error}
              </p>) : null}

            <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-[11px] leading-relaxed text-amber-800">
              Simulated checkout: no charge and no shipping. Prices come from server-side product data.
            </p>

            <button type="button" onClick={submit} disabled={submitting} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin"/> : null}
              {submitting ? "Creating…" : "Confirm demo order"}
            </button>
          </>)}
      </div>
    </div>);
}
