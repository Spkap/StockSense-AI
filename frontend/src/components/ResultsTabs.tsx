import { useState } from 'react';
import { Card } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from './ui/tabs';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { RefreshCw, Clock, AlertTriangle, BookOpen, FileJson, FileSpreadsheet, Scale, Loader2, ArrowUpRight, Info } from 'lucide-react';
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

function formatCacheAge(hours: number | null | undefined): string {
  if (hours === null || hours === undefined) return 'Unknown';
  if (hours === 0) return 'Just now';
  if (hours < 1) return `${Math.round(hours * 60)}m ago`;
  if (hours < 24) return `${Math.round(hours)}h ago`;
  if (hours < 48) return 'Yesterday';
  return `${Math.round(hours / 24)}d ago`;
}

function cleanMarkdown(text: string): string {
  if (!text) return '';
  let cleaned = text;
  cleaned = cleaned.replace(/\*\*([^*\n]{1,20})\.{3}$/gm, '$1...');
  cleaned = cleaned.replace(/\*\*([^*\n]{1,20})$/gm, '$1');
  const boldMatches = cleaned.match(/\*\*/g) || [];
  if (boldMatches.length % 2 !== 0) {
    cleaned = cleaned.replace(/\*\*(?!.*\*\*)/, '');
  }
  const lines = cleaned.split('\n');
  cleaned = lines.map(line => {
    if (line.trim().startsWith('* ') || line.trim().startsWith('- ')) {
      return line;
    }
    const italicMatches = line.match(/(?<!\*)\*(?!\*)/g) || [];
    if (italicMatches.length % 2 !== 0) {
      line = line.replace(/(?<!\*)\*(?!\*)(?!.*(?<!\*)\*(?!\*))/, '');
    }
    return line;
  }).join('\n');
  return cleaned;
}

