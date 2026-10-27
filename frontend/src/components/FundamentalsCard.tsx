import { useState } from 'react';
import { cn } from '../utils/cn';

interface FundamentalsCardProps {
  data: {
    info?: Record<string, any>;
    income_statement?: Record<string, any>;
    balance_sheet?: Record<string, any>;
    cash_flow?: Record<string, any>;
  };
}

const KeyStat = ({ label, value, format = 'text' }: { label: string; value: any; format?: 'text' | 'currency' | 'percent' | 'number' }) => {
  if (value === undefined || value === null) return null;

  let displayValue = value;
  if (format === 'currency') {
    displayValue = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', notation: 'compact' }).format(value);
  } else if (format === 'percent') {
    displayValue = new Intl.NumberFormat('en-US', { style: 'percent', maximumFractionDigits: 2 }).format(value);
  } else if (format === 'number') {
    displayValue = new Intl.NumberFormat('en-US', { maximumFractionDigits: 2 }).format(value);
  }

  return (
    <div className="flex flex-col gap-1 p-3 border border-border-base bg-surface-1 rounded-sm">
      <span className="text-micro font-mono text-txt-muted uppercase tracking-widest font-bold">{label}</span>
      <span className="text-sm font-mono font-bold text-txt-primary tracking-widest">{displayValue}</span>
    </div>
  );
};

const FinancialTable = ({ data, title }: { data?: Record<string, any>; title: string }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="p-8 text-center text-micro font-mono text-txt-muted uppercase tracking-widest border border-dashed border-border-strong opacity-70 bg-surface-1 rounded-sm">
        --- NO_{title.toUpperCase().replace(' ', '_')}_DATA_AVAILABLE ---
      </div>
    );
  }

  // Get dates (columns) and metrics (rows)
  const dates = Object.keys(data).sort().reverse();
  const priority = ['Total Revenue', 'Gross Profit', 'Operating Income', 'Net Income', 'Basic EPS', 'Diluted EPS', 'Total Assets', 'Total Liabilities Net Minority Interest', 'Stockholders Equity', 'Operating Cash Flow', 'Investing Cash Flow', 'Financing Cash Flow', 'Free Cash Flow'];
  const metrics = [...new Set(dates.slice(0, 4).flatMap(date => Object.keys(data[date] || {})))].sort((a, b) => {
    const rankA = priority.indexOf(a), rankB = priority.indexOf(b);
    return (rankA < 0 ? priority.length : rankA) - (rankB < 0 ? priority.length : rankB) || a.localeCompare(b);
  });

  return (
    <div role="region" aria-label={`${title} data, scroll horizontally to compare years`} tabIndex={0} className="border border-border-base bg-surface-1 rounded-sm overflow-x-auto focus-visible:outline-accent">
      <table className="w-full min-w-[680px] table-fixed text-left border-collapse font-mono">
        <colgroup><col className="w-[160px] sm:w-[240px]" />{dates.slice(0, 4).map(date => <col key={date} className="w-[130px]" />)}</colgroup>
        <thead>
          <tr className="bg-surface-2/50 border-b border-border-base">
            <th className="sticky left-0 z-20 bg-surface-2 p-3 font-bold text-txt-primary text-micro">Metric</th>
            {dates.slice(0, 4).map(date => (
              <th key={date} className="p-2 px-3 font-bold text-txt-primary uppercase tracking-widest text-micro text-right border-l border-border-base/50">
                {date}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {metrics.map((metric, idx) => (
            <tr key={metric} className={cn("border-b border-border-base/30 hover:bg-surface-2 transition-colors", idx % 2 === 0 ? "bg-transparent" : "bg-surface-1")}>
              <td className="sticky left-0 z-10 bg-surface-1 p-3 text-txt-secondary whitespace-normal break-words text-sm tracking-normal">{metric}</td>
              {dates.slice(0, 4).map(date => {
                const val = data[date]?.[metric];
                let displayVal = val;
                 if (typeof val === 'number') {
                    displayVal = new Intl.NumberFormat('en-US', { 
                        notation: 'compact', 
                        maximumFractionDigits: 2 
                    }).format(val);
                }
                return (
                  <td key={`${date}-${metric}`} className="p-3 text-right whitespace-nowrap border-l border-border-base/50 text-txt-primary text-sm tracking-normal">
                    {displayVal ?? '—'}
                  </td>
                );
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default function FundamentalsCard({ data }: FundamentalsCardProps) {
  const info = data.info || {};
  const [activeTab, setActiveTab] = useState<'income' | 'balance' | 'cashflow'>('income');

  const tabs = [
    { id: 'income', label: 'Income statement' },
    { id: 'balance', label: 'Balance sheet' },
    { id: 'cashflow', label: 'Cash flow' },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Key Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <KeyStat label="Market Cap" value={info.market_cap} format="currency" />
        <KeyStat label="P/E Ratio" value={info.pe_ratio} format="number" />
        <KeyStat label="Forward P/E" value={info.forward_pe} format="number" />
        <KeyStat label="Rev Growth" value={info.revenue_growth} format="percent" />
        <KeyStat label="Profit Margin" value={info.profit_margins} format="percent" />
        <KeyStat label="Price/Book" value={info.price_to_book} format="number" />
        <KeyStat label="Debt/Equity" value={info.debt_to_equity} format="number" />
        <KeyStat label="Target High" value={info.target_high} format="currency" />
        <KeyStat label="Analyst score" value={info.recommendation_mean} format="number" />
      </div>

<p className="text-sm text-txt-secondary">Annual statements · newest reporting periods first · large values abbreviated as K, M, B or T. Missing values appear as —. Scroll tables horizontally to compare years.</p>
      {/* Financial Statements Custom Tabs */}
      <div className="flex flex-col gap-4">
        <div className="flex flex-wrap w-full border-b border-border-base/50 gap-2 pb-2">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                aria-pressed={isActive}
                onClick={() => setActiveTab(tab.id as 'income' | 'balance' | 'cashflow')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 font-mono text-micro tracking-wide transition-colors outline-none rounded-sm border shrink-0 font-bold",
                  isActive 
                    ? "text-txt-primary bg-surface-2 border-border-strong" 
                    : "text-txt-muted hover:text-txt-secondary bg-surface-1 border-border-base hover:bg-surface-2"
                )}
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        <div>
          {activeTab === 'income' && <FinancialTable data={data.income_statement} title="Income Statement" />}
          {activeTab === 'balance' && <FinancialTable data={data.balance_sheet} title="Balance Sheet" />}
          {activeTab === 'cashflow' && <FinancialTable data={data.cash_flow} title="Cash Flow" />}
        </div>
      </div>
    </div>
  );
}
