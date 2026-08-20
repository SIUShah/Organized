import { useAuth } from "@/_core/hooks/useAuth";
import { startLogin } from "@/const";
import { trpc } from "@/lib/trpc";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import { AlertCircle, ArrowLeft, Bot, CheckCircle2, CircleDot, ExternalLink, LogOut, MessageCircle, Radio, Send, ShieldCheck, Sparkles } from "lucide-react";
import { useState } from "react";
import { Link } from "wouter";

type ChatMessage = { role: "user" | "assistant"; content: string };

const suggestions = [
  "What should we build next to make FindCut valuable for Pakistani creators?",
  "Review the beta funnel and identify the biggest risk.",
  "Give me a focused 7-day CTO execution plan.",
];

export default function CTODashboard() {
  const { user, loading, logout } = useAuth();
  const statusQuery = trpc.cto.status.useQuery(undefined, { enabled: Boolean(user) });
  const askMutation = trpc.cto.ask.useMutation();
  const broadcastMutation = trpc.cto.broadcast.useMutation();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [broadcast, setBroadcast] = useState("");

  if (loading) return <DashboardLoading />;
  if (!user) return <LoginGate />;
  if (statusQuery.isError) return <AccessDenied userName={user.name ?? user.email ?? "account"} onLogout={logout} />;

  const sendMessage = async (content = draft) => {
    const trimmed = content.trim();
    if (!trimmed || askMutation.isPending) return;
    const next = [...messages, { role: "user" as const, content: trimmed }];
    setMessages(next);
    setDraft("");
    try {
      const result = await askMutation.mutateAsync({ messages: next });
      setMessages([...next, { role: "assistant", content: result.answer }]);
    } catch {
      setMessages([...next, { role: "assistant", content: "The CTO channel is temporarily unavailable. Check the dashboard connection status and try again." }]);
    }
  };

  const sendBroadcast = async () => {
    const trimmed = broadcast.trim();
    if (!trimmed || broadcastMutation.isPending) return;
    await broadcastMutation.mutateAsync({ message: trimmed });
    setBroadcast("");
  };

  return (
    <div className="min-h-screen bg-[#071114] text-slate-100">
      <header className="sticky top-0 z-30 border-b border-white/10 bg-[#071114]/90 backdrop-blur-xl">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
          <div className="flex min-w-0 items-center gap-3">
            <div className="grid size-10 shrink-0 place-items-center rounded-2xl border border-amber-200/30 bg-amber-200/10 text-amber-100"><Bot className="size-5" /></div>
            <div className="min-w-0"><p className="truncate font-semibold">FindCut CTO Console</p><p className="truncate text-xs text-slate-500">Protected founder workspace</p></div>
          </div>
          <div className="flex items-center gap-2"><Link href="/"><Button variant="outline" className="hidden border-white/15 bg-white/5 text-slate-100 sm:inline-flex"><ArrowLeft className="mr-2 size-4" /> Public site</Button></Link><Button variant="outline" onClick={() => logout()} className="border-white/15 bg-white/5 text-slate-100"><LogOut className="mr-2 size-4" /> Sign out</Button></div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 px-4 py-8 sm:px-6 lg:grid-cols-[0.72fr_1.28fr] lg:px-8">
        <section className="space-y-6">
          <div><Badge className="border border-amber-200/20 bg-amber-200/10 text-amber-100">AI systems architect mode</Badge><h1 className="mt-4 text-3xl font-semibold tracking-tight sm:text-4xl">Communicate, decide, execute.</h1><p className="mt-3 max-w-xl leading-7 text-slate-400">This is the protected control room for beta operations, Discord communication, and focused product decisions.</p></div>
          <Card className="border-white/10 bg-white/[0.05]"><CardHeader><CardTitle className="flex items-center gap-2 text-white"><ShieldCheck className="size-5 text-emerald-300" /> Access control</CardTitle></CardHeader><CardContent className="space-y-3 text-sm"><div className="flex items-center justify-between gap-4"><span className="text-slate-400">Signed in as</span><span className="text-right text-slate-100">{user.name ?? user.email ?? user.openId}</span></div><div className="flex items-center justify-between gap-4"><span className="text-slate-400">Backend authorization</span><span className="inline-flex items-center gap-1.5 text-emerald-200"><CheckCircle2 className="size-4" /> owner/admin verified</span></div><div className="flex items-center justify-between gap-4"><span className="text-slate-400">Session</span><span className="font-mono text-xs text-slate-500">Manus OAuth</span></div></CardContent></Card>
          <Card className="border-white/10 bg-white/[0.05]"><CardHeader><CardTitle className="flex items-center gap-2 text-white"><Radio className="size-5 text-cyan-300" /> Discord operations</CardTitle></CardHeader><CardContent className="space-y-4"><div className="flex items-start gap-3 rounded-xl border border-white/10 bg-black/10 p-3"><CircleDot className={`mt-0.5 size-4 ${statusQuery.data?.discordConfigured ? "text-emerald-300" : "text-amber-300"}`} /><div><p className="text-sm text-slate-200">{statusQuery.data?.discordConfigured ? "Webhook connected" : "Webhook not connected"}</p><p className="mt-1 text-xs leading-5 text-slate-500">{statusQuery.data?.discordConfigured ? "New beta requests and CTO replies can be forwarded server-side." : "Add DISCORD_WEBHOOK_URL through the secure project secret panel to enable delivery."}</p></div></div><div className="grid grid-cols-2 gap-3 text-xs"><div className="rounded-xl border border-white/10 p-3"><p className="text-slate-500">Beta alerts</p><p className="mt-1 font-medium text-white">{statusQuery.data?.discordConfigured ? "Active" : "Waiting"}</p></div><div className="rounded-xl border border-white/10 p-3"><p className="text-slate-500">Channel mode</p><p className="mt-1 font-medium text-white">Webhook</p></div></div><a className="inline-flex items-center text-xs text-cyan-200 hover:text-cyan-100" href="https://discord.gg/H5mhpBPe9" target="_blank" rel="noreferrer">Open Discord server <ExternalLink className="ml-1 size-3" /></a></CardContent></Card>
          <Card className="border-white/10 bg-white/[0.05]"><CardHeader><CardTitle className="flex items-center gap-2 text-white"><MessageCircle className="size-5 text-fuchsia-300" /> Broadcast to Discord</CardTitle></CardHeader><CardContent className="space-y-3"><Textarea value={broadcast} onChange={(event) => setBroadcast(event.target.value)} placeholder="Send a short founder update to the connected channel…" className="min-h-24 border-white/10 bg-black/20 text-white placeholder:text-slate-600" /><Button onClick={sendBroadcast} disabled={!statusQuery.data?.discordConfigured || broadcastMutation.isPending || !broadcast.trim()} className="w-full bg-cyan-300 text-slate-950 hover:bg-cyan-200">{broadcastMutation.isPending ? "Sending…" : "Send to Discord"} <Send className="ml-2 size-4" /></Button>{broadcastMutation.isSuccess && <p className="text-xs text-emerald-200">Message delivered to the configured Discord webhook.</p>}{broadcastMutation.isError && <p className="text-xs text-rose-200">Delivery failed. Check the webhook and try again.</p>}</CardContent></Card>
        </section>

        <section><Card className="flex min-h-[680px] flex-col border-amber-200/15 bg-white/[0.05] shadow-2xl shadow-amber-950/10"><CardHeader className="border-b border-white/10"><div className="flex items-center justify-between gap-4"><div><CardTitle className="flex items-center gap-2 text-white"><Sparkles className="size-5 text-amber-200" /> CTO conversation</CardTitle><p className="mt-1 text-sm text-slate-500">Private NLP strategy channel. Replies are also forwarded to Discord when connected.</p></div><Badge variant="outline" className="border-emerald-200/20 text-emerald-200">online</Badge></div></CardHeader><CardContent className="flex flex-1 flex-col gap-4 p-4 sm:p-6"><div className="flex-1 space-y-3 overflow-auto rounded-2xl border border-white/10 bg-black/15 p-3 sm:p-5">{messages.length === 0 ? <div className="grid min-h-80 place-items-center text-center"><div><Bot className="mx-auto size-10 text-amber-200" /><h2 className="mt-4 text-lg font-medium text-white">Your CTO is ready.</h2><p className="mt-2 max-w-md text-sm leading-6 text-slate-500">Ask about roadmap, architecture, pricing, beta operations, security, or execution.</p><div className="mt-5 grid gap-2 text-left">{suggestions.map((suggestion) => <button key={suggestion} onClick={() => sendMessage(suggestion)} className="rounded-xl border border-white/10 bg-white/[0.04] p-3 text-sm text-slate-300 transition hover:border-amber-200/30 hover:bg-amber-200/[0.08]">{suggestion}</button>)}</div></div></div> : messages.map((message, index) => <div key={`${message.role}-${index}`} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}><div className={`max-w-[88%] rounded-2xl px-4 py-3 text-sm leading-6 ${message.role === "user" ? "bg-amber-200 text-slate-950" : "border border-white/10 bg-white/[0.06] text-slate-200"}`}>{message.content}</div></div>)}{askMutation.isPending && <div className="flex items-center gap-2 text-sm text-slate-500"><Bot className="size-4 animate-pulse" /> CTO is thinking…</div>}{askMutation.isError && <div className="flex items-center gap-2 rounded-xl border border-rose-300/20 bg-rose-300/10 p-3 text-sm text-rose-100"><AlertCircle className="size-4" /> The NLP service could not respond. Try again shortly.</div>}</div><div className="flex flex-col gap-3 sm:flex-row"><Textarea value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) { event.preventDefault(); void sendMessage(); } }} placeholder="Ask your CTO… (Ctrl/Cmd + Enter to send)" className="min-h-24 flex-1 border-white/10 bg-black/20 text-white placeholder:text-slate-600" /><Button onClick={() => void sendMessage()} disabled={!draft.trim() || askMutation.isPending} className="h-auto min-h-12 bg-amber-200 text-slate-950 hover:bg-amber-100 sm:w-32">{askMutation.isPending ? "Thinking…" : "Ask CTO"}<Send className="ml-2 size-4" /></Button></div></CardContent></Card></section>
      </main>
    </div>
  );
}

