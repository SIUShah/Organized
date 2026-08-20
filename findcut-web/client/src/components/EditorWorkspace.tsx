import { useEffect, useMemo, useRef, useState } from "react";
import { AudioLines, ChevronDown, Download, Film, Keyboard, Pause, Play, Plus, Redo2, Scissors, Trash2, Undo2, Volume2, VolumeX } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { useAuth } from "@/_core/hooks/useAuth";
import { trpc } from "@/lib/trpc";

interface Clip {
  id: string;
  name: string;
  kind: "video" | "audio";
  start: number;
  duration: number;
  color: string;
  volume: number;
  muted: boolean;
  opacity: number;
  text: string;
  transition: string;
  keyframes: boolean;
  url?: string;
}

const initialClips: Clip[] = [
  { id: "episode", name: "episode_02.mp4", kind: "video", start: 0, duration: 42, color: "bg-cyan-400/70", volume: 82, muted: false, opacity: 100, text: "", transition: "cut", keyframes: false },
  { id: "voice", name: "voice_clean.wav", kind: "audio", start: 0, duration: 38, color: "bg-indigo-400/70", volume: 78, muted: false, opacity: 100, text: "", transition: "cut", keyframes: false },
];

const clone = (clips: Clip[]) => clips.map((clip) => ({ ...clip }));

