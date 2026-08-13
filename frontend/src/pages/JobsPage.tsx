import { useQuery } from "@tanstack/react-query";
import { fetchJobs } from "@/lib/api/jobs";
import { Card } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { Loader2 } from "lucide-react";
import Layout from "@/components/shared/Layout";

export default function JobsPage() {
  const { data: jobs, isLoading, error } = useQuery({
    queryKey: ["jobs"],
    queryFn: () => fetchJobs(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <Alert variant="error">Failed to load jobs</Alert>
      </div>
    );
  }

  return (
    <Layout>
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <h1 className="text-xl font-bold">Jobs</h1>
          <p className="text-sm text-slate-400">Processing job history and status</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {!jobs || jobs.length === 0 ? (
          <Card className="text-center py-12">
            <p className="text-slate-400">No jobs yet.</p>
          </Card>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <Card key={job.id} className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-200">{job.job_type}</p>
                  <p className="text-xs text-slate-400">
                    Job #{job.id} • Project #{job.project_id} • Priority: {job.priority}
                  </p>
                  {job.error_message && (
                    <p className="text-xs text-red-400 mt-1">{job.error_message}</p>
                  )}
                </div>
                <div className="flex items-center gap-3">
                  <Badge status={job.status}>{job.status}</Badge>
                  <span className="text-xs text-slate-500">
                    {new Date(job.created_at).toLocaleString()}
                  </span>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>
    </Layout>
  );
}
