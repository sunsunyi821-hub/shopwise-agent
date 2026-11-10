"use client";
import { AlertTriangle, Check, ShoppingBag, Star, X, } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Review, ScoredProduct } from "@/lib/types";
import { categoryEmoji, categoryGradient, cn, formatPrice, scorePercent, } from "@/lib/utils";
const BREAKDOWN_LABELS: Record<string, string> = {
    price: "Price",
    rating: "Rating",
    reviews: "Reviews",
    preference: "Preference",
    semantic: "Semantic",
};
const SENTIMENT_LABELS: Record<string, string> = {
    positive: "Positive",
    neutral: "Neutral",
    negative: "Negative",
};
function ReviewStars({ value }: {
    value: number;
}) {
    return (<span className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, index) => (<Star key={index} className={index < value
                ? "h-3 w-3 fill-amber-500 text-amber-500"
                : "h-3 w-3 text-muted/30"}/>))}
    </span>);
}
function SentimentBadge({ sentiment }: {
    sentiment: string;
}) {
    const tone = sentiment === "positive"
        ? "bg-brand-soft text-brand-dark"
        : sentiment === "negative"
            ? "bg-amber-50 text-amber-800"
            : "bg-paper text-muted";
    return (<span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium ${tone}`}>
      {SENTIMENT_LABELS[sentiment] ?? sentiment}
    </span>);
}
function ScoreBar({ label, value }: {
    label: string;
    value: number;
}) {
    return (<div>
      <div className="mb-1 flex items-center justify-between text-[11px]">
        <span className="text-muted">{label}</span>
        <span className="font-semibold text-ink">{Math.round(value * 100)}</span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-line/70">
        <div className="h-full rounded-full bg-brand transition-all" style={{ width: `${Math.max(4, Math.round(value * 100))}%` }}/>
      </div>
    </div>);
}
export function ProductModal({ item, onClose, onOrder, }: {
    item: ScoredProduct | null;
    onClose: () => void;
    onOrder: (item: ScoredProduct) => void;
}) {
    const [reviews, setReviews] = useState<Review[]>([]);
    const [reviewsLoading, setReviewsLoading] = useState(false);
    const productId = item?.product.id;
    useEffect(() => {
        if (!productId) {
            setReviews([]);
            return;
        }
        let active = true;
        setReviewsLoading(true);
        api
            .reviews(productId)
            .then((data) => {
            if (active)
                setReviews(data);
        })
            .catch(() => {
            if (active)
                setReviews([]);
        })
            .finally(() => {
            if (active)
                setReviewsLoading(false);
        });
        return () => {
            active = false;
        };
    }, [productId]);
    if (!item)
        return null;
    const { product } = item;
    return (<div className="fixed inset-0 z-50 flex items-end justify-center bg-ink/40 p-0 backdrop-blur-sm sm:items-center sm:p-6" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-t-3xl bg-card shadow-2xl sm:rounded-3xl" onClick={(event) => event.stopPropagation()}>
        <div className={cn("relative flex items-center gap-4 bg-gradient-to-br p-6 sm:p-8", categoryGradient(product.category))}>
          <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-white/70 text-4xl shadow-sm backdrop-blur">
            {categoryEmoji(product.category)}
          </div>
          <div className="min-w-0">
            <p className="text-xs font-medium text-ink-soft">{product.brand}</p>
            <h2 className="mt-1 text-xl font-bold leading-tight text-ink sm:text-2xl">
              {product.name}
            </h2>
            <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-ink-soft">
              <span className="rounded-full bg-white/70 px-2 py-0.5 font-semibold text-brand-dark">
                {scorePercent(item.score)}% match
              </span>
              <span className="flex items-center gap-1">
                <Star className="h-3 w-3 fill-amber-500 text-amber-500"/>
                {product.rating.toFixed(1)}
              </span>
              <span>{product.review_count} reviews</span>
            </div>
          </div>
          <button type="button" onClick={onClose} className="absolute right-4 top-4 rounded-full bg-white/70 p-2 text-ink-soft transition hover:bg-white" aria-label="Close">
            <X className="h-4 w-4"/>
          </button>
        </div>

        <div className="grid gap-6 p-6 sm:grid-cols-[1.15fr_0.85fr] sm:p-8">
          <div className="space-y-5">
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold tracking-tight text-brand">
                {formatPrice(product.price)}
              </span>
              {product.original_price && product.original_price > product.price ? (<span className="text-sm text-muted line-through">
                  {formatPrice(product.original_price)}
                </span>) : null}
            </div>

            <p className="text-sm leading-relaxed text-ink-soft">
              {product.description}
            </p>

            <div>
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
                Why this product
              </h3>
              <ul className="mt-2 space-y-1.5">
                {item.reasons.map((reason) => (<li key={reason} className="flex items-start gap-2 text-sm text-ink-soft">
                    <Check className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand"/>
                    <span>{reason}</span>
                  </li>))}
              </ul>
            </div>

            {item.warnings.length ? (<div className="rounded-xl border border-amber-200 bg-amber-50 p-3">
                <p className="flex items-center gap-1.5 text-xs font-semibold text-amber-800">
                  <AlertTriangle className="h-3.5 w-3.5"/>
                  Things to note
                </p>
                <ul className="mt-1.5 space-y-1">
                  {item.warnings.map((warning) => (<li key={warning} className="text-xs text-amber-800/90">
                      · {warning}
                    </li>))}
                </ul>
              </div>) : null}

            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl border border-line bg-paper/60 p-3">
                <p className="text-[11px] font-semibold text-brand">Pros</p>
                <ul className="mt-1 space-y-1 text-[11px] text-ink-soft">
                  {product.pros.map((pro) => (<li key={pro}>· {pro}</li>))}
                </ul>
              </div>
              <div className="rounded-xl border border-line bg-paper/60 p-3">
                <p className="text-[11px] font-semibold text-accent">Cons</p>
                <ul className="mt-1 space-y-1 text-[11px] text-ink-soft">
                  {product.cons.map((con) => (<li key={con}>· {con}</li>))}
                </ul>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
                  Latest reviews
                </h3>
                <span className="text-[10px] text-muted">
                  {reviews.length} reviews
                </span>
              </div>

              {reviewsLoading ? (<p className="mt-2 text-xs text-muted">Loading reviews…</p>) : reviews.length === 0 ? (<p className="mt-2 rounded-xl border border-line bg-paper/40 px-3 py-3 text-xs leading-relaxed text-muted">
                  No reviews yet. Purchase the product and write the first one from your order.
                </p>) : (<div className="mt-2 space-y-2">
                  {reviews.slice(0, 3).map((review) => (<div key={review.id} className="rounded-xl border border-line bg-paper/50 p-3">
                      <div className="flex items-center justify-between gap-2">
                        <div className="flex min-w-0 items-center gap-1.5 text-[11px] text-muted">
                          <ReviewStars value={review.rating}/>
                          <span className="truncate">{review.author}</span>
                        </div>
                        <SentimentBadge sentiment={review.sentiment}/>
                      </div>
                      <p className="mt-1.5 text-xs leading-relaxed text-ink-soft">
                        {review.summary || review.content}
                      </p>
                      {review.tags.length ? (<div className="mt-2 flex flex-wrap gap-1">
                          {review.tags.map((tag) => (<span key={tag} className="rounded-full border border-line bg-card px-2 py-0.5 text-[10px] text-muted">
                              {tag}
                            </span>))}
                        </div>) : null}
                      {review.pros.length || review.cons.length ? (<div className="mt-2 space-y-0.5 text-[11px]">
                          {review.pros.map((pro) => (<p key={pro} className="text-brand">
                              + {pro}
                            </p>))}
                          {review.cons.map((con) => (<p key={con} className="text-amber-700">
                              - {con}
                            </p>))}
                        </div>) : null}
                    </div>))}
                </div>)}
            </div>
          </div>

          <div className="space-y-4">
            <div className="rounded-2xl border border-line bg-paper/50 p-4">
              <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
                Score breakdown
              </h3>
              <div className="mt-3 space-y-3">
                {Object.entries(item.breakdown).map(([key, value]) => (<ScoreBar key={key} label={BREAKDOWN_LABELS[key] ?? key} value={value}/>))}
              </div>
              <p className="mt-3 text-[10px] leading-relaxed text-muted">
                Scores combine price, rating, review count, preference match
                {"semantic" in item.breakdown ? ", and semantic relevance" : ""}{" "}
                Make your own judgment before ordering.
              </p>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {product.tags.map((tag) => (<span key={tag} className="rounded-full border border-line bg-card px-2 py-0.5 text-[10px] text-ink-soft">
                  {tag}
                </span>))}
            </div>

            <button type="button" onClick={() => onOrder(item)} className="flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-3 text-sm font-semibold text-white transition hover:bg-brand-dark">
              <ShoppingBag className="h-4 w-4"/>
              Place demo order
            </button>
            <p className="text-center text-[10px] text-muted">
              Demo flow; no real payment
            </p>
          </div>
        </div>
      </div>
    </div>);
}
