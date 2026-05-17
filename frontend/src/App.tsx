import { BarChart3, History, Search } from "lucide-react";
import { useEffect, useState } from "react";
import { AnalyzePage } from "./pages/AnalyzePage";
import { DashboardPage } from "./pages/DashboardPage";
import { HistoryPage } from "./pages/HistoryPage";
import { RunProgressPage } from "./pages/RunProgressPage";
import { TickerDetailPage } from "./pages/TickerDetailPage";

type Route =
  | { name: "dashboard" }
  | { name: "analyze" }
  | { name: "run"; runId: number }
  | { name: "history" }
  | { name: "ticker"; ticker: string };

export function routeFromHash(hashValue = window.location.hash): Route {
  const hash = hashValue.replace(/^#\//, "");
  if (hash === "analyze") return { name: "analyze" };
  const runMatch = hash.match(/^runs\/([1-9]\d*)$/);
  if (runMatch) return { name: "run", runId: Number(runMatch[1]) };
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
          <a className={route.name === "analyze" ? "active" : ""} href="#/analyze">
            <Search size={18} />
            Analyze
          </a>
          <a className={route.name === "history" ? "active" : ""} href="#/history">
            <History size={18} />
            Status
          </a>
        </nav>
      </aside>
      <main className="content">
        {route.name === "dashboard" && <DashboardPage />}
        {route.name === "analyze" && <AnalyzePage />}
        {route.name === "run" && <RunProgressPage runId={route.runId} />}
        {route.name === "history" && <HistoryPage />}
        {route.name === "ticker" && <TickerDetailPage ticker={route.ticker} />}
      </main>
    </div>
  );
}
