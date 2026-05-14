import type { ImportCommit, ImportPreview, WatchlistRow } from "../types";

export async function previewImport(file: File): Promise<ImportPreview> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/import/preview", { method: "POST", body: formData });
  if (!response.ok) throw new Error("Import preview failed");
  return response.json();
}

export async function commitImport(previewId: string): Promise<ImportCommit> {
  const response = await fetch("/api/import/commit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preview_id: previewId })
  });
  if (!response.ok) throw new Error("Import commit failed");
  return response.json();
}

export async function fetchWatchlist(params = new URLSearchParams()): Promise<WatchlistRow[]> {
  const query = params.toString();
  const response = await fetch(`/api/watchlist${query ? `?${query}` : ""}`);
  if (!response.ok) throw new Error("Failed to load watchlist");
  return response.json();
}
