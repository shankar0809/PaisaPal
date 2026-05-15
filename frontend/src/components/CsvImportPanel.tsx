import { ChangeEvent, useState } from "react";
import { commitImport, previewImport } from "../api/client";
import type { ImportPreview } from "../types";

export function CsvImportPanel() {
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [error, setError] = useState("");

  function onFileChange(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] ?? null);
    setPreview(null);
    setError("");
  }

  async function onPreview() {
    if (!file) return;
    try {
      setPreview(await previewImport(file));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import preview failed");
    }
  }

  async function onCommit() {
    if (!preview?.preview_id) return;
    try {
      await commitImport(preview.preview_id);
      window.location.hash = "#/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import commit failed");
    }
  }

  return (
    <section className="panel formPanel">
      <div className="field">
        <label htmlFor="watchlist-csv">Watchlist CSV</label>
        <input id="watchlist-csv" type="file" accept=".csv,text/csv" onChange={onFileChange} />
      </div>
      <div className="actions">
        <button type="button" onClick={onPreview} disabled={!file}>
          Preview
        </button>
        <button type="button" onClick={onCommit} disabled={!preview || preview.valid_count === 0}>
          Import valid rows
        </button>
      </div>
      {error && <p role="alert">{error}</p>}
      {preview && (
        <div className="previewGrid">
          <p>Valid rows: {preview.valid_count}</p>
          <p>Errors: {preview.error_count}</p>
          <p>Warnings: {preview.warning_count}</p>
          {preview.errors.length > 0 && (
            <table>
              <thead>
                <tr>
                  <th>Row</th>
                  <th>Column</th>
                  <th>Error</th>
                </tr>
              </thead>
              <tbody>
                {preview.errors.map((issue) => (
                  <tr key={`${issue.row_number}-${issue.column}-${issue.message}`}>
                    <td>{issue.row_number}</td>
                    <td>{issue.column}</td>
                    <td>{issue.message}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </section>
  );
}
