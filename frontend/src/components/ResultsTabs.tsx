import { useState } from 'react';
import { Card, CardContent, CardHeader } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { RefreshCw, Clock, AlertTriangle, BookOpen, FileJson, FileSpreadsheet, Scale, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import type { AnalysisData, PriceDataPoint } from '../types/api';
import SentimentCard from './SentimentCard';
import SkepticCard from './SkepticCard';
import FundamentalsCard from './FundamentalsCard';
import EmptyState from './EmptyState';
import ThesisEditor from './ThesisEditor';
import DebateView from './DebateView';
import { useThesisForTicker } from '../api/theses';
import { useStreamingDebate } from '../hooks/useStreamingDebate';
import { exportAsJSON, exportAsCSV } from '../utils/export';
import { cn } from '../utils/cn';

interface ResultsTabsProps {
  result: AnalysisData;
  onRefresh?: () => void;
  isRefreshing?: boolean;
}

/**
 * Format cache age as human-readable string
 */
function formatCacheAge(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return 'Unknown';
  if (hours === 0) return 'Just now';
  if (hours < 1) return `${Math.round(hours * 60)}m ago`;
  if (hours < 24) return `${Math.round(hours)}h ago`;
  if (hours < 48) return 'Yesterday';
  return `${Math.round(hours / 24)}d ago`;
}

/**
 * Clean and fix malformed markdown from LLM output
 * - Fixes unclosed bold (**) and italic (*) markers
 * - Removes orphaned markers at end of truncated text
 */
function cleanMarkdown(text: string): string {
  if (!text) return '';
  
  let cleaned = text;
  
  // Fix truncated bold markers (e.g., "**Sent..." -> "Sent...")
  // Remove single ** at end of line that isn't closed
  cleaned = cleaned.replace(/\*\*([^*\n]{1,20})\.{3}$/gm, '$1...');
  cleaned = cleaned.replace(/\*\*([^*\n]{1,20})$/gm, '$1');
  
  // Fix unclosed bold markers within text
  // Count ** pairs and close any unclosed ones
  const boldMatches = cleaned.match(/\*\*/g) || [];
  if (boldMatches.length % 2 !== 0) {
    // Odd number of **, remove the last orphaned one or close it
    cleaned = cleaned.replace(/\*\*(?!.*\*\*)/, '');
  }
  
  // Fix unclosed italic markers (single *)
  // This is trickier because * is used in lists
  // Only fix * that appears to be for emphasis (preceded by space or start)
  const lines = cleaned.split('\n');
  cleaned = lines.map(line => {
    // Skip lines that start with * (list items)
    if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
      return line;
    }
    // Count non-list * and close if odd
    const italicMatches = line.match(/(?<!\*)\*(?!\*)/g) || [];
    if (italicMatches.length % 2 !== 0) {
      // Remove orphaned single *
      line = line.replace(/(?<!\*)\*(?!\*)(?!.*(?<!\*)\*(?!\*))/, '');
    }
    return line;
  }).join('\n');
  
  return cleaned;
}

