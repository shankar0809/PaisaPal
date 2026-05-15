import { BarChart3, FileUp, History } from "lucide-react";
import { useEffect, useState } from "react";
import { DashboardPage } from "./pages/DashboardPage";
import { HistoryPage } from "./pages/HistoryPage";
import { ImportPage } from "./pages/ImportPage";
import { TickerDetailPage } from "./pages/TickerDetailPage";

type Route =
  | { name: "dashboard" }
  | { name: "import" }
  | { name: "history"; ticker?: string }
  | { name: "ticker"; ticker: string };

function routeFromHash(): Route {
  const hash = window.location.hash.replace("#/", "");
  if (hash === "import") return { name: "import" };
  if (hash.startsWith("history/")) return { name: "history", ticker: hash.split("/")[1] };
  if (hash === "history") return { name: "history" };
  if (hash.startsWith("ticker/")) return { name: "ticker", ticker: hash.split("/")[1] };
  return { name: "dashboard" };
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
          <a className={route.name === "dashboard" ? "active" : ""} href="#/">
            <BarChart3 size={18} />
            Dashboard
          </a>
          <a className={route.name === "import" ? "active" : ""} href="#/import">
            <FileUp size={18} />
            Import
          </a>
          <a className={route.name === "history" ? "active" : ""} href="#/history">
            <History size={18} />
            History
          </a>
        </nav>
      </aside>
      <main className="content">
        {route.name === "dashboard" && <DashboardPage />}
        {route.name === "import" && <ImportPage />}
        {route.name === "history" && <HistoryPage ticker={route.ticker} />}
        {route.name === "ticker" && <TickerDetailPage ticker={route.ticker} />}
      </main>
    </div>
  );
}
