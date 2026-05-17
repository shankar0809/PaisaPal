export type CsvIssue = {
  row_number: number;
  column: string;
  message: string;
};

export type ImportPreview = {
  preview_id: string;
  valid_count: number;
  error_count: number;
  warning_count: number;
  errors: CsvIssue[];
  warnings: CsvIssue[];
  rows: Array<{
    row_number: number;
    ticker: string;
    current_price: number;
  }>;
};

export type ImportCommit = {
  batch_id: number;
  imported_count: number;
};

export type WatchlistRow = {
  id: number;
  ticker: string;
  current_price: number;
  final_decision: string;
  confidence: string;
  technical_rating: string;
  fundamental_rating: string;
  earnings_rating?: string;
  sentiment_rating: string;
  options_flow_rating: string;
  risk_reward: number | null;
  created_at: string;
};

export type SourceSummaryItem = {
  provider: string;
  retrieved_at: string;
  status: string;
  label: string;
  url: string | null;
  warnings: string[];
};

export type SourceCoverageItem = {
  section: string;
  status: "covered" | "partial" | "missing";
  matched_sources: Array<{
    provider: string;
    label: string;
    status: string;
    url: string | null;
  }>;
  warnings: string[];
};

export type TickerReport = {
  ticker: string;
  report: {
    ticker?: string;
    company_name?: string;
    current_price?: number;
    final_classification?: string;
    confidence?: string;
    technical_rating?: string;
    vcp_rating?: string;
    fundamental_rating?: string;
    earnings_rating?: string;
    sentiment_rating?: string;
    options_flow_rating?: string;
    vcp_summary?: {
      ticker: string;
      vcp_score: number;
      vcp_stage: string;
      tech_output: string;
      vcp_rating: string;
    };
    data_warnings?: string[];
    source_summary?: SourceSummaryItem[];
    analysis_steps?: Array<{
      section: string;
      status: "covered" | "partial" | "missing";
      summary: string;
      results: Record<string, unknown>;
      sources: Array<{
        provider: string;
        source_type: string;
        status: string;
        label: string;
      }>;
      warnings: string[];
    }>;
    input?: Record<string, unknown>;
    analysis?: Record<string, unknown>;
  };
  markdown_report: string;
  created_at: string;
  source_coverage: SourceCoverageItem[];
};

export type HistoryRow = {
  id: number;
  ticker: string;
  final_decision: string;
  confidence: string;
  risk_reward: number | null;
  created_at: string;
};

export type AnalysisJob = {
  id: number;
  ticker: string;
  status: string;
  error_message: string | null;
};

export type AnalysisRun = {
  id: number;
  status: string;
  tickers: string[];
  account_size: number;
  risk_percent: number;
  max_dollar_risk: number | null;
  notes: string;
  created_at: string;
  jobs: AnalysisJob[];
};

export type ProviderStatus = {
  provider: string;
  configured: boolean;
  role: string;
  required_for_live: boolean;
  live_ready: boolean;
  message: string;
};