export default function EditorWorkspace() {
  const [clips, setClips] = useState<Clip[]>(() => {
    try { return JSON.parse(localStorage.getItem("findcut-project") ?? "null") ?? initialClips; } catch { return initialClips; }
  });
  const [selectedId, setSelectedId] = useState("episode");
  const [history, setHistory] = useState<Clip[][]>([]);
  const [future, setFuture] = useState<Clip[][]>([]);
  const [playing, setPlaying] = useState(false);
  const [playhead, setPlayhead] = useState(12);
  const { user } = useAuth();
  const projectMutation = trpc.projects.create.useMutation();
  const [activePanel, setActivePanel] = useState<"media" | "inspector">("media");
  const videoRef = useRef<HTMLVideoElement>(null);
  const selected = clips.find((clip) => clip.id === selectedId) ?? clips[0];
  const timelineLength = Math.max(60, ...clips.map((clip) => clip.start + clip.duration));

  useEffect(() => { localStorage.setItem("findcut-project", JSON.stringify(clips)); }, [clips]);
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    if (playing) {
      void video.play().catch(() => setPlaying(false));
    } else {
      video.pause();
    }
  }, [playing, selectedId]);
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "z") { event.preventDefault(); event.shiftKey ? redo() : undo(); }
      if (event.key === " ") { event.preventDefault(); setPlaying((value) => !value); }
      if (event.key.toLowerCase() === "s" && !event.metaKey && !event.ctrlKey) splitSelected();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  function commit(next: Clip[]) {
    setHistory((items) => [...items.slice(-19), clone(clips)]);
    setFuture([]);
    setClips(next);
  }
  function updateSelected(patch: Partial<Clip>) {
    if (!selected) return;
    commit(clips.map((clip) => clip.id === selected.id ? { ...clip, ...patch } : clip));
  }
  function undo() {
    const previous = history.at(-1);
    if (!previous) return;
    setFuture((items) => [clone(clips), ...items].slice(0, 20));
    setClips(clone(previous));
    setHistory((items) => items.slice(0, -1));
  }
  function redo() {
    const next = future[0];
    if (!next) return;
    setHistory((items) => [...items, clone(clips)].slice(-20));
    setClips(clone(next));
    setFuture((items) => items.slice(1));
  }
  function splitSelected() {
    if (!selected || selected.duration < 4) return;
    const firstDuration = Math.max(2, Math.round(selected.duration / 2));
    const second: Clip = { ...selected, id: `${selected.id}-${Date.now()}`, name: `${selected.name} · split`, start: selected.start + firstDuration, duration: selected.duration - firstDuration };
    commit(clips.flatMap((clip) => clip.id === selected.id ? [{ ...clip, duration: firstDuration }, second] : [clip]));
    setSelectedId(second.id);
  }
  function deleteSelected() {
    if (!selected) return;
    commit(clips.filter((clip) => clip.id !== selected.id));
    setSelectedId(clips.find((clip) => clip.id !== selected.id)?.id ?? "");
  }
  function addMedia(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    const kind = file.type.startsWith("audio") ? "audio" : "video";
    const newClip: Clip = { id: `${file.name}-${Date.now()}`, name: file.name, kind, start: timelineLength, duration: 12, color: kind === "audio" ? "bg-indigo-400/70" : "bg-cyan-400/70", volume: 80, muted: false, opacity: 100, text: "", transition: "cut", keyframes: false, url: URL.createObjectURL(file) };
    commit([...clips, newClip]);
    setSelectedId(newClip.id);
  }
  function saveProject() {
    const document = JSON.stringify({ clips, playhead });
    localStorage.setItem("findcut-project", JSON.stringify(clips));
    if (user) projectMutation.mutate({ name: "FindCut beta project", document });
  }
  function moveSelected(direction: -1 | 1) {
    if (!selected) return;
    const index = clips.findIndex((clip) => clip.id === selected.id);
    const target = index + direction;
    if (target < 0 || target >= clips.length) return;
    const reordered = [...clips];
    [reordered[index], reordered[target]] = [reordered[target], reordered[index]];
    commit(reordered);
  }

  return <Card id="editor" className="border-cyan-300/15 bg-slate-950/75 shadow-2xl shadow-cyan-950/30">
    <CardHeader className="border-b border-white/10 pb-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div><Badge className="border border-cyan-300/30 bg-cyan-300/10 text-cyan-200">Live workspace surface</Badge><CardTitle className="mt-3 text-xl text-white">FindCut editor beta</CardTitle></div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" variant="outline" onClick={undo} disabled={!history.length} className="border-white/10 bg-white/5 text-white"><Undo2 className="mr-1 size-4" />Undo</Button>
          <Button size="sm" variant="outline" onClick={redo} disabled={!future.length} className="border-white/10 bg-white/5 text-white"><Redo2 className="mr-1 size-4" />Redo</Button>
          <label className="inline-flex h-9 cursor-pointer items-center gap-2 rounded-md bg-cyan-300 px-3 text-sm font-medium text-slate-950 hover:bg-cyan-200"><Plus className="size-4" />Import<input type="file" accept="video/*,audio/*" className="sr-only" onChange={addMedia} /></label>
        </div>
      </div>
    </CardHeader>
    <CardContent className="space-y-4 p-4 sm:p-6">
      <div className="grid gap-4 lg:grid-cols-[220px_minmax(0,1fr)_240px]">
        <div className="space-y-3">
          <div className="flex gap-2"><Button size="sm" variant={activePanel === "media" ? "default" : "outline"} onClick={() => setActivePanel("media")} className="flex-1">Media</Button><Button size="sm" variant={activePanel === "inspector" ? "default" : "outline"} onClick={() => setActivePanel("inspector")} className="flex-1">Inspector</Button></div>
          {activePanel === "media" ? <div className="space-y-2">{clips.map((clip) => <button key={clip.id} onClick={() => setSelectedId(clip.id)} className={`w-full rounded-xl border p-3 text-left transition ${clip.id === selectedId ? "border-cyan-300/50 bg-cyan-300/10" : "border-white/10 bg-white/[0.03] hover:bg-white/[0.07]"}`}><div className="flex items-center gap-2 text-xs text-slate-300">{clip.kind === "video" ? <Film className="size-4 text-cyan-300" /> : <AudioLines className="size-4 text-indigo-300" />}<span className="truncate">{clip.name}</span></div><div className="mt-2 text-[10px] text-slate-500">{clip.duration}s · {clip.kind}</div></button>)}</div> : <div className="rounded-xl border border-white/10 bg-white/[0.03] p-3 text-xs leading-6 text-slate-400"><Keyboard className="mb-2 size-4 text-cyan-300" />Shortcuts:<br /><b className="text-slate-200">Space</b> play/pause<br /><b className="text-slate-200">S</b> split selected<br /><b className="text-slate-200">Ctrl/Cmd + Z</b> undo<br /><b className="text-slate-200">Shift + Ctrl/Cmd + Z</b> redo</div>}
        </div>
        <div className="space-y-3">
          <div className="relative aspect-video overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-cyan-300/20 via-slate-900 to-indigo-400/20">
            {selected?.url && selected.kind === "video" ? <video ref={videoRef} src={selected.url} onTimeUpdate={(event) => setPlayhead(Math.floor(event.currentTarget.currentTime))} onEnded={() => setPlaying(false)} className="h-full w-full object-contain" controls={false} /> : <div className="absolute inset-0 grid place-items-center text-center text-sm text-slate-400"><div><MonitorIcon /><div className="mt-2">Preview engine ready</div><div className="text-xs text-slate-600">Import a video to preview it here</div></div></div>}
            <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between rounded-xl border border-white/10 bg-slate-950/75 px-3 py-2"><Button size="icon" variant="ghost" onClick={() => setPlaying((value) => !value)} className="text-white">{playing ? <Pause className="size-4" /> : <Play className="size-4" />}</Button><span className="font-mono text-xs text-cyan-200">00:{String(playhead).padStart(2, "0")} / 01:00</span><span className="text-xs text-slate-500">{selected?.name ?? "No clip"}</span></div>
          </div>
          <div className="rounded-xl border border-white/10 bg-slate-950/60 p-3"><div className="mb-3 flex justify-between text-xs text-slate-500"><span>Playhead</span><span>{playhead}s</span></div><Slider value={[playhead]} min={0} max={60} step={1} onValueChange={(value) => setPlayhead(value[0] ?? 0)} /></div>
        </div>
        <div className="space-y-3 rounded-xl border border-white/10 bg-white/[0.03] p-4">
          <div className="flex items-center justify-between"><span className="text-xs uppercase tracking-[0.16em] text-slate-500">Inspector</span><Scissors className="size-4 text-cyan-300" /></div>
          {selected ? <div className="space-y-4"><div><Label className="text-xs text-slate-400">Clip name</Label><Input value={selected.name} onChange={(event) => updateSelected({ name: event.target.value })} className="mt-1 border-white/10 bg-slate-950/60 text-white" /></div><div><Label className="text-xs text-slate-400">Duration · {selected.duration}s</Label><Slider value={[selected.duration]} min={2} max={90} step={1} onValueChange={(value) => updateSelected({ duration: value[0] ?? selected.duration })} className="mt-3" /></div><div><Label className="text-xs text-slate-400">Opacity · {selected.opacity}%</Label><Slider value={[selected.opacity]} min={0} max={100} step={1} onValueChange={(value) => updateSelected({ opacity: value[0] ?? selected.opacity })} className="mt-3" /></div><div><Label className="text-xs text-slate-400">Audio · {selected.volume}%</Label><div className="mt-2 flex items-center gap-2"><Button size="icon" variant="ghost" onClick={() => updateSelected({ muted: !selected.muted })} className="text-slate-300">{selected.muted ? <VolumeX className="size-4" /> : <Volume2 className="size-4" />}</Button><Slider value={[selected.volume]} min={0} max={100} step={1} onValueChange={(value) => updateSelected({ volume: value[0] ?? selected.volume })} /></div></div><div><Label className="text-xs text-slate-400">Text overlay</Label><Input value={selected.text} onChange={(event) => updateSelected({ text: event.target.value })} placeholder="Add a caption or title" className="mt-1 border-white/10 bg-slate-950/60 text-white placeholder:text-slate-600" /></div><div className="grid grid-cols-2 gap-2"><Select value={selected.transition} onValueChange={(value) => updateSelected({ transition: value })}><SelectTrigger className="border-white/10 bg-slate-950/60 text-white"><SelectValue /></SelectTrigger><SelectContent><SelectItem value="cut">Cut</SelectItem><SelectItem value="fade">Fade</SelectItem><SelectItem value="dissolve">Dissolve</SelectItem><SelectItem value="wipe">Wipe</SelectItem></SelectContent></Select><Button variant={selected.keyframes ? "default" : "outline"} onClick={() => updateSelected({ keyframes: !selected.keyframes })} className="border-white/10">Keyframes</Button></div><div className="flex gap-2"><Button size="sm" variant="outline" onClick={() => moveSelected(-1)} className="flex-1 border-white/10">Earlier</Button><Button size="sm" variant="outline" onClick={() => moveSelected(1)} className="flex-1 border-white/10">Later</Button></div><div className="flex gap-2"><Button size="sm" onClick={splitSelected} className="flex-1 bg-cyan-300 text-slate-950 hover:bg-cyan-200"><Scissors className="mr-1 size-4" />Split</Button><Button size="sm" variant="destructive" onClick={deleteSelected}><Trash2 className="size-4" /></Button></div></div> : <div className="text-sm text-slate-500">Import or select a clip to edit.</div>}
        </div>
      </div>
      <div className="rounded-2xl border border-white/10 bg-slate-950/70 p-4"><div className="mb-3 flex flex-wrap items-center justify-between gap-3"><div className="flex items-center gap-3"><span className="text-xs uppercase tracking-[0.2em] text-slate-500">Timeline</span><span className="text-xs text-slate-600">{clips.length} clips · {user ? "cloud save enabled" : "local autosave"}</span></div><div className="flex gap-2"><Button size="sm" variant="outline" onClick={saveProject} disabled={projectMutation.isPending} className="border-white/10"><Download className="mr-1 size-4" />{projectMutation.isPending ? "Saving…" : user ? "Save to cloud" : "Save locally"}</Button>{projectMutation.isError && <span className="text-xs text-rose-200">Cloud save failed; your local draft is still kept.</span>}{projectMutation.isSuccess && <span className="text-xs text-emerald-200">Cloud draft saved.</span>}</div></div><div className="space-y-3 overflow-x-auto pb-1">{clips.map((clip) => <div key={clip.id} className="min-w-[520px] cursor-pointer" onClick={() => setSelectedId(clip.id)}><div className="mb-1 flex items-center justify-between text-[10px] text-slate-500"><span>{clip.kind === "video" ? "V1" : "A1"} · {clip.name}</span><span>{clip.start}s — {clip.start + clip.duration}s</span></div><div className="relative h-10 rounded-lg bg-white/[0.04]"><div className={`absolute inset-y-1 rounded-md ${clip.color} ${clip.id === selectedId ? "ring-2 ring-white/70" : ""}`} style={{ left: `${(clip.start / timelineLength) * 100}%`, width: `${(clip.duration / timelineLength) * 100}%`, opacity: clip.opacity / 100 }}><div className="flex h-full items-center gap-2 overflow-hidden px-3 text-xs font-medium text-slate-950"><span className="truncate">{clip.name}</span>{clip.text && <span className="rounded bg-slate-950/40 px-1 text-white">T: {clip.text}</span>}</div></div></div></div>)}</div></div>
    </CardContent>
  </Card>;
}

function MonitorIcon() { return <div className="mx-auto grid size-12 place-items-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10"><Film className="size-5 text-cyan-200" /></div>; }
