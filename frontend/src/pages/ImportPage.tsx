import { CsvImportPanel } from "../components/CsvImportPanel";

export function ImportPage() {
  return (
    <main className="page">
      <header className="pageHeader">
        <h1>CSV Import</h1>
      </header>
      <CsvImportPanel />
    </main>
  );
}
