import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  listApiKeys,
  createApiKey,
  deleteApiKey,
  toggleApiKey,
} from "@/lib/api/settings";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Modal } from "@/components/ui/Modal";
import { Badge } from "@/components/ui/Badge";
import { Alert } from "@/components/ui/Alert";
import { Plus, Trash2, ToggleLeft, ToggleRight, Loader2 } from "lucide-react";
import Layout from "@/components/shared/Layout";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [isCreateOpen, setCreateOpen] = useState(false);
  const [serviceName, setServiceName] = useState("");
  const [apiKeyValue, setApiKeyValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const { data: apiKeys, isLoading } = useQuery({
    queryKey: ["api-keys"],
    queryFn: listApiKeys,
  });

  const createMutation = useMutation({
    mutationFn: () => createApiKey({ service_name: serviceName, api_key_value: apiKeyValue }),
    onSuccess: () => {
      setSuccess("API key created");
      setCreateOpen(false);
      setServiceName("");
      setApiKeyValue("");
      setError(null);
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
    onError: (err: Error) => setError(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: deleteApiKey,
    onSuccess: () => {
      setSuccess("API key deleted");
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  const toggleMutation = useMutation({
    mutationFn: toggleApiKey,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  return (
    <Layout>
      <header className="border-b border-slate-800 bg-slate-900/60 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-4">
          <h1 className="text-xl font-bold">Settings</h1>
          <p className="text-sm text-slate-400">API keys and configuration</p>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-8">
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
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">API Keys</h2>
            <Button onClick={() => setCreateOpen(true)}>
              <Plus className="mr-2 h-4 w-4" />
              Add Key
            </Button>
          </div>

          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
            </div>
          ) : !apiKeys || apiKeys.length === 0 ? (
            <p className="text-slate-400 text-sm">No API keys configured.</p>
          ) : (
            <div className="space-y-2">
              {apiKeys.map((key: any) => (
                <div
                  key={key.id}
                  className="flex items-center justify-between rounded-lg border border-slate-800 bg-slate-800/40 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-slate-200">{key.service_name}</p>
                    <p className="text-xs text-slate-400 font-mono">{key.api_key_value}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge status={key.is_active ? "success" : "failed"}>
                      {key.is_active ? "Active" : "Inactive"}
                    </Badge>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => toggleMutation.mutate(key.id)}
                    >
                      {key.is_active ? (
                        <ToggleRight className="h-4 w-4" />
                      ) : (
                        <ToggleLeft className="h-4 w-4" />
                      )}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => deleteMutation.mutate(key.id)}
                    >
                      <Trash2 className="h-4 w-4 text-red-400" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </main>

      <Modal open={isCreateOpen} onClose={() => setCreateOpen(false)} title="Add API Key">
        {error && <Alert variant="error">{error}</Alert>}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              Service Name
            </label>
            <Input
              value={serviceName}
              onChange={(e) => setServiceName(e.target.value)}
              placeholder="e.g., pexels, ollama"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">
              API Key Value
            </label>
            <Input
              value={apiKeyValue}
              onChange={(e) => setApiKeyValue(e.target.value)}
              placeholder="Enter API key"
            />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button variant="ghost" onClick={() => setCreateOpen(false)}>
              Cancel
            </Button>
            <Button
              onClick={() => createMutation.mutate()}
              disabled={createMutation.isPending || !serviceName || !apiKeyValue}
            >
              {createMutation.isPending ? "Saving..." : "Save"}
            </Button>
          </div>
        </div>
      </Modal>
    </Layout>
  );
}
