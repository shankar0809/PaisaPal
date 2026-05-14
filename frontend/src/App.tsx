import { BarChart3, FileUp, History } from "lucide-react";
import { useEffect, useState } from "react";
import { ImportPage } from "./pages/ImportPage";

type Route = "dashboard" | "import" | "history";

function routeFromHash(): Route {
  const hash = window.location.hash.replace("#/", "");
  if (hash === "import" || hash === "history") return hash;
  return "dashboard";
}

export function App() {
  const [route, setRoute] = useState<Route>(routeFromHash);

  useEffect(() => {
    const onHashChange = () => setRoute(routeFromHash());
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  return (
    <div className="appShell">
      <aside className="sidebar">
        <div className="brand">PaisaPal</div>
        <nav className="nav">
          <a className={route === "dashboard" ? "active" : ""} href="#/">
            <BarChart3 size={18} />
            Dashboard
          </a>
          <a className={route === "import" ? "active" : ""} href="#/import">
            <FileUp size={18} />
            Import
          </a>
          <a className={route === "history" ? "active" : ""} href="#/history">
            <History size={18} />
            History
          </a>
        </nav>
      </aside>
      <main className="content">
        {route === "dashboard" && (
          <section className="page">
            <header className="pageHeader">
              <h1>Dashboard</h1>
            </header>
            <div className="panel emptyState">Import a CSV watchlist to start analyzing tickers.</div>
          </section>
        )}
        {route === "import" && <ImportPage />}
        {route === "history" && (
          <section className="page">
            <header className="pageHeader">
              <h1>History</h1>
            </header>
            <div className="panel emptyState">Select a ticker to review prior snapshots.</div>
          </section>
        )}
      </main>
    </div>
  );
}