const ResultsTabs = ({ result, onRefresh, isRefreshing }: ResultsTabsProps) => {
  const { data: thesisData } = useThesisForTicker(result.ticker);
  const [showThesisEditor, setShowThesisEditor] = useState(false);
  
  // Phase 3: Streaming Debate
  const {
    isStreaming: debateLoading,
    progress: debateProgress,
    phases: debatePhases,
    error: debateError,
    finalData: debateData,
    startDebate,
    reset: resetDebate,
  } = useStreamingDebate();
  
  const existingThesis = thesisData?.theses?.[0] || null;
  const hasThesis = !!existingThesis;

  // Start streaming debate when tab is clicked
  const fetchDebateAnalysis = () => {
    if (debateData) return; // Already loaded
    startDebate(result.ticker);
  };

  // Transform chart data
  const chartData = (result.price_data || []).map((d: PriceDataPoint, index: number) => ({
    date: d.Date?.split('T')[0] || `Day ${index + 1}`,
    close: d.Close,
  }));

  const hasChartData = chartData.length > 1;
  
  let priceChange: string | null = null;
  let isPositive = false;

  if (hasChartData) {
    const firstClose = chartData[0].close;
    const lastClose = chartData[chartData.length - 1].close;

    if (firstClose !== null && lastClose !== null && firstClose !== 0) {
      const change = ((lastClose - firstClose) / firstClose) * 100;
      priceChange = change.toFixed(2);
      isPositive = change >= 0;
    }
  }

  // Determine if cache is stale (>24 hours)
  const cacheAgeHours = result.cache_age_hours;
  const isStale = cacheAgeHours !== null && cacheAgeHours !== undefined && cacheAgeHours > 24;
  const isCached = result.source === 'cache';

  return (
    <>
    <Card className="overflow-hidden border-border bg-card shadow-sm">
      {/* Thesis Context Banner */}
      {hasThesis && (
        <div className="bg-primary/10 border-b border-primary/20 px-4 py-3 md:px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <BookOpen className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-primary">
                You have a thesis for this asset
              </span>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowThesisEditor(true)}
              className="text-primary hover:text-primary"
            >
              View / Edit
            </Button>
          </div>
        </div>
      )}
      
      {/* Header */}
      <div className="border-b border-border bg-muted/50 p-4 md:p-6">
        <div className="mb-4 flex flex-col gap-3 sm:mb-6 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 sm:gap-3">
            {/* Track Thesis Button */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowThesisEditor(true)}
              className={cn(
                "gap-1.5",
                hasThesis && "border-primary/50 text-primary"
              )}
            >
              <BookOpen className="h-4 w-4" />
              {hasThesis ? 'Thesis' : 'Track'}
            </Button>
            
            <h2 className="text-2xl font-bold tracking-tight text-foreground sm:text-3xl">
              {result.ticker}
            </h2>
            {priceChange && (
              <Badge 
                variant={isPositive ? "default" : "destructive"} 
                className={cn(
                  "text-sm", 
                  isPositive ? "bg-success hover:bg-success/90 text-success-foreground" : ""
                )}
              >
                {isPositive ? '+' : ''}{priceChange}%
              </Badge>
            )}
          </div>
          
          {/* Cache Status & Refresh */}
          <div className="flex items-center gap-2">
            {/* Cache Age */}
            {isCached && cacheAgeHours !== undefined && (
              <div className={cn(
                "flex items-center gap-1.5 text-xs",
                isStale ? "text-warning" : "text-muted-foreground"
              )}>
                {isStale ? (
                  <AlertTriangle className="h-3.5 w-3.5" />
                ) : (
                  <Clock className="h-3.5 w-3.5" />
                )}
                <span>Updated {formatCacheAge(cacheAgeHours)}</span>
              </div>
            )}
            
            {/* Source Badge */}
            <Badge 
              variant="secondary" 
              className={cn(
                "bg-background text-muted-foreground border-border",
                isStale && "border-warning/50 text-warning"
              )}
            >
              {isCached ? (isStale ? 'Stale' : 'Cached') : 'Fresh'}
            </Badge>
            
            {/* Refresh Button */}
            {onRefresh && (
              <Button
                variant="outline"
                size="sm"
                onClick={onRefresh}
                disabled={isRefreshing}
                className="gap-1.5"
              >
                <RefreshCw className={cn("h-3.5 w-3.5", isRefreshing && "animate-spin")} />
                Refresh
              </Button>
            )}
            
            {/* Export Buttons */}
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => exportAsJSON(result)}
                className="h-8 w-8"
                title="Export as JSON"
              >
                <FileJson className="h-4 w-4" />
              </Button>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => exportAsCSV(result)}
                className="h-8 w-8"
                title="Export as CSV"
              >
                <FileSpreadsheet className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        <Tabs defaultValue="overview" className="w-full">
          <TabsList className="grid w-full grid-cols-6 lg:w-[600px]">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="chart">Chart</TabsTrigger>
            <TabsTrigger value="fundamentals">Fund.</TabsTrigger>
            <TabsTrigger value="debate" onClick={fetchDebateAnalysis}>
              <Scale className="h-3.5 w-3.5 mr-1" />
              Debate
            </TabsTrigger>
            <TabsTrigger value="news">News</TabsTrigger>
            <TabsTrigger value="agent">Logic</TabsTrigger>
          </TabsList>

          <div className="mt-4 md:mt-6">
             <TabsContent value="overview" className="space-y-4">
                {/* Primary vs Skeptic Analysis - Side by Side */}
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                   <div className="col-span-1">
                      <SentimentCard data={result} report={result.sentiment_report || ''} />
                   </div>
                   <div className="col-span-1">
                      <SkepticCard data={result} />
                   </div>
                </div>

                {/* AI Summary */}
                <Card className="bg-accent/20 border-none">
                   <CardHeader>
                      <h3 className="text-lg font-semibold">AI Summary</h3>
                   </CardHeader>
                   <CardContent>
                      <div className="prose prose-sm dark:prose-invert max-w-none text-muted-foreground
                        prose-headings:text-foreground prose-headings:font-semibold prose-headings:mb-2 prose-headings:mt-4
                        prose-h2:text-base prose-h3:text-sm
                        prose-p:leading-relaxed prose-p:mb-3
                        prose-strong:text-foreground prose-strong:font-semibold
                        prose-ul:list-disc prose-ul:ml-4 prose-ul:mb-3
                        prose-li:mb-1">
                        <ReactMarkdown>{cleanMarkdown(result.summary)}</ReactMarkdown>
                      </div>
                   </CardContent>
                </Card>

                {/* Key Themes */}
                {result.key_themes && result.key_themes.length > 0 && (
                  <Card className="border-border">
                    <CardHeader className="pb-3">
                      <h3 className="text-lg font-semibold flex items-center gap-2">
                        Key Themes
                      </h3>
                    </CardHeader>
                    <CardContent>
                      <div className="flex flex-wrap gap-2">
                        {result.key_themes.map((theme, index) => (
                          <Badge
                            key={index}
                            variant={
                              theme.sentiment_direction === 'Bullish' ? 'default' :
                              theme.sentiment_direction === 'Bearish' ? 'destructive' : 'secondary'
                            }
                            className={cn(
                              "text-sm py-1 px-3",
                              theme.sentiment_direction === 'Bullish' && "bg-success/20 text-success hover:bg-success/30",
                              theme.sentiment_direction === 'Mixed' && "bg-warning/20 text-warning hover:bg-warning/30"
                            )}
                          >
                            {theme.theme} ({theme.headline_count})
                          </Badge>
                        ))}
                      </div>
                      {result.key_themes.length > 0 && result.key_themes[0].summary && (
                        <p className="text-sm text-muted-foreground mt-3">
                          {result.key_themes[0].summary}
                        </p>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Potential Impact & Information Gaps */}
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {/* Potential Impact */}
                  {result.potential_impact && result.potential_impact !== 'Uncertain' && (
                    <Card className="border-border">
                      <CardContent className="pt-4">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">Potential Impact</p>
                        <Badge
                          variant="outline"
                          className={cn(
                            "text-sm",
                            result.potential_impact.includes('Positive') && "border-success text-success",
                            result.potential_impact.includes('Negative') && "border-destructive text-destructive"
                          )}
                        >
                          {result.potential_impact}
                        </Badge>
                      </CardContent>
                    </Card>
                  )}

                  {/* Information Gaps */}
                  {result.information_gaps && result.information_gaps.length > 0 && (
                    <Card className="border-border">
                      <CardContent className="pt-4">
                        <p className="text-xs text-muted-foreground uppercase tracking-wider mb-2">What We Don't Know</p>
                        <ul className="space-y-1">
                          {result.information_gaps.slice(0, 3).map((gap, index) => (
                            <li key={index} className="text-sm text-muted-foreground flex items-start gap-2">
                              <span className="text-warning">?</span>
                              <span>{gap}</span>
                            </li>
                          ))}
                        </ul>
                      </CardContent>
                    </Card>
                  )}
                </div>
             </TabsContent>

             <TabsContent value="chart" className="min-h-[300px] md:min-h-[400px]">
                {hasChartData ? (
                   <div className="h-[300px] w-full md:h-[400px]">
                      <ResponsiveContainer>
                         <AreaChart data={chartData}>
                            <defs>
                               <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                                  <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3}/>
                                  <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                               </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" vertical={false} />
                            <XAxis 
                               dataKey="date" 
                               tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                               tickLine={false}
                               axisLine={{ stroke: 'hsl(var(--border))' }}
                            />
                            <YAxis 
                               tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 11 }}
                               tickLine={false}
                               axisLine={{ stroke: 'hsl(var(--border))' }}
                               tickFormatter={(value) => `$${value}`}
                               domain={['auto', 'auto']}
                            />
                            <Tooltip 
                               contentStyle={{ 
                                  backgroundColor: 'hsl(var(--card))', 
                                  borderRadius: '0.5rem', 
                                  borderColor: 'hsl(var(--border))', 
                                  color: 'hsl(var(--foreground))'
                               }}
                               itemStyle={{ color: 'hsl(var(--primary))', fontWeight: 600 }}
                            />
                            <Area 
                               type="monotone" 
                               dataKey="close" 
                               stroke="hsl(var(--primary))"
                               strokeWidth={2}
                               fillOpacity={1}
                               fill="url(#colorClose)"
                            />
                         </AreaChart>
                      </ResponsiveContainer>
                   </div>
                ) : (
                   <div className="py-12 md:py-20">
                      <EmptyState type="no-chart" />
                   </div>
                )}
             </TabsContent>

             <TabsContent value="fundamentals">
               <Card>
                 <CardContent className="pt-6">
                   {result.fundamental_data ? (
                     <FundamentalsCard data={result.fundamental_data} />
                   ) : (
                     <div className="py-12 md:py-20 text-center">
                       <EmptyState type="no-data" />
                       <p className="mt-4 text-muted-foreground">Fundamental data not available for this analysis.</p>
                     </div>
                   )}
                 </CardContent>
               </Card>
             </TabsContent>

             <TabsContent value="news">
                <Card>
                   <CardContent className="pt-6">
                      {(result.headlines || []).length > 0 ? (
                        <ul className="space-y-3">
                           {result.headlines.map((headline, index) => (
                              <li key={index} className="rounded-lg border border-border bg-card p-3 transition-colors hover:bg-accent hover:text-accent-foreground md:p-4">
                                 <p className="text-sm font-medium text-foreground md:text-base">{headline}</p>
                              </li>
                           ))}
                        </ul>
                      ) : (
                        <EmptyState type="no-news" />
                      )}
                   </CardContent>
                </Card>
             </TabsContent>

             <TabsContent value="agent">
                <div className="rounded-xl border border-dashed border-border bg-card p-4 md:p-6">
                   <div className="mb-4 flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
                      <Badge variant="outline">Reasoning</Badge>
                      <span>{result.iterations} iterations</span>
                   </div>
                   <ol className="relative ml-3 space-y-4 border-l border-border pl-6">
                      {(result.reasoning_steps || []).map((step, index) => (
                         <li key={index} className="relative">
                            <span className="absolute -left-[30px] flex h-6 w-6 items-center justify-center rounded-full bg-muted text-xs font-bold text-muted-foreground ring-4 ring-background">
                               {index + 1}
                            </span>
                            <p className="text-sm text-muted-foreground">{step}</p>
                         </li>
                      ))}
                   </ol>
                   <div className="mt-6 border-t border-border pt-6">
                      <p className="mb-3 text-sm font-medium text-muted-foreground">Tools Used</p>
                      <div className="flex flex-wrap gap-2">
                         {(result.tools_used || []).map(tool => (
                            <Badge key={tool} variant="secondary">
                               {tool}
                            </Badge>
                         ))}
                      </div>
                   </div>
                   </div>
               </TabsContent>

               {/* Phase 3: Debate Tab */}
               <TabsContent value="debate" className="space-y-4">
                 {debateLoading && (
                   <Card className="p-8">
                     <div className="flex flex-col items-center justify-center gap-6">
                       <div className="flex items-center gap-3">
                         <Loader2 className="h-8 w-8 animate-spin text-primary" />
                         <div className="text-left">
                           <p className="font-semibold">Running Adversarial Analysis...</p>
                           <p className="text-sm text-muted-foreground">
                             Progress: {Math.round(debateProgress * 100)}%
                           </p>
                         </div>
                       </div>
                       
                       {/* Progress bar */}
                       <div className="w-full max-w-md">
                         <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
                           <div 
                             className="h-full bg-primary transition-all duration-500 ease-out"
                             style={{ width: `${debateProgress * 100}%` }}
                           />
                         </div>
                       </div>
                       
                       {/* Phase indicators */}
                       <div className="w-full max-w-lg space-y-2">
                         {debatePhases.map((phase) => (
                           <div 
                             key={phase.id}
                             className={cn(
                               "flex items-center gap-3 px-3 py-2 rounded-lg transition-all",
                               phase.status === 'active' && "bg-primary/10",
                               phase.status === 'complete' && "opacity-60"
                             )}
                           >
                             {phase.status === 'complete' && (
                               <div className="h-4 w-4 rounded-full bg-success flex items-center justify-center">
                                 <span className="text-[10px] text-white">✓</span>
                               </div>
                             )}
                             {phase.status === 'active' && (
                               <Loader2 className="h-4 w-4 animate-spin text-primary" />
                             )}
                             {phase.status === 'pending' && (
                               <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/30" />
                             )}
                             <span className={cn(
                               "text-sm",
                               phase.status === 'active' && "font-medium text-primary",
                               phase.status === 'pending' && "text-muted-foreground"
                             )}>
                               {phase.label}
                             </span>
                             {phase.message && phase.status === 'active' && (
                               <span className="ml-auto text-xs text-muted-foreground">
                                 {phase.message}
                               </span>
                             )}
                           </div>
                         ))}
                       </div>
                       
                       <Button onClick={resetDebate} variant="ghost" size="sm" className="mt-2">
                         Cancel
                       </Button>
                     </div>
                   </Card>
                 )}
                 
                 {debateError && !debateLoading && (
                   <Card className="p-8 border-destructive/50 bg-destructive/5">
                     <div className="flex flex-col items-center justify-center gap-4">
                       <AlertTriangle className="h-8 w-8 text-destructive" />
                       <div className="text-center">
                         <p className="font-semibold text-destructive">Debate Failed</p>
                         <p className="text-sm text-muted-foreground">{debateError}</p>
                       </div>
                       <Button onClick={() => { resetDebate(); fetchDebateAnalysis(); }} variant="outline" size="sm">
                         Try Again
                       </Button>
                     </div>
                   </Card>
                 )}
                 
                 {debateData && !debateLoading && (
                   <DebateView data={debateData} />
                 )}
                 
                 {!debateData && !debateLoading && !debateError && (
                   <Card className="p-8">
                     <div className="flex flex-col items-center justify-center gap-4">
                       <Scale className="h-8 w-8 text-muted-foreground" />
                       <div className="text-center">
                         <p className="font-semibold">Click to Load Debate Analysis</p>
                         <p className="text-sm text-muted-foreground">
                           Run an adversarial analysis with Bull and Bear AI agents.
                         </p>
                       </div>
                       <Button onClick={fetchDebateAnalysis} variant="default" size="sm">
                         <Scale className="h-4 w-4 mr-2" />
                         Start Debate
                       </Button>
                     </div>
                   </Card>
                 )}
               </TabsContent>
          </div>
        </Tabs>
      </div>
    </Card>
    
    {/* Thesis Editor Modal */}
    <ThesisEditor
      isOpen={showThesisEditor}
      onClose={() => setShowThesisEditor(false)}
      ticker={result.ticker}
      existingThesis={existingThesis}
    />
    </>
  );
};

export default ResultsTabs;