const ResultsTabs = ({ result, onRefresh, isRefreshing }: ResultsTabsProps) => {
  const { data: thesisData } = useThesisForTicker(result.ticker);
  const [showThesisEditor, setShowThesisEditor] = useState(false);
  
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

  const fetchDebateAnalysis = () => {
    if (debateData) return;
    startDebate(result.ticker);
  };

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

  const cacheAgeHours = result.cache_age_hours;
  const isStale = cacheAgeHours !== null && cacheAgeHours !== undefined && cacheAgeHours > 24;
  const isCached = result.source === 'cache';

  return (
    <>
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      
      {/* Header Section */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
           <div className="flex items-center gap-3">
             <h2 className="text-4xl font-bold tracking-tight text-foreground">
               {result.ticker}
             </h2>
             {priceChange && (
               <div className={cn(
                 "flex items-center gap-1 rounded-full px-2 py-0.5 text-sm font-medium",
                 isPositive
                  ? "bg-success/10 text-success"
                  : "bg-destructive/10 text-destructive"
               )}>
                 {isPositive ? <ArrowUpRight className="h-4 w-4" /> : <ArrowUpRight className="h-4 w-4 rotate-90" />}
                 <span>{isPositive ? '+' : ''}{priceChange}%</span>
               </div>
             )}
           </div>
           <p className="mt-1 text-sm text-muted-foreground">AI-Powered Market Analysis</p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
            {/* Thesis Button */}
            <Button
              variant={hasThesis ? "secondary" : "outline"}
              size="sm"
              onClick={() => setShowThesisEditor(true)}
              className={cn(
                "rounded-full px-4 h-8 text-xs font-medium",
                hasThesis && "bg-primary/10 text-primary hover:bg-primary/20"
              )}
            >
              <BookOpen className="mr-1.5 h-3.5 w-3.5" />
              {hasThesis ? 'View Thesis' : 'Track Thesis'}
            </Button>
            
            {/* Source Badge */}
            <div className={cn(
                "flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium border",
                isStale ? "border-warning/30 bg-warning/5 text-warning" : "border-border bg-background text-muted-foreground"
              )}>
              {isStale ? <AlertTriangle className="h-3 w-3" /> : <Clock className="h-3 w-3" />}
              <span>{isCached ? (isStale ? 'Stale Data' : 'Cached') : 'Live Data'}</span>
            </div>
            
            {/* Refresh */}
            {onRefresh && (
              <Button
                variant="ghost"
                size="icon"
                onClick={onRefresh}
                disabled={isRefreshing}
                className="h-8 w-8 rounded-full hover:bg-muted"
              >
                <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
              </Button>
            )}

             {/* Export */}
            <Button
               variant="ghost"
               size="icon"
               onClick={() => exportAsJSON(result)}
               className="h-8 w-8 rounded-full hover:bg-muted"
            >
               <FileJson className="h-4 w-4" />
            </Button>
        </div>
      </div>

      <Tabs defaultValue="overview" className="w-full">
        <div className="mb-6 overflow-x-auto pb-2 scrollbar-none">
          <TabsList className="inline-flex h-11 items-center justify-start rounded-full bg-muted/50 p-1 text-muted-foreground w-auto">
            {['Overview', 'Chart', 'Fundamentals', 'Debate', 'News', 'Logic'].map((tab) => (
               <TabsTrigger
                  key={tab}
                  value={tab.toLowerCase()}
                  onClick={tab === 'Debate' ? fetchDebateAnalysis : undefined}
                  className="rounded-full px-6 py-2 text-sm font-medium transition-all data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow-sm"
               >
                  {tab === 'Debate' && <Scale className="mr-2 h-4 w-4" />}
                  {tab}
               </TabsTrigger>
            ))}
          </TabsList>
        </div>

        <TabsContent value="overview" className="space-y-6 outline-none">
            {/* Summary Card */}
            <Card className="rounded-3xl border-none bg-secondary/30 p-6 md:p-8">
               <div className="flex items-center gap-2 mb-4">
                  <div className="h-2 w-2 rounded-full bg-primary animate-pulse" />
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Executive Summary</h3>
               </div>
               <div className="prose prose-lg dark:prose-invert max-w-none text-foreground leading-relaxed">
                  <ReactMarkdown>{cleanMarkdown(result.summary)}</ReactMarkdown>
               </div>
            </Card>

            {/* Bull/Bear Grid */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <SentimentCard data={result} report={result.sentiment_report || ''} />
                <SkepticCard data={result} />
            </div>

            {/* Themes */}
            {result.key_themes && result.key_themes.length > 0 && (
               <Card className="rounded-3xl border border-border bg-card p-6 md:p-8">
                  <h3 className="mb-4 text-lg font-bold">Key Themes</h3>
                  <div className="flex flex-wrap gap-2">
                     {result.key_themes.map((theme, index) => (
                        <Badge
                        key={index}
                        variant="secondary"
                        className={cn(
                           "rounded-lg px-3 py-1.5 text-sm font-normal",
                           theme.sentiment_direction === 'Bullish' && "bg-success/10 text-success hover:bg-success/20",
                           theme.sentiment_direction === 'Bearish' && "bg-destructive/10 text-destructive hover:bg-destructive/20"
                        )}
                        >
                        {theme.theme}
                        </Badge>
                     ))}
                  </div>
               </Card>
            )}

            {/* Impact & Gaps */}
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
               {result.potential_impact && (
                  <Card className="rounded-3xl border border-border bg-card p-6">
                     <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Potential Impact</p>
                     <p className={cn(
                        "text-lg font-medium",
                        result.potential_impact.includes('Positive') ? "text-success" :
                        result.potential_impact.includes('Negative') ? "text-destructive" : "text-foreground"
                     )}>
                        {result.potential_impact}
                     </p>
                  </Card>
               )}

               {result.information_gaps && result.information_gaps.length > 0 && (
                  <Card className="rounded-3xl border border-border bg-card p-6">
                     <p className="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Information Gaps</p>
                     <ul className="space-y-2">
                        {result.information_gaps.slice(0, 3).map((gap, i) => (
                           <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                              <span className="mt-0.5 text-warning">•</span>
                              <span>{gap}</span>
                           </li>
                        ))}
                     </ul>
                  </Card>
               )}
            </div>
        </TabsContent>

        <TabsContent value="chart" className="outline-none">
            <Card className="rounded-3xl border border-border bg-card p-6 md:p-8">
               {hasChartData ? (
                  <div className="h-[400px] w-full">
                  <ResponsiveContainer>
                     <AreaChart data={chartData}>
                        <defs>
                           <linearGradient id="colorClose" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.2}/>
                              <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0}/>
                           </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" className="stroke-muted/30" vertical={false} />
                        <XAxis
                           dataKey="date"
                           tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                           tickLine={false}
                           axisLine={{ stroke: 'hsl(var(--border))' }}
                           dy={10}
                        />
                        <YAxis
                           tick={{ fill: 'hsl(var(--muted-foreground))', fontSize: 12 }}
                           tickLine={false}
                           axisLine={false}
                           tickFormatter={(value) => `$${value}`}
                           domain={['auto', 'auto']}
                           dx={-10}
                        />
                        <Tooltip
                           contentStyle={{
                              backgroundColor: 'hsl(var(--card))',
                              borderRadius: '1rem',
                              borderColor: 'hsl(var(--border))',
                              color: 'hsl(var(--foreground))',
                              padding: '12px 16px',
                              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
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
                  <div className="py-20">
                     <EmptyState type="no-chart" />
                  </div>
               )}
            </Card>
        </TabsContent>

        <TabsContent value="fundamentals" className="outline-none">
            <Card className="rounded-3xl border border-border bg-card p-6 md:p-8">
               {result.fundamental_data ? (
                  <FundamentalsCard data={result.fundamental_data} />
               ) : (
                  <div className="py-20 text-center">
                  <EmptyState type="no-data" />
                  <p className="mt-4 text-muted-foreground">Fundamental data not available.</p>
                  </div>
               )}
            </Card>
        </TabsContent>

        <TabsContent value="news" className="outline-none">
            <Card className="rounded-3xl border border-border bg-card p-6 md:p-8">
               {(result.headlines || []).length > 0 ? (
                  <ul className="grid gap-4 sm:grid-cols-2">
                  {result.headlines.map((headline, index) => (
                     <li key={index} className="group relative rounded-2xl border border-border bg-muted/30 p-5 transition-all hover:bg-muted/50 hover:shadow-sm">
                        <p className="text-sm font-medium leading-relaxed text-foreground">{headline}</p>
                     </li>
                  ))}
                  </ul>
               ) : (
                  <EmptyState type="no-news" />
               )}
            </Card>
        </TabsContent>

        <TabsContent value="agent" className="outline-none">
            <Card className="rounded-3xl border border-border bg-card p-6 md:p-8">
               <div className="mb-6 flex items-center justify-between">
                  <h3 className="text-lg font-bold">Analysis Logic</h3>
                  <Badge variant="outline" className="rounded-full px-3">{result.iterations} Iterations</Badge>
               </div>

               <ol className="relative ml-3 space-y-8 border-l border-border pl-8">
                  {(result.reasoning_steps || []).map((step, index) => (
                  <li key={index} className="relative">
                     <span className="absolute -left-[41px] flex h-6 w-6 items-center justify-center rounded-full bg-background ring-4 ring-background border border-border text-xs font-bold text-muted-foreground">
                        {index + 1}
                     </span>
                     <p className="text-sm leading-relaxed text-muted-foreground">{step}</p>
                  </li>
                  ))}
               </ol>

               <div className="mt-8 border-t border-border pt-6">
                  <p className="mb-3 text-sm font-medium text-foreground">Tools Deployed</p>
                  <div className="flex flex-wrap gap-2">
                  {(result.tools_used || []).map(tool => (
                     <Badge key={tool} variant="secondary" className="rounded-full px-3 font-normal">
                        {tool}
                     </Badge>
                  ))}
                  </div>
               </div>
            </Card>
        </TabsContent>

        <TabsContent value="debate" className="outline-none space-y-6">
            {debateLoading && (
               <Card className="rounded-3xl border border-border bg-card p-12">
                  <div className="flex flex-col items-center justify-center gap-6">
                  <div className="flex items-center gap-3">
                     <Loader2 className="h-6 w-6 animate-spin text-primary" />
                     <div className="text-left">
                        <p className="font-semibold">Running Adversarial Analysis...</p>
                        <p className="text-sm text-muted-foreground">
                        Progress: {Math.round(debateProgress * 100)}%
                        </p>
                     </div>
                  </div>

                  <div className="w-full max-w-md">
                     <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
                        <div
                        className="h-full bg-primary transition-all duration-500 ease-out"
                        style={{ width: `${debateProgress * 100}%` }}
                        />
                     </div>
                  </div>

                  <Button onClick={resetDebate} variant="ghost" size="sm" className="mt-4 rounded-full">
                     Cancel Analysis
                  </Button>
                  </div>
               </Card>
            )}

            {debateError && !debateLoading && (
               <Card className="rounded-3xl border-destructive/20 bg-destructive/5 p-8">
                  <div className="flex flex-col items-center justify-center gap-4 text-center">
                  <AlertTriangle className="h-8 w-8 text-destructive" />
                  <div>
                     <p className="font-semibold text-destructive">Debate Failed</p>
                     <p className="text-sm text-muted-foreground">{debateError}</p>
                  </div>
                  <Button onClick={() => { resetDebate(); fetchDebateAnalysis(); }} variant="outline" size="sm" className="rounded-full">
                     Try Again
                  </Button>
                  </div>
               </Card>
            )}

            {debateData && !debateLoading && (
               <DebateView data={debateData} />
            )}

            {!debateData && !debateLoading && !debateError && (
               <Card className="rounded-3xl border border-border bg-card p-12 transition-all hover:shadow-md cursor-pointer" onClick={fetchDebateAnalysis}>
                  <div className="flex flex-col items-center justify-center gap-4 text-center">
                  <div className="rounded-full bg-primary/5 p-4">
                     <Scale className="h-8 w-8 text-primary" />
                  </div>
                  <div>
                     <p className="text-lg font-semibold">Start Adversarial Debate</p>
                     <p className="text-sm text-muted-foreground max-w-sm mx-auto mt-1">
                        Initiate a real-time debate between AI agents representing Bull and Bear perspectives.
                     </p>
                  </div>
                  <Button onClick={(e) => { e.stopPropagation(); fetchDebateAnalysis(); }} className="rounded-full px-6 mt-2">
                     Begin Analysis
                  </Button>
                  </div>
               </Card>
            )}
        </TabsContent>
      </Tabs>
    </div>
    
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
