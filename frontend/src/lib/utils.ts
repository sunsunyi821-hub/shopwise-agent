export function cn(...classes: Array<string | false | null | undefined>) {
    return classes.filter(Boolean).join(" ");
}
export function formatPrice(value: number) {
    return new Intl.NumberFormat("zh-CN", {
        style: "currency",
        currency: "CNY",
        minimumFractionDigits: Number.isInteger(value) ? 0 : 2,
        maximumFractionDigits: 2,
    }).format(value);
}
export function formatDate(value: string) {
    return new Intl.DateTimeFormat("zh-CN", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    }).format(new Date(value));
}
export const CATEGORY_EMOJI: Record<string, string> = {
    沐浴露: "🧴",
    洗发水: "🫧",
    面霜: "🫙",
    防晒霜: "☀️",
    牙膏: "🪥",
    洗衣液: "🧺",
};
export function categoryEmoji(category: string) {
    return CATEGORY_EMOJI[category] ?? "🛍️";
}
export const CATEGORY_GRADIENT: Record<string, string> = {
    沐浴露: "from-teal-100 via-emerald-50 to-cyan-100",
    洗发水: "from-sky-100 via-blue-50 to-indigo-100",
    面霜: "from-rose-100 via-orange-50 to-amber-100",
    防晒霜: "from-amber-100 via-yellow-50 to-orange-100",
    牙膏: "from-violet-100 via-fuchsia-50 to-pink-100",
    洗衣液: "from-lime-100 via-green-50 to-emerald-100",
};
export function categoryGradient(category: string) {
    return CATEGORY_GRADIENT[category] ?? "from-stone-100 to-stone-50";
}
export function scorePercent(score: number) {
    return Math.round(Math.max(0, Math.min(1, score)) * 100);
}
export function scoreTone(score: number) {
    if (score >= 0.8)
        return "text-emerald-700 bg-emerald-50 border-emerald-200";
    if (score >= 0.65)
        return "text-amber-700 bg-amber-50 border-amber-200";
    return "text-stone-600 bg-stone-50 border-stone-200";
}
