import { cn } from "@/lib/utils";

export function Card({
  className,
  children,
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-800 bg-slate-900/60 p-5 shadow-sm",
        className,
      )}
    >
      {children}
    </div>
  );
}
