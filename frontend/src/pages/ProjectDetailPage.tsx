import { useState, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchProject,
  uploadVideo,
  downloadYoutube,
  extractAudio,
  transcribeProject,
  analyzeProject,
  renderProject,
  searchBroll,
  garbageCollect,
  scheduleProjectJobs,
} from "@/lib/api/projects";
import { fetchClips } from "@/lib/api/clips";
import { fetchJobs } from "@/lib/api/jobs";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import {
  Upload,
  Play,
  FileText,
  Sparkles,
  Film,
  Image,
  Trash2,
  Calendar,
  ArrowLeft,
  Loader2,
} from "lucide-react";
import { useParams, Link } from "react-router-dom";
import Layout from "@/components/shared/Layout";

export default function ProjectDetailPage() {
  const { id } = useParams<{ id: string }>();
  const projectId = Number(id);
  const queryClient = useQueryClient();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [uploadModal, setUploadModal] = useState(false);
  const [scheduleModal, setScheduleModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const [scheduledAt, setScheduledAt] = useState("");
  const [webhookUrl, setWebhookUrl] = useState("");
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);

  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId),
    enabled: !!projectId,
  });

  const { data: clips } = useQuery({
    queryKey: ["clips", projectId],
    queryFn: () => fetchClips(projectId),
    enabled: !!projectId,
  });

  const { data: jobs } = useQuery({
    queryKey: ["jobs", projectId],
    queryFn: () => fetchJobs(projectId),
    enabled: !!projectId,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadVideo(projectId, file),
    onSuccess: () => {
      setSuccess("Video uploaded successfully");
      setUploadModal(false);
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const actionMutation = useMutation({
    mutationFn: async (action: () => Promise<any>) => action(),
    onSuccess: () => {
      setSuccess("Job queued successfully");
      queryClient.invalidateQueries({ queryKey: ["project", projectId] });
      queryClient.invalidateQueries({ queryKey: ["jobs", projectId] });
      queryClient.invalidateQueries({ queryKey: ["clips", projectId] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const scheduleMutation = useMutation({
    mutationFn: () =>
      scheduleProjectJobs(projectId, {
        job_types: selectedJobs,
        scheduled_at: scheduledAt || undefined,
        webhook_url: webhookUrl || undefined,
      }),
    onSuccess: () => {
      setSuccess("Jobs scheduled successfully");
      setScheduleModal(false);
      setScheduledAt("");
      setWebhookUrl("");
      setSelectedJobs([]);
      queryClient.invalidateQueries({ queryKey: ["jobs", projectId] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) uploadMutation.mutate(file);
  };

  const runAction = (action: () => Promise<any>) => {
    setError(null);
    setSuccess(null);
    actionMutation.mutate(action);
  };

  if (projectLoading) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
        </div>
      </Layout>
    );
  }

  if (!project) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center min-h-screen gap-4">
          <p className="text-slate-400">Project not found</p>
          <Link to="/">
            <Button>Back to Dashboard</Button>
          </Link>
        </div>
      </Layout>
    );
  }

  const availableJobs = [
    { key: "ffmpeg_extract_audio", label: "Extract Audio", icon: FileText },
    { key: "whisper_transcribe", label: "Transcribe", icon: FileText },
    { key: "ollama_analyze", label: "Analyze", icon: Sparkles },
    { key: "render_clip", label: "Render Clips", icon: Film },
    { key: "broll_search", label: "Search B-roll", icon: Image },
    { key: "garbage_collect", label: "Garbage Collect", icon: Trash2 },
  ];

  return (
    <Layout>
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-4 flex items-center gap-4">
          <Link to="/">
            <Button variant="ghost" size="sm">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div className="flex-1">
            <h1 className="text-xl font-bold">{project.title}</h1>
            <p className="text-sm text-slate-400">
              {project.source_type === "youtube" ? "YouTube" : "Local Upload"} •{" "}
              <Badge status={project.status}>{project.status}</Badge>
            </p>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8 space-y-6">
        {error && (
          <Alert variant="error" className="mb-4">
            {error}
          </Alert>
        )}
        {success && (
          <Alert variant="success" className="mb-4">
            {success}
          </Alert>
        )}

        <Card>
          <h2 className="text-lg font-semibold mb-4">Actions</h2>
          <div className="flex flex-wrap gap-2">
            {project.source_type === "local_upload" && (
              <Button onClick={() => setUploadModal(true)}>
                <Upload className="mr-2 h-4 w-4" />
                Upload Video
              </Button>
            )}
            {project.source_type === "youtube" && (
              <Button onClick={() => runAction(() => downloadYoutube(projectId))}>
                <Play className="mr-2 h-4 w-4" />
                Download YouTube
              </Button>
            )}
            <Button
              variant="secondary"
              onClick={() => runAction(() => extractAudio(projectId))}
            >
              <FileText className="mr-2 h-4 w-4" />
              Extract Audio
            </Button>
            <Button
              variant="secondary"
              onClick={() => runAction(() => transcribeProject(projectId))}
            >
              <FileText className="mr-2 h-4 w-4" />
              Transcribe
            </Button>
            <Button
              variant="secondary"
              onClick={() => runAction(() => analyzeProject(projectId))}
            >
              <Sparkles className="mr-2 h-4 w-4" />
              Analyze
            </Button>
            <Button
              variant="secondary"
              onClick={() => runAction(() => renderProject(projectId))}
            >
              <Film className="mr-2 h-4 w-4" />
              Render
            </Button>
            <Button
              variant="secondary"
              onClick={() => runAction(() => searchBroll(projectId))}
            >
              <Image className="mr-2 h-4 w-4" />
              B-roll
            </Button>
            <Button
              variant="ghost"
              onClick={() => runAction(() => garbageCollect(projectId))}
            >
              <Trash2 className="mr-2 h-4 w-4" />
              GC
            </Button>
            <Button
              variant="ghost"
              onClick={() => setScheduleModal(true)}
            >
              <Calendar className="mr-2 h-4 w-4" />
              Schedule
            </Button>
          </div>
        </Card>

        <Card>
          <h2 className="text-lg font-semibold mb-4">Clips</h2>
          {!clips || clips.length === 0 ? (
            <p className="text-slate-400 text-sm">No clips yet. Run render to create clips.</p>
          ) : (
            <div className="space-y-2">
              {clips.map((clip) => (
                <div
                  key={clip.id}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-800/40 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-slate-200">Clip #{clip.id}</p>
                    <p className="text-xs text-slate-400">
                      {clip.resolution || "Pending"} •{" "}
                      {clip.duration_seconds
                        ? `${clip.duration_seconds.toFixed(1)}s`
                        : "—"}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge status={clip.render_status}>{clip.render_status}</Badge>
                    {clip.output_path && (
                      <Button size="sm" variant="secondary" asChild>
                        <Link to={clip.output_path} target="_blank" rel="noreferrer">
                          <Play className="h-3 w-3" />
                        </Link>
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>

        <Card>
          <h2 className="text-lg font-semibold mb-4">Jobs</h2>
          {!jobs || jobs.length === 0 ? (
            <p className="text-slate-400 text-sm">No jobs yet.</p>
          ) : (
            <div className="space-y-2">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-800/40 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-slate-200">{job.job_type}</p>
                    <p className="text-xs text-slate-400">
                      Job #{job.id} • Priority: {job.priority}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge status={job.status}>{job.status}</Badge>
                    {job.error_message && (
                      <span className="text-xs text-red-400 max-w-[200px] truncate" title={job.error_message}>
                        {job.error_message}
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </main>

      <Modal open={uploadModal} onClose={() => setUploadModal(false)} title="Upload Video">
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          onChange={handleFileUpload}
          className="mb-4"
        />
        {uploadMutation.isPending && (
          <p className="text-sm text-slate-400">Uploading...</p>
        )}
      </Modal>

      <Modal open={scheduleModal} onClose={() => setScheduleModal(false)} title="Schedule Jobs">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Scheduled At (ISO 8601, optional)
            </label>
            <Input
              value={scheduledAt}
              onChange={(e) => setScheduledAt(e.target.value)}
              placeholder="2026-08-13T10:00:00Z"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Webhook URL (optional)
            </label>
            <Input
              value={webhookUrl}
              onChange={(e) => setWebhookUrl(e.target.value)}
              placeholder="https://example.com/webhook"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Jobs
            </label>
            <div className="space-y-2">
              {availableJobs.map((job) => (
                <label key={job.key} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={selectedJobs.includes(job.key)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedJobs([...selectedJobs, job.key]);
                      } else {
                        setSelectedJobs(selectedJobs.filter((j) => j !== job.key));
                      }
                    }}
                    className="rounded border-slate-700 bg-slate-800"
                  />
                  <span className="text-sm text-slate-300">{job.label}</span>
                </label>
              ))}
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setScheduleModal(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => scheduleMutation.mutate()}
              disabled={scheduleMutation.isPending || selectedJobs.length === 0}
            >
              {scheduleMutation.isPending ? "Scheduling..." : "Schedule"}
            </Button>
          </div>
        </div>
      </Modal>
    </Layout>
  );
}
