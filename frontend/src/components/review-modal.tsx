"use client";
import { CheckCircle2, Loader2, Star, X } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Order, Review } from "@/lib/types";
const SENTIMENT_LABELS: Record<string, string> = {
    positive: "Positive",
    neutral: "Neutral",
    negative: "Negative",
};
export function ReviewStars({ value }: {
    value: number;
}) {
    return (<span className="flex items-center gap-0.5">
      {Array.from({ length: 5 }).map((_, index) => (<Star key={index} className={index < value
                ? "h-3.5 w-3.5 fill-amber-500 text-amber-500"
                : "h-3.5 w-3.5 text-muted/30"}/>))}
    </span>);
}
export function SentimentBadge({ sentiment }: {
    sentiment: string;
}) {
    const tone = sentiment === "positive"
        ? "bg-brand-soft text-brand-dark"
        : sentiment === "negative"
            ? "bg-amber-50 text-amber-800"
            : "bg-paper text-muted";
    return (<span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-semibold ${tone}`}>
      {SENTIMENT_LABELS[sentiment] ?? sentiment}
    </span>);
}
export function ReviewModal({ order, review, onClose, onSubmitted, }: {
    order: Order | null;
    review?: Review | null;
    onClose: () => void;
    onSubmitted?: (review: Review) => void;
}) {
    const [rating, setRating] = useState(review?.rating ?? 5);
    const [content, setContent] = useState(review?.content ?? "");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<(Review & {
        degraded: boolean;
    }) | null>(null);
    const [isEditing] = useState(Boolean(review));
    if (!order)
        return null;
    async function submit() {
        if (!order)
            return;
        const text = content.trim();
        if (text.length < 5) {
            setError("Please write at least 5 characters");
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            const saved = review
                ? await api.updateReview(review.id, {
                    rating,
                    content: text,
                    author: "Demo user",
                    user_id: "demo-user",
                })
                : await api.createReview({
                    order_id: order.id,
                    rating,
                    content: text,
                    author: "Demo user",
                    user_id: "demo-user",
                });
            setResult(saved);
            onSubmitted?.(saved);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Failed to submit the review. Please try again.");
        }
        finally {
            setSubmitting(false);
        }
    }
    return (<div className="fixed inset-0 z-[70] flex items-end justify-center bg-ink/45 backdrop-blur-sm sm:items-center sm:p-6" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-t-3xl bg-card p-6 shadow-2xl sm:rounded-3xl" onClick={(event) => event.stopPropagation()}>
        {result ? (<div>
            <div className="text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-brand-soft">
                <CheckCircle2 className="h-7 w-7 text-brand"/>
              </div>
              <h2 className="mt-4 text-lg font-bold text-ink">
                {isEditing ? "Review updated" : "Review submitted"}
              </h2>
              <p className="mt-1 text-sm text-muted">{order.product_name}</p>
            </div>

            <div className="mt-4 rounded-2xl border border-line bg-paper/60 p-4">
              <div className="flex items-center justify-between gap-2">
                <ReviewStars value={result.rating}/>
                <SentimentBadge sentiment={result.sentiment}/>
              </div>
              <p className="mt-2 text-sm leading-relaxed text-ink-soft">
                {result.summary || result.content}
              </p>
              {result.pros.length ? (<div className="mt-2 flex flex-wrap gap-1.5">
                  {result.pros.map((item) => (<span key={item} className="rounded-full bg-brand-soft/70 px-2 py-0.5 text-[10px] text-brand-dark">
                      + {item}
                    </span>))}
                </div>) : null}
              {result.cons.length ? (<div className="mt-1.5 flex flex-wrap gap-1.5">
                  {result.cons.map((item) => (<span key={item} className="rounded-full bg-amber-50 px-2 py-0.5 text-[10px] text-amber-800">
                      - {item}
                    </span>))}
                </div>) : null}
              {result.tags.length ? (<div className="mt-2 flex flex-wrap gap-1">
                  {result.tags.map((tag) => (<span key={tag} className="rounded-full border border-line bg-card px-2 py-0.5 text-[10px] text-muted">
                      {tag}
                    </span>))}
                </div>) : null}
            </div>

            {result.degraded ? (<p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-[11px] leading-relaxed text-amber-800">
                AI analysis is temporarily unavailable. The review was saved with rule-based analysis.
              </p>) : null}

            <button type="button" onClick={onClose} className="mt-4 w-full rounded-xl bg-brand py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark">
              Done
            </button>
          </div>) : (<>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-muted">
                  {isEditing ? "Edit review" : "Review product"}
                </p>
                <h2 className="mt-1 text-lg font-bold text-ink">
                  {order.product_name}
                </h2>
              </div>
              <button type="button" onClick={onClose} className="rounded-full p-1.5 text-muted transition hover:bg-paper" aria-label="Close">
                <X className="h-4 w-4"/>
              </button>
            </div>

            <div className="mt-4 rounded-xl bg-paper p-4">
              <p className="text-xs text-muted">Your rating</p>
              <div className="mt-2 flex items-center gap-1">
                {Array.from({ length: 5 }).map((_, index) => (<button key={index} type="button" onClick={() => setRating(index + 1)} className="rounded p-0.5 transition hover:scale-110" aria-label={`Rating ${index + 1}`}>
                    <Star className={index < rating
                    ? "h-6 w-6 fill-amber-500 text-amber-500"
                    : "h-6 w-6 text-muted/30"}/>
                  </button>))}
                <span className="ml-2 text-sm font-semibold text-ink">
                  {rating} / 5
                </span>
              </div>
            </div>

            <label className="mt-4 block">
              <span className="text-xs font-medium text-ink-soft">
                Review text
              </span>
              <textarea value={content} onChange={(event) => setContent(event.target.value)} rows={5} maxLength={2000} className="mt-1.5 w-full resize-none rounded-xl border border-line bg-paper/50 px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:bg-white" placeholder="Write your experience…"/>
            </label>
            <p className="mt-1 text-[10px] leading-relaxed text-muted">
              AI will extract a summary, pros, cons, and tags for other shoppers.
            </p>

            {error ? (<p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
                {error}
              </p>) : null}

            <button type="button" onClick={() => void submit()} disabled={submitting} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60">
              {submitting ? <Loader2 className="h-4 w-4 animate-spin"/> : null}
              {submitting
                ? "Analyzing and saving…"
                : isEditing
                    ? "Save changes"
                    : "Submit review"}
            </button>
          </>)}
      </div>
    </div>);
}
