"use client";
import { CheckCircle2, Loader2, Sparkles, Store, X, } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { Product, SellerProductCreated } from "@/lib/types";
import { formatPrice } from "@/lib/utils";
export function SellerModal({ open, sellerId, version = 0, onClose, }: {
    open: boolean;
    sellerId: string;
    version?: number;
    onClose: () => void;
}) {
    const [categories, setCategories] = useState<string[]>([]);
    const [listings, setListings] = useState<Product[]>([]);
    const [loadingListings, setLoadingListings] = useState(false);
    const [category, setCategory] = useState("");
    const [description, setDescription] = useState("");
    const [price, setPrice] = useState("");
    const [brand, setBrand] = useState("");
    const [loadingCategories, setLoadingCategories] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<SellerProductCreated | null>(null);
    useEffect(() => {
        if (!open)
            return;
        setResult(null);
        setError(null);
        setDescription("");
        setPrice("");
        setBrand("");
        setLoadingCategories(true);
        api
            .categories()
            .then((data) => {
            setCategories(data);
            setCategory((current) => current || data[0] || "");
        })
            .catch(() => setCategories([]))
            .finally(() => setLoadingCategories(false));
        setLoadingListings(true);
        api
            .sellerProducts(sellerId)
            .then(setListings)
            .catch(() => setListings([]))
            .finally(() => setLoadingListings(false));
    }, [open, sellerId, version]);
    if (!open)
        return null;
    async function submit() {
        const text = description.trim();
        const value = Number(price);
        if (text.length < 10) {
            setError("Please write at least 10 characters describing the product");
            return;
        }
        if (!Number.isFinite(value) || value <= 0) {
            setError("Please enter a valid price");
            return;
        }
        if (!category) {
            setError("Please choose a category");
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            const created = await api.createSellerProduct({
                description: text,
                price: value,
                category,
                brand: brand.trim() || undefined,
                seller_id: sellerId,
            });
            setResult(created);
            setListings((current) => [created.product, ...current]);
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "Could not create the listing. Please try again.");
        }
        finally {
            setSubmitting(false);
        }
    }
    function resetForm() {
        setResult(null);
        setDescription("");
        setPrice("");
        setBrand("");
        setError(null);
    }
    return (<div className="fixed inset-0 z-[65] flex items-end justify-center bg-ink/45 backdrop-blur-sm sm:items-center sm:p-6" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-card p-6 shadow-2xl sm:rounded-3xl" onClick={(event) => event.stopPropagation()}>
        {result ? (<div>
            <div className="text-center">
              <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-brand-soft">
                <CheckCircle2 className="h-7 w-7 text-brand"/>
              </div>
              <h2 className="mt-4 text-lg font-bold text-ink">Listing created</h2>
              <p className="mt-1 text-sm text-muted">
                Agent structured the listing and added it to the catalog
              </p>
            </div>

            <div className="mt-4 rounded-2xl border border-line bg-paper/60 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="text-sm font-semibold text-ink">
                    {result.product.name}
                  </p>
                  <p className="mt-1 text-[11px] text-muted">
                    {result.product.brand} · {result.product.category}
                  </p>
                </div>
                <span className="shrink-0 text-base font-bold text-brand">
                  {formatPrice(result.product.price)}
                </span>
              </div>

              <p className="mt-2 text-xs leading-relaxed text-ink-soft">
                {result.product.description}
              </p>

              {Object.keys(result.product.attributes).length ? (<div className="mt-2 flex flex-wrap gap-1">
                  {Object.entries(result.product.attributes).map(([key, value]) => (<span key={key} className="rounded-full bg-paper px-2 py-0.5 text-[10px] text-ink-soft">
                      {key}: {String(value)}
                    </span>))}
                </div>) : null}

              {result.product.tags.length ? (<div className="mt-2 flex flex-wrap gap-1">
                  {result.product.tags.map((tag) => (<span key={tag} className="rounded-full border border-line bg-card px-2 py-0.5 text-[10px] text-muted">
                      {tag}
                    </span>))}
                </div>) : null}

              {result.product.pros.length ? (<div className="mt-2 space-y-0.5 text-[11px] text-brand">
                  {result.product.pros.map((pro) => (<p key={pro}>+ {pro}</p>))}
                </div>) : null}
              {result.product.cons.length ? (<div className="mt-1 space-y-0.5 text-[11px] text-amber-700">
                  {result.product.cons.map((con) => (<p key={con}>- {con}</p>))}
                </div>) : null}
            </div>

            {result.degraded ? (<p className="mt-3 rounded-lg bg-amber-50 px-3 py-2 text-[11px] leading-relaxed text-amber-800">
                AI structuring is temporarily unavailable; rule-based extraction was used and the listing is still live.
              </p>) : null}

            <div className="mt-4 flex gap-2">
              <button type="button" onClick={resetForm} className="flex-1 rounded-xl border border-line bg-card py-2.5 text-sm font-semibold text-ink-soft transition hover:bg-paper">
                Create another
              </button>
              <button type="button" onClick={onClose} className="flex-1 rounded-xl bg-brand py-2.5 text-sm font-semibold text-white transition hover:bg-brand-dark">
                Done
              </button>
            </div>
          </div>) : (<>
            <div className="flex items-start justify-between">
              <div>
                <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
                  <Store className="h-3.5 w-3.5"/>
                  Seller center
                </p>
                <h2 className="mt-1 text-lg font-bold text-ink">List a product</h2>
              </div>
              <button type="button" onClick={onClose} className="rounded-full p-1.5 text-muted transition hover:bg-paper" aria-label="Close">
                <X className="h-4 w-4"/>
              </button>
            </div>

            <div className="mt-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-semibold uppercase tracking-wide text-muted">
                  My listings
                </h3>
                <span className="text-[10px] text-muted">
                  {listings.length} item(s)
                </span>
              </div>
              {loadingListings ? (<p className="mt-2 text-[11px] text-muted">Loading listings…</p>) : listings.length === 0 ? (<p className="mt-2 rounded-lg border border-line bg-paper/40 px-3 py-2 text-[11px] leading-relaxed text-muted">
                  No listings yet. Create your first one below.
                </p>) : (<div className="mt-2 space-y-1.5">
                  {listings.slice(0, 4).map((listing) => (<div key={listing.id} className="flex items-center justify-between gap-2 rounded-lg border border-line bg-paper/40 px-2.5 py-2">
                      <div className="min-w-0">
                        <p className="truncate text-[11px] font-medium text-ink">
                          {listing.name}
                        </p>
                        <p className="text-[10px] text-muted">
                          {listing.category}
                        </p>
                      </div>
                      <span className="shrink-0 text-[11px] font-semibold text-brand">
                        {formatPrice(listing.price)}
                      </span>
                    </div>))}
                </div>)}
            </div>

            <div className="mt-4 rounded-xl bg-brand-soft/60 px-3 py-2 text-[11px] leading-relaxed text-brand-dark">
              <span className="flex items-center gap-1 font-semibold">
                <Sparkles className="h-3 w-3"/>
                The agent will structure your listing
              </span>
              You describe the product and set the price; AI extracts the name, attributes, highlights, and caveats.
            </div>

            <label className="mt-4 block">
              <span className="text-xs font-medium text-ink-soft">
                Product description
              </span>
              <textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={6} maxLength={2000} className="mt-1.5 w-full resize-none rounded-xl border border-line bg-paper/50 px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:bg-white" placeholder="For example: a 500ml amino-acid body wash for sensitive skin, light scent, fine foam, priced at ¥69…"/>
            </label>

            <div className="mt-3 grid gap-3 sm:grid-cols-2">
              <label className="block">
                <span className="text-xs font-medium text-ink-soft">Price (CNY)</span>
                <input type="number" min="0.01" step="0.01" value={price} onChange={(event) => setPrice(event.target.value)} className="mt-1.5 w-full rounded-xl border border-line bg-paper/50 px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:bg-white" placeholder="69"/>
              </label>
              <label className="block">
                <span className="text-xs font-medium text-ink-soft">Category</span>
                <select value={category} onChange={(event) => setCategory(event.target.value)} disabled={loadingCategories} className="mt-1.5 w-full rounded-xl border border-line bg-paper/50 px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:bg-white disabled:opacity-60">
                  {categories.map((item) => (<option key={item} value={item}>
                      {item}
                    </option>))}
                </select>
              </label>
            </div>

            <label className="mt-3 block">
              <span className="text-xs font-medium text-ink-soft">
                Brand (optional)
              </span>
              <input value={brand} onChange={(event) => setBrand(event.target.value)} maxLength={50} className="mt-1.5 w-full rounded-xl border border-line bg-paper/50 px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:bg-white" placeholder="Independent seller / your brand"/>
            </label>

            <p className="mt-2 text-[10px] leading-relaxed text-muted">
              You control price and category; AI never changes them. A new listing enters the buyer catalog immediately.
            </p>

            {error ? (<p className="mt-2 rounded-lg bg-red-50 px-3 py-2 text-xs text-red-700">
                {error}
              </p>) : null}

            <button type="button" onClick={() => void submit()} disabled={submitting} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-brand py-3 text-sm font-semibold text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:opacity-60">
              {submitting ? (<Loader2 className="h-4 w-4 animate-spin"/>) : (<Sparkles className="h-4 w-4"/>)}
              {submitting ? "Structuring and publishing…" : "Let the agent structure and publish"}
            </button>
          </>)}
      </div>
    </div>);
}
