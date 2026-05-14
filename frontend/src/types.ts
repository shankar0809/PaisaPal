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
