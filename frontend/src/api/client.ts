import type { HistoryRow, ImportCommit, ImportPreview, TickerReport, WatchlistRow } from "../types";

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

export async function fetchTickerReport(ticker: string): Promise<TickerReport> {
  const response = await fetch(`/api/tickers/${encodeURIComponent(ticker)}`);
  if (!response.ok) throw new Error("Failed to load ticker report");
  return response.json();
}

export async function fetchTickerHistory(ticker: string): Promise<HistoryRow[]> {
  const response = await fetch(`/api/tickers/${encodeURIComponent(ticker)}/history`);
  if (!response.ok) throw new Error("Failed to load ticker history");
  return response.json();
}
