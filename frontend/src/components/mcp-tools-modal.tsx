"use client";
import { AlertTriangle, CheckCircle2, PlugZap, RefreshCw, Server, Wrench, X, } from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import type { MCPToolsStatus } from "@/lib/types";
function paramNames(tool: MCPToolsStatus["tools"][number]) {
    const properties = tool.input_schema?.properties ?? {};
    const required = new Set(tool.input_schema?.required ?? []);
    return Object.keys(properties).map((name) => ({
        name,
        required: required.has(name),
    }));
}
export function McpToolsModal({ open, onClose, }: {
    open: boolean;
    onClose: () => void;
}) {
    const [status, setStatus] = useState<MCPToolsStatus | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    async function load(refresh = false) {
        setLoading(true);
        setError(null);
        try {
            setStatus(refresh ? await api.refreshMcpTools() : await api.mcpTools());
        }
        catch (err) {
            setError(err instanceof Error ? err.message : "MCP tool discovery failed");
        }
        finally {
            setLoading(false);
        }
    }
    useEffect(() => {
        if (!open)
            return;
        void load(false);
    }, [open]);
    if (!open)
        return null;
    return (<div className="fixed inset-0 z-[65] flex items-end justify-center bg-ink/45 backdrop-blur-sm sm:items-center sm:p-6" role="dialog" aria-modal="true" onClick={onClose}>
      <div className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-t-3xl bg-card p-6 shadow-2xl sm:rounded-3xl" onClick={(event) => event.stopPropagation()}>
        <div className="flex items-start justify-between">
          <div>
            <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-muted">
              <PlugZap className="h-3.5 w-3.5"/>
              Model Context Protocol
            </p>
            <h2 className="mt-1 text-lg font-bold text-ink">MCP external tools</h2>
          </div>
          <button type="button" onClick={onClose} className="rounded-full p-1.5 text-muted transition hover:bg-paper" aria-label="Close">
            <X className="h-4 w-4"/>
          </button>
        </div>

        <div className="mt-4 rounded-xl border border-line bg-paper/50 px-3 py-2 text-[11px] leading-relaxed text-ink-soft">
          At startup the agent discovers tools through MCP <code className="font-mono">tools/list</code>{" "}
          and invokes them during chat through <code className="font-mono">tools/call</code>.
          The demo server searches JD and Taobao demo listings with fixed data.
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-2">
          <span className={status?.available
            ? "flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-medium text-emerald-700"
            : "flex items-center gap-1 rounded-full bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-700"}>
            {status?.available ? (<CheckCircle2 className="h-3 w-3"/>) : (<AlertTriangle className="h-3 w-3"/>)}
            {status?.available ? "Connected" : "Disconnected"}
          </span>
          <span className="flex items-center gap-1 rounded-full bg-paper px-2 py-0.5 text-[10px] text-muted">
            <Server className="h-3 w-3"/>
            {status?.server ?? "shopwise-marketplace"}
          </span>
          <span className="rounded-full bg-paper px-2 py-0.5 text-[10px] text-muted">
            {status?.transport ?? "stdio"}
          </span>
          <button type="button" onClick={() => void load(true)} disabled={loading} className="ml-auto flex items-center gap-1 rounded-full border border-line bg-card px-2.5 py-1 text-[10px] font-medium text-ink-soft transition hover:border-brand/30 hover:text-brand disabled:opacity-60">
            <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`}/>
            Rediscover
          </button>
        </div>

        {error || status?.error ? (<p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-[11px] text-red-700">
            {error ?? status?.error}
          </p>) : null}

        <div className="mt-3 space-y-2">
          {status?.tools?.length ? (status.tools.map((tool) => (<div key={tool.name} className="rounded-xl border border-line bg-paper/40 px-3 py-2.5">
                <div className="flex items-center gap-1.5">
                  <Wrench className="h-3.5 w-3.5 text-brand"/>
                  <code className="font-mono text-[11px] font-semibold text-ink">
                    {tool.name}
                  </code>
                </div>
                <p className="mt-1 text-[11px] leading-relaxed text-ink-soft">
                  {tool.description}
                </p>
                <div className="mt-1.5 flex flex-wrap gap-1">
                  {paramNames(tool).map((param) => (<span key={param.name} className="rounded-full border border-line bg-card px-1.5 py-0.5 font-mono text-[9px] text-muted">
                      {param.name}
                      {param.required ? "*" : ""}
                    </span>))}
                </div>
              </div>))) : !loading ? (<p className="rounded-xl border border-line bg-paper/40 px-3 py-4 text-center text-xs text-muted">
              No MCP tools discovered.
            </p>) : (<p className="py-4 text-center text-xs text-muted">Discovering tools…</p>)}
        </div>

        <p className="mt-3 text-[10px] leading-relaxed text-muted">
          To connect a real marketplace, point <code className="font-mono">MCP_MARKETPLACE_URL</code>{" "}
          at the official MCP server; the planning and invocation code stays unchanged.
        </p>
      </div>
    </div>);
}
