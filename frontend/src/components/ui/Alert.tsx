import { cn } from "@/lib/utils";

export function Alert({
  className,
  variant = "info",
  children,
}: React.HTMLAttributes<HTMLDivElement> & {
  variant?: "info" | "error" | "success";
}) {
  const variants = {
    info: "border-blue-800 bg-blue-900/20 text-blue-200",
    error: "border-red-800 bg-red-900/20 text-red-200",
    success: "border-emerald-800 bg-emerald-900/20 text-emerald-200",
  };

  return (
    <div className={cn("rounded-lg border px-4 py-3 text-sm", variants[variant], className)}>
      {children}
    </div>
  );
}
