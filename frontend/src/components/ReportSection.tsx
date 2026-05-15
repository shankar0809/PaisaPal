import { ReactNode } from "react";

type ReportSectionProps = {
  title: string;
  children: ReactNode;
};

export function ReportSection({ title, children }: ReportSectionProps) {
  return (
    <section className="panel reportSection">
      <h2>{title}</h2>
      {children}
    </section>
  );
}
