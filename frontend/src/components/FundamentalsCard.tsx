import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';

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
    <div className="flex flex-col gap-1 p-3 rounded-lg border bg-card">
      <span className="text-xs text-muted-foreground uppercase tracking-wider font-semibold">{label}</span>
      <span className="text-lg font-bold">{displayValue}</span>
    </div>
  );
};

const FinancialTable = ({ data, title }: { data?: Record<string, any>; title: string }) => {
  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground italic">
        No {title} data available
      </div>
    );
  }

  // Get dates (columns) and metrics (rows)
  // Data structure is { "Date1": { "Metric1": val, ... }, "Date2": ... }
  const dates = Object.keys(data).sort().reverse();
  // Get all unique metrics from the first date to assume structure
  const metrics = Object.keys(data[dates[0]] || {});

  return (
    <div className="rounded-md border overflow-x-auto">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[200px]">Metric</TableHead>
            {dates.slice(0, 4).map(date => (
              <TableHead key={date} className="text-right">{date}</TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {metrics.map(metric => (
            <TableRow key={metric}>
              <TableCell className="font-medium whitespace-nowrap">{metric}</TableCell>
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
                  <TableCell key={`${date}-${metric}`} className="text-right whitespace-nowrap">
                    {displayVal ?? '-'}
                  </TableCell>
                );
              })}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default function FundamentalsCard({ data }: FundamentalsCardProps) {
  const info = data.info || {};

  return (
    <div className="space-y-6">
      {/* Key Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
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

      {/* Financial Statements Tabs */}
      <Tabs defaultValue="income" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="income">Income Statement</TabsTrigger>
          <TabsTrigger value="balance">Balance Sheet</TabsTrigger>
          <TabsTrigger value="cashflow">Cash Flow</TabsTrigger>
        </TabsList>
        <div className="mt-4">
          <TabsContent value="income">
            <FinancialTable data={data.income_statement} title="Income Statement" />
          </TabsContent>
          <TabsContent value="balance">
            <FinancialTable data={data.balance_sheet} title="Balance Sheet" />
          </TabsContent>
          <TabsContent value="cashflow">
            <FinancialTable data={data.cash_flow} title="Cash Flow" />
          </TabsContent>
        </div>
      </Tabs>
    </div>
  );
}
