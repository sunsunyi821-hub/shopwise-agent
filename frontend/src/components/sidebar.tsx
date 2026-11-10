"use client";
import { MessageSquare, Plus, Sparkles } from "lucide-react";
import type { SessionSummary } from "@/lib/types";
import { cn, formatDate } from "@/lib/utils";
export function Sidebar({ sessions, activeSessionId, onNew, onSelect, }: {
    sessions: SessionSummary[];
    activeSessionId: string | null;
    onNew: () => void;
    onSelect: (sessionId: string) => void;
}) {
    return (<aside className="hidden w-[270px] shrink-0 flex-col bg-brand-dark text-[#f3efe4] md:flex">
      <div className="flex items-center gap-2.5 px-5 pb-5 pt-6">
        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-[#f3efe4]/10 text-[#f3efe4]">
          <Sparkles className="h-4 w-4"/>
        </span>
        <div>
          <p className="font-display text-lg leading-none tracking-tight">ShopWise</p>
          <p className="mt-1 text-[10px] uppercase tracking-[0.18em] text-[#f3efe4]/50">
            shopping agent
          </p>
        </div>
      </div>

      <div className="px-3">
        <button type="button" onClick={onNew} className="flex w-full items-center justify-center gap-2 rounded-xl border border-[#f3efe4]/15 bg-[#f3efe4]/8 py-2.5 text-xs font-semibold text-[#f3efe4] transition hover:bg-[#f3efe4]/15">
          <Plus className="h-3.5 w-3.5"/>
          New shopping chat
        </button>
      </div>

      <div className="mt-6 flex-1 overflow-y-auto px-3 scrollbar-thin">
        <p className="px-2 pb-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-[#f3efe4]/40">
          Recent chats
        </p>
        {sessions.length === 0 ? (<p className="px-2 py-3 text-[11px] leading-relaxed text-[#f3efe4]/45">
            No history yet. Describe a shopping request and the agent will save it here.
          </p>) : (<ul className="space-y-1">
            {sessions.map((session) => (<li key={session.id}>
                <button type="button" onClick={() => onSelect(session.id)} className={cn("flex w-full items-start gap-2 rounded-lg px-2 py-2 text-left transition", activeSessionId === session.id
                    ? "bg-[#f3efe4]/12"
                    : "hover:bg-[#f3efe4]/7")}>
                  <MessageSquare className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#f3efe4]/45"/>
                  <span className="min-w-0">
                    <span className="block truncate text-[11.5px] font-medium text-[#f3efe4]/85">
                      {session.title}
                    </span>
                    <span className="mt-0.5 block text-[10px] text-[#f3efe4]/35">
                      {formatDate(session.updated_at)}
                    </span>
                  </span>
                </button>
              </li>))}
          </ul>)}
      </div>

      <div className="border-t border-[#f3efe4]/10 px-5 py-4">
        <p className="text-[10px] leading-relaxed text-[#f3efe4]/40">
          Demo catalog · Simulated checkout
          <br />
          No real payment or shipping
        </p>
      </div>
    </aside>);
}
