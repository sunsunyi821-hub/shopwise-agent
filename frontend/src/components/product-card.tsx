"use client";
import { Star } from "lucide-react";
import type { ScoredProduct } from "@/lib/types";
import { categoryEmoji, categoryGradient, cn, formatPrice, scorePercent, scoreTone, } from "@/lib/utils";
type Props = {
    item: ScoredProduct;
    onOpen: (item: ScoredProduct) => void;
};
export function ProductCard({ item, onOpen }: Props) {
    const { product } = item;
    return (<article className="group flex w-[255px] shrink-0 flex-col rounded-2xl border border-line bg-card p-3 shadow-[0_2px_14px_rgba(23,33,29,0.04)] transition hover:-translate-y-0.5 hover:shadow-[0_10px_30px_rgba(23,33,29,0.09)]">
      <button type="button" onClick={() => onOpen(item)} className="flex-1 text-left focus:outline-none">
        <div className={cn("relative flex h-28 items-center justify-center overflow-hidden rounded-xl bg-gradient-to-br", categoryGradient(product.category))}>
          <span className="text-4xl drop-shadow-sm">
            {categoryEmoji(product.category)}
          </span>
          <span className={cn("absolute right-2 top-2 rounded-full border px-2 py-0.5 text-[10px] font-semibold", scoreTone(item.score))}>
            {scorePercent(item.score)}% match
          </span>
          <span className="absolute bottom-2 left-2 rounded-full bg-white/75 px-2 py-0.5 text-[10px] font-medium text-ink-soft backdrop-blur">
            {product.brand}
          </span>
          {product.seller_id ? (<span className="absolute left-2 top-2 rounded-full bg-white/80 px-2 py-0.5 text-[10px] font-semibold text-brand-dark backdrop-blur">
              Independent seller
            </span>) : null}
        </div>

        <h3 className="mt-3 line-clamp-2 min-h-[2.5rem] text-sm font-semibold leading-snug text-ink">
          {product.name}
        </h3>

        <div className="mt-1.5 flex items-baseline gap-1.5">
          <span className="text-lg font-bold tracking-tight text-brand">
            {formatPrice(product.price)}
          </span>
          {product.original_price && product.original_price > product.price ? (<span className="text-[11px] text-muted line-through">
              {formatPrice(product.original_price)}
            </span>) : null}
        </div>

        <div className="mt-1 flex items-center gap-1 text-[11px] text-muted">
          <Star className="h-3 w-3 fill-amber-400 text-amber-400"/>
          <span className="font-medium text-ink-soft">{product.rating.toFixed(1)}</span>
          <span>· {product.review_count} reviews</span>
        </div>

        <div className="mt-2 flex flex-wrap gap-1">
          {product.tags.slice(0, 3).map((tag) => (<span key={tag} className="rounded-full bg-brand-soft px-2 py-0.5 text-[10px] font-medium text-brand-dark">
              {tag}
            </span>))}
        </div>

        <p className="mt-2 line-clamp-2 min-h-[2rem] text-[11px] leading-relaxed text-ink-soft">
          {item.reasons[0] ?? product.description}
        </p>
      </button>

      <button type="button" onClick={() => onOpen(item)} className="mt-3 w-full rounded-xl border border-brand/20 bg-brand-soft/60 py-2 text-xs font-semibold text-brand-dark transition hover:bg-brand hover:text-white">
        View recommendation
      </button>
    </article>);
}
export function ProductGrid({ items, onOpen, }: {
    items: ScoredProduct[];
    onOpen: (item: ScoredProduct) => void;
}) {
    if (!items.length)
        return null;
    return (<div className="scrollbar-thin -mx-1 flex gap-3 overflow-x-auto px-1 pb-2">
      {items.map((item) => (<ProductCard key={item.product.id} item={item} onOpen={onOpen}/>))}
    </div>);
}
