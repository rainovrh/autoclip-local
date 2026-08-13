import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchProjects,
  createProject,
  deleteProject,
} from "@/lib/api/projects";
import { fetchHealth } from "@/lib/api/settings";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { Plus, Trash2, Play, FileVideo } from "lucide-react";
import { useNavigate } from "react-router-dom";
import Layout from "@/components/shared/Layout";

export default function DashboardPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [isCreateOpen, setCreateOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [sourceType, setSourceType] = useState<"youtube" | "local_upload">("youtube");
  const [sourceUrl, setSourceUrl] = useState("");
  const [originalFilename, setOriginalFilename] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: health } = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
  });

  const { data: projectsData, isLoading } = useQuery({
    queryKey: ["projects"],
    queryFn: fetchProjects,
  });

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
      setCreateOpen(false);
      setTitle("");
      setSourceUrl("");
      setOriginalFilename("");
      setError(null);
    },
    onError: (err: Error) => setError(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
  });

  const handleCreate = () => {
    setError(null);
    createMutation.mutate({
      title,
      source_type: sourceType,
      source_url: sourceType === "youtube" ? sourceUrl : null,
      original_filename: sourceType === "local_upload" ? originalFilename : null,
    });
  };

  return (
    <Layout>
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold">Projects</h1>
            <p className="text-sm text-slate-400">
              {health?.message || "Loading..."}
            </p>
          </div>
          <Button onClick={() => setCreateOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            New Project
          </Button>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
        {isLoading && (
          <p className="text-center text-slate-400">Loading projects...</p>
        )}

        {!isLoading && (!projectsData || projectsData.total === 0) && (
          <Card className="text-center py-12">
            <FileVideo className="mx-auto h-12 w-12 text-slate-600 mb-4" />
            <h2 className="text-lg font-semibold mb-2">No projects yet</h2>
            <p className="text-slate-400 mb-4">
              Create your first project to start clipping videos.
            </p>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Create Project
            </Button>
          </Card>
        )}

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projectsData?.items.map((project) => (
            <Card key={project.id} className="flex flex-col">
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h3 className="font-semibold text-slate-100">{project.title}</h3>
                  <p className="text-xs text-slate-400 mt-1">
                    {project.source_type === "youtube" ? "YouTube" : "Local Upload"}
                  </p>
                </div>
                <Badge status={project.status}>{project.status}</Badge>
              </div>

              <div className="text-xs text-slate-500 space-y-1 mb-4">
                <p>Created: {new Date(project.created_at).toLocaleDateString()}</p>
                {project.source_url && (
                  <p className="truncate">URL: {project.source_url}</p>
                )}
              </div>

              <div className="mt-auto flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() => navigate(`/projects/${project.id}`)}
                >
                  <Play className="mr-1 h-3 w-3" />
                  Open
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => deleteMutation.mutate(project.id)}
                >
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </main>

      <Modal
        open={isCreateOpen}
        onClose={() => setCreateOpen(false)}
        title="Create Project"
      >
        {error && <Alert variant="error">{error}</Alert>}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Title
            </label>
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="My Awesome Video"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Source Type
            </label>
            <select
              value={sourceType}
              onChange={(e) =>
                setSourceType(e.target.value as "youtube" | "local_upload")
              }
              className="w-full rounded-lg border border-slate-700 bg-slate-800 px-3 py-2 text-sm text-slate-100"
            >
              <option value="youtube">YouTube</option>
              <option value="local_upload">Local Upload</option>
            </select>
          </div>

          {sourceType === "youtube" && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                YouTube URL
              </label>
              <Input
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://youtube.com/watch?v=..."
              />
            </div>
          )}

          {sourceType === "local_upload" && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">
                Original Filename
              </label>
              <Input
                value={originalFilename}
                onChange={(e) => setOriginalFilename(e.target.value)}
                placeholder="video.mp4"
              />
            </div>
          )}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleCreate}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? "Creating..." : "Create"}
            </Button>
          </div>
        </div>
      </Modal>
    </Layout>
  );
}
