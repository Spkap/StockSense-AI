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
      <span className="text-micro font-mono text-txt-muted uppercase tracking-widest font-bold">{label.replace(' ', '_')}</span>
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
  const metrics = Object.keys(data[dates[0]] || {});

  return (
    <div className="border border-border-base bg-surface-1 rounded-sm overflow-x-auto">
      <table className="w-full text-left border-collapse font-mono">
        <thead>
          <tr className="bg-surface-2/50 border-b border-border-base">
            <th className="p-2 px-3 font-bold text-txt-primary uppercase tracking-widest text-micro">METRIC_ID</th>
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
              <td className="p-2 px-3 text-txt-secondary whitespace-nowrap text-micro tracking-widest uppercase">{metric}</td>
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
                  <td key={`${date}-${metric}`} className="p-2 px-3 text-right whitespace-nowrap border-l border-border-base/50 text-txt-primary font-bold text-micro tracking-wider">
                    {displayVal ?? '-'}
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
    { id: 'income', label: 'INCOME_STATEMENT' },
    { id: 'balance', label: 'BALANCE_SHEET' },
    { id: 'cashflow', label: 'CASH_FLOW' },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Key Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-2">
        <KeyStat label="Market Cap" value={info.market_cap} format="currency" />
        <KeyStat label="P/E Ratio" value={info.pe_ratio} format="number" />
        <KeyStat label="Forward P/E" value={info.forward_pe} format="number" />
        <KeyStat label="Rev Growth" value={info.revenue_growth} format="percent" />
        <KeyStat label="Profit Margin" value={info.profit_margins} format="percent" />
        <KeyStat label="Price/Book" value={info.price_to_book} format="number" />
        <KeyStat label="Debt/Equity" value={info.debt_to_equity} format="number" />
        <KeyStat label="Target High" value={info.target_high} format="currency" />
        <KeyStat label="Analyst Rec" value={info.recommendation_mean} format="number" />
      </div>

      {/* Financial Statements Custom Tabs */}
      <div className="flex flex-col gap-4">
        <div className="flex w-full border-b border-border-base/50 gap-1 overflow-x-auto no-scrollbar pb-1">
          {tabs.map((tab) => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as 'income' | 'balance' | 'cashflow')}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 font-mono text-micro tracking-widest transition-colors outline-none rounded-sm border shrink-0 uppercase font-bold",
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
