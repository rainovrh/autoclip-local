import { useQuery } from "@tanstack/react-query";
import { fetchHealth } from "@/lib/api/settings";

export default function HomePage() {
  const { data, isLoading, isError } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  return (
    <main className="mx-auto flex min-h-screen max-w-4xl flex-col gap-6 px-6 py-12">
      <header>
        <h1 className="text-3xl font-bold tracking-tight">AutoClip Local</h1>
        <p className="mt-2 text-slate-400">
          Potong video panjang menjadi klip vertikal dengan subtitle otomatis.
        </p>
      </header>

      <section className="rounded-xl border border-slate-700 bg-slate-900 p-6">
        <h2 className="text-lg font-semibold">Status API</h2>
        {isLoading && <p className="mt-2 text-slate-400">Memeriksa koneksi...</p>}
        {isError && (
          <p className="mt-2 text-red-400">
            Backend belum berjalan. Jalankan FastAPI di port 8000.
          </p>
        )}
        {data && (
          <p className="mt-2 text-emerald-400">
            {data.message} ({data.status})
          </p>
        )}
      </section>
    </main>
  );
}
