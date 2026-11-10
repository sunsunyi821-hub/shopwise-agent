"use client";
import { ArrowLeft, Loader2, Package, Star, X } from "lucide-react";
import { useEffect, useState } from "react";
import { ReviewModal, ReviewStars, SentimentBadge, } from "@/components/review-modal";
import { api } from "@/lib/api";
import type { Order, Review } from "@/lib/types";
import { formatPrice } from "@/lib/utils";
const STATUS_LABELS: Record<string, string> = {
    confirmed: "Confirmed",
    paid: "Paid",
    shipped: "Shipped",
    completed: "Completed",
    cancelled: "Cancelled",
};
function statusLabel(status: string) {
    return STATUS_LABELS[status] ?? status;
}
function formatTime(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime()))
        return value;
    return date.toLocaleString("zh-CN", { hour12: false });
}
export function OrdersModal({ open, userId, version, onClose, }: {
    open: boolean;
    userId: string;
    version: number;
    onClose: () => void;
}) {
    const [orders, setOrders] = useState<Order[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selected, setSelected] = useState<Order | null>(null);
    const [detailLoading, setDetailLoading] = useState(false);
    const [selectedReview, setSelectedReview] = useState<Review | null>(null);
    const [reviewLoading, setReviewLoading] = useState(false);
    const [reviewing, setReviewing] = useState<Order | null>(null);
    useEffect(() => {
        if (!open) {
            setSelected(null);
            setSelectedReview(null);
            setReviewLoading(false);
            setReviewing(null);
            return;
        }
        let active = true;
        setLoading(true);
        setError(null);
        api
            .orders(userId)
            .then((data) => {
            if (active)
                setOrders(data);
        })
            .catch((err: unknown) => {
            if (active) {
                setError(err instanceof Error ? err.message : "Failed to load orders");
            }
        })
            .finally(() => {
            if (active)
                setLoading(false);
        });
        return () => {
            active = false;
        };
    }, [open, userId, version]);
    async function openDetail(order: Order) {
        setSelected(order);
        setSelectedReview(null);
        setReviewLoading(order.reviewed);
        setDetailLoading(true);
        setError(null);
        try {
            const detail = await api.order(order.id, userId);
            setSelected(detail);
            if (detail.reviewed) {
                try {
                    setSelectedReview(await api.orderReview(detail.id, userId));
                }
                catch {
                    setSelectedReview(null);
                }
            }
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load order details");
        }
        finally {
            setDetailLoading(false);
            setReviewLoading(false);
        }
    }
    function handleReviewSaved(saved: Review) {
        const orderId = saved.order_id;
        if (orderId) {
            setOrders((current) => current.map((order) => order.id === orderId ? { ...order, reviewed: true } : order));
            setSelected((current) => current && current.id === orderId
                ? { ...current, reviewed: true }
                : current);
        }
        setSelectedReview(saved);
    }
    async function openReviewEditor(order: Order) {
        if (!order.reviewed) {
            setReviewing(order);
            return;
        }
        if (selectedReview) {
            setReviewing(order);
            return;
        }
        setReviewLoading(true);
        setError(null);
        try {
            setSelectedReview(await api.orderReview(order.id, userId));
            setReviewing(order);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to load review");
        }
        finally {
            setReviewLoading(false);
        }
    }
    if (!open)
        return null;
    return (<>
      <div className="fixed inset-0 z-[60] flex items-end justify-center bg-ink/45 backdrop-blur-sm sm:items-center sm:p-6" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="flex max-h-[88vh] w-full max-w-lg flex-col rounded-t-3xl bg-card shadow-2xl sm:rounded-3xl" onClick={(event) => event.stopPropagation()}>
        <div className="flex items-center justify-between border-b border-line/70 px-5 py-4">
          <div className="flex items-center gap-2">
            {selected ? (<button type="button" onClick={() => {
                setSelected(null);
                setSelectedReview(null);
                setReviewLoading(false);
            }} className="rounded-full p-1.5 text-muted transition hover:bg-paper" aria-label="Back to orders">
                <ArrowLeft className="h-4 w-4"/>
              </button>) : null}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                {selected ? "Order details" : "My orders"}
              </p>
              <h2 className="mt-0.5 text-lg font-bold text-ink">
                {selected ? selected.id : `${orders.length} demo orders`}
              </h2>
            </div>
          </div>
          <button type="button" onClick={onClose} className="rounded-full p-1.5 text-muted transition hover:bg-paper" aria-label="Close">
            <X className="h-4 w-4"/>
          </button>
        </div>

        <div className="scrollbar-thin flex-1 overflow-y-auto px-5 py-4">
          {error ? (<p className="mb-3 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
              {error}
            </p>) : null}

          {selected ? (<div>
              <div className="rounded-2xl border border-line bg-paper/60 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-sm font-semibold leading-relaxed text-ink">
                      {selected.product_name}
                    </p>
                    <p className="mt-1 text-[11px] text-muted">
                      Qty {selected.quantity} · Unit price{" "}
                      {formatPrice(selected.unit_price)}
                    </p>
                  </div>
                  <span className="shrink-0 rounded-full bg-brand-soft px-2 py-0.5 text-[10px] font-semibold text-brand-dark">
                    {statusLabel(selected.status)}
                  </span>
                </div>
                <div className="mt-3 flex items-baseline justify-between border-t border-line pt-3">
                  <span className="text-xs text-muted">Total</span>
                  <span className="text-xl font-bold text-brand">
                    {formatPrice(selected.total_price)}
                  </span>
                </div>
              </div>

              {detailLoading ? (<p className="mt-3 flex items-center gap-2 text-[11px] text-muted">
                  <Loader2 className="h-3 w-3 animate-spin"/>
                  Loading latest order status…
                </p>) : null}

              <dl className="mt-3 space-y-2 rounded-2xl border border-line px-4 py-3 text-xs">
                <div className="flex justify-between gap-4">
                  <dt className="text-muted">Order ID</dt>
                  <dd className="text-right font-medium text-ink">
                    {selected.id}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted">Ordered at</dt>
                  <dd className="text-right text-ink-soft">
                    {formatTime(selected.created_at)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-muted">Shipping address</dt>
                  <dd className="text-right text-ink-soft">{selected.address}</dd>
                </div>
              </dl>

              <p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-[11px] leading-relaxed text-amber-800">
                This is a demo order. No real payment or shipping.
              </p>

              {selected.reviewed ? (<div className="mt-3 rounded-2xl border border-line bg-card p-4">
                  {reviewLoading ? (<p className="flex items-center gap-2 text-[11px] text-muted">
                      <Loader2 className="h-3 w-3 animate-spin"/>
                      Loading your review…
                    </p>) : selectedReview ? (<>
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex min-w-0 items-center gap-2">
                          <ReviewStars value={selectedReview.rating}/>
                          <span className="truncate text-[11px] text-muted">
                            {selectedReview.author}
                          </span>
                        </div>
                        <SentimentBadge sentiment={selectedReview.sentiment}/>
                      </div>
                      <p className="mt-2 text-xs leading-relaxed text-ink-soft">
                        {selectedReview.summary || selectedReview.content}
                      </p>
                      {selectedReview.tags.length ? (<div className="mt-2 flex flex-wrap gap-1">
                          {selectedReview.tags.map((tag) => (<span key={tag} className="rounded-full border border-line bg-paper px-2 py-0.5 text-[10px] text-muted">
                              {tag}
                            </span>))}
                        </div>) : null}
                      <p className="mt-2 text-[10px] text-muted">
                        Last updated: {formatTime(selectedReview.updated_at)}
                      </p>
                    </>) : (<p className="text-xs text-muted">
                      Could not load the review. You can try editing it.
                    </p>)}
                </div>) : null}

              <div className="mt-4 flex items-center gap-2">
                <button type="button" onClick={() => void openReviewEditor(selected)} className="flex flex-1 items-center justify-center gap-1 rounded-xl border border-brand/20 bg-brand-soft py-2.5 text-xs font-semibold text-brand-dark transition hover:bg-brand-soft/70">
                  <Star className="h-3.5 w-3.5"/>
                  {selected.reviewed ? "Edit review" : "Write a review"}
                </button>
                <button type="button" onClick={onClose} className="flex-1 rounded-xl bg-brand py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark">
                  Close
                </button>
              </div>
            </div>) : loading ? (<div className="flex items-center justify-center py-12 text-sm text-muted">
              <Loader2 className="mr-2 h-4 w-4 animate-spin"/>
              Loading orders…
            </div>) : orders.length === 0 ? (<div className="py-10 text-center">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-paper">
                <Package className="h-6 w-6 text-muted"/>
              </div>
              <p className="mt-3 text-sm font-medium text-ink">No orders yet</p>
              <p className="mt-1 text-xs leading-relaxed text-muted">
                Place a demo order from a product card and it will appear here.
              </p>
            </div>) : (<div className="space-y-2">
              {orders.map((order) => (<button key={order.id} type="button" onClick={() => void openDetail(order)} className="w-full rounded-2xl border border-line bg-card p-4 text-left transition hover:border-brand/30 hover:shadow-[0_8px_24px_rgba(23,33,29,0.06)]">
                  <div className="flex items-center justify-between gap-3">
                    <span className="truncate text-sm font-semibold text-ink">
                      {order.product_name}
                    </span>
                    <span className="shrink-0 text-sm font-bold text-brand">
                      {formatPrice(order.total_price)}
                    </span>
                  </div>
                  <div className="mt-1.5 flex items-center justify-between gap-3 text-[11px] text-muted">
                    <span className="truncate">{order.id}</span>
                    <span className="shrink-0">
                      {formatTime(order.created_at)}
                    </span>
                  </div>
                  <div className="mt-2 flex items-center gap-2 text-[11px] text-ink-soft">
                    <span className="rounded-full bg-paper px-2 py-0.5">
                      {statusLabel(order.status)}
                    </span>
                    <span>Qty {order.quantity}</span>
                    {order.reviewed ? (<span className="rounded-full bg-brand-soft px-2 py-0.5 text-brand-dark">
                        Reviewed
                      </span>) : null}
                  </div>
                </button>))}
            </div>)}
        </div>
        </div>
      </div>

      {reviewing ? (<ReviewModal order={reviewing} review={selectedReview} onClose={() => setReviewing(null)} onSubmitted={handleReviewSaved}/>) : null}
    </>);
}
