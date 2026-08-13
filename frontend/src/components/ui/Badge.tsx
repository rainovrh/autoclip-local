import { cn } from "@/lib/utils";

const statusStyles: Record<string, string> = {
  queued: "bg-slate-700 text-slate-200",
  running: "bg-blue-900/40 text-blue-200",
  completed: "bg-emerald-900/40 text-emerald-200",
  failed: "bg-red-900/40 text-red-200",
  UPLOADED: "bg-slate-700 text-slate-200",
  AUDIO_EXTRACTED: "bg-indigo-900/40 text-indigo-200",
  TRANSCRIBED: "bg-purple-900/40 text-purple-200",
  ANALYZED: "bg-amber-900/40 text-amber-200",
  RENDERED: "bg-emerald-900/40 text-emerald-200",
  FAILED: "bg-red-900/40 text-red-200",
  pending: "bg-slate-700 text-slate-200",
  success: "bg-emerald-900/40 text-emerald-200",
  skipped: "bg-slate-700 text-slate-200",
  found: "bg-blue-900/40 text-blue-200",
};

export function Badge({
  className,
  children,
  status,
}: React.HTMLAttributes<HTMLSpanElement> & { status?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium",
        status && statusStyles[status],
        !status && "bg-slate-800 text-slate-300",
        className,
      )}
    >
      {children}
    </span>
  );
}
