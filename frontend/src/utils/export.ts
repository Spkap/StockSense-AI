import type { AnalysisData } from '../types/api';

/**
 * Export analysis data as JSON file
 */
export function exportAsJSON(data: AnalysisData): void {
  const exportData = {
    ticker: data.ticker,
    timestamp: data.timestamp,
    summary: data.summary,
    sentiment_report: data.sentiment_report,
    headlines: data.headlines,
    headlines_count: data.headlines_count,
    price_data: data.price_data,
    reasoning_steps: data.reasoning_steps,
    tools_used: data.tools_used,
    iterations: data.iterations,
    source: data.source,
    agent_type: data.agent_type,
    exported_at: new Date().toISOString(),
  };

  const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
    type: 'application/json' 
  });
  
  downloadBlob(blob, `stocksense-${data.ticker}-${formatDate(data.timestamp)}.json`);
}

/**
 * Export analysis data as CSV file
 */
export function exportAsCSV(data: AnalysisData): void {
  const rows: string[][] = [];
  
  // Header info
  rows.push(['StockSense Analysis Export']);
  rows.push(['Ticker', data.ticker]);
  rows.push(['Timestamp', data.timestamp]);
  rows.push(['Source', data.source]);
  rows.push(['']);
  
  // Summary
  rows.push(['Summary']);
  rows.push([escapeCSV(data.summary)]);
  rows.push(['']);
  
  // Sentiment
  rows.push(['Sentiment Report']);
  rows.push([escapeCSV(data.sentiment_report)]);
  rows.push(['']);
  
  // Headlines
  rows.push(['Headlines']);
  (data.headlines || []).forEach((headline, i) => {
    rows.push([`${i + 1}`, escapeCSV(headline)]);
  });
  rows.push(['']);
  
  // Price Data
  rows.push(['Price Data']);
  rows.push(['Date', 'Open', 'High', 'Low', 'Close', 'Volume']);
  (data.price_data || []).forEach((point) => {
    rows.push([
      point.Date,
      point.Open?.toString() ?? '',
      point.High?.toString() ?? '',
      point.Low?.toString() ?? '',
      point.Close?.toString() ?? '',
      point.Volume?.toString() ?? '',
    ]);
  });
  rows.push(['']);
  
  // Reasoning Steps
  rows.push(['Reasoning Steps']);
  (data.reasoning_steps || []).forEach((step, i) => {
    rows.push([`${i + 1}`, escapeCSV(step)]);
  });
  rows.push(['']);
  
  // Tools Used
  rows.push(['Tools Used']);
  rows.push([(data.tools_used || []).join(', ')]);
  
  const csvContent = rows.map(row => row.join(',')).join('\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  
  downloadBlob(blob, `stocksense-${data.ticker}-${formatDate(data.timestamp)}.csv`);
}

/**
 * Helper to escape CSV values
 */
function escapeCSV(value: string): string {
  if (!value) return '';
  // Escape quotes and wrap in quotes if contains comma, newline, or quote
  const escaped = value.replace(/"/g, '""');
  if (escaped.includes(',') || escaped.includes('\n') || escaped.includes('"')) {
    return `"${escaped}"`;
  }
  return escaped;
}

/**
 * Helper to format date for filename
 */
function formatDate(timestamp: string): string {
  try {
    const date = new Date(timestamp);
    return date.toISOString().split('T')[0];
  } catch {
    return 'unknown';
  }
}

/**
 * Helper to trigger download
 */
function downloadBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