function LoginGate() {
  return <div className="grid min-h-screen place-items-center bg-[#071114] px-4 text-center text-slate-100"><Card className="w-full max-w-md border-white/10 bg-white/[0.06]"><CardHeader><Bot className="mx-auto size-10 text-amber-200" /><CardTitle className="mt-2 text-2xl text-white">FindCut CTO Console</CardTitle><p className="text-sm leading-6 text-slate-400">Sign in with your FindCut owner account to open the protected AI dashboard.</p></CardHeader><CardContent><Button onClick={() => startLogin()} className="w-full bg-amber-200 text-slate-950 hover:bg-amber-100">Sign in to continue</Button></CardContent></Card></div>;
}

function AccessDenied({ userName, onLogout }: { userName: string; onLogout: () => void }) {
  return <div className="grid min-h-screen place-items-center bg-[#071114] px-4 text-center text-slate-100"><Card className="w-full max-w-md border-rose-200/20 bg-rose-200/[0.05]"><CardHeader><AlertCircle className="mx-auto size-10 text-rose-200" /><CardTitle className="mt-2 text-2xl text-white">Owner access required</CardTitle><p className="text-sm leading-6 text-slate-400">The account {userName} is signed in, but it is not authorized for the CTO console.</p></CardHeader><CardContent><Button onClick={onLogout} variant="outline" className="border-white/15 bg-white/5 text-white">Sign out</Button></CardContent></Card></div>;
}

function DashboardLoading() {
  return <div className="grid min-h-screen place-items-center bg-[#071114] text-slate-300"><div className="flex items-center gap-3"><Bot className="size-5 animate-pulse text-amber-200" /> Checking secure access…</div></div>;
}
