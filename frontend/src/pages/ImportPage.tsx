import { CsvImportPanel } from "../components/CsvImportPanel";

export function ImportPage() {
  return (
    <main className="page">
      <header className="pageHeader">
        <h1>CSV Import</h1>
        <a className="buttonLink" href="/api/sample-csv">
          Sample CSV
        </a>
      </header>
      <CsvImportPanel />
    </main>
  );
}
