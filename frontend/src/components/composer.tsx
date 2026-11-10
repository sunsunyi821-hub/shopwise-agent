"use client";
import { ArrowUp, Loader2 } from "lucide-react";
import { useEffect, useRef } from "react";
export function Composer({ value, onChange, onSend, disabled, }: {
    value: string;
    onChange: (value: string) => void;
    onSend: () => void;
    disabled?: boolean;
}) {
    const textareaRef = useRef<HTMLTextAreaElement>(null);
    useEffect(() => {
        const element = textareaRef.current;
        if (!element)
            return;
        element.style.height = "auto";
        element.style.height = `${Math.min(element.scrollHeight, 160)}px`;
    }, [value]);
    useEffect(() => {
        textareaRef.current?.focus();
    }, []);
    function handleKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            if (!disabled)
                onSend();
        }
    }
    return (<div className="rounded-2xl border border-line bg-card p-2 shadow-[0_8px_30px_rgba(23,33,29,0.08)] focus-within:border-brand/40">
      <div className="flex items-end gap-2">
        <textarea ref={textareaRef} value={value} onChange={(event) => onChange(event.target.value)} onKeyDown={handleKeyDown} rows={1} placeholder="Tell me what you want to buy, e.g. body wash under ¥100, sensitive skin, fragrance-free…" className="max-h-40 min-h-[44px] flex-1 resize-none bg-transparent px-2 py-2 text-sm leading-relaxed text-ink outline-none placeholder:text-muted/70"/>
        <button type="button" onClick={onSend} disabled={disabled || !value.trim()} className="mb-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand text-white transition hover:bg-brand-dark disabled:cursor-not-allowed disabled:bg-line disabled:text-muted" aria-label="Send">
          {disabled ? (<Loader2 className="h-4 w-4 animate-spin"/>) : (<ArrowUp className="h-4 w-4"/>)}
        </button>
      </div>
      <div className="flex items-center justify-between px-2 pb-1 pt-1">
        <span className="text-[10px] text-muted">
          Enter to send · Shift + Enter for a new line
        </span>
        <span className="text-[10px] text-muted">
          The agent only recommends; you confirm before ordering
        </span>
      </div>
    </div>);
}
