import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, FileText, BarChart3, ShieldAlert, Sparkles } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from './ui/card';
import { Badge } from './ui/badge';
import FundamentalsCard from './FundamentalsCard';
import SkepticCard from './SkepticCard';
import SentimentCard from './SentimentCard';
import { useDeleteAnalysis } from '../api/hooks';
import type { AnalysisData } from '../types/api';
import { cn } from '../utils/cn';

interface ResultsTabsProps {
  result: AnalysisData;
  onRefresh: () => void;
  isRefreshing: boolean;
}

const tabs = [
  { id: 'thesis', label: 'Investment Thesis', icon: FileText },
  { id: 'skeptic', label: 'Bear Case & Risks', icon: ShieldAlert },
  { id: 'fundamentals', label: 'Fundamentals', icon: BarChart3 },
  // { id: 'news', label: 'News & Sentiment', icon: Newspaper }, // Merged into Thesis/Sentiment
];

function splitParagraphs(text: string): string[] {
  return text
    .split(/\n{2,}/)
    .map((paragraph) => paragraph.trim())
    .filter(Boolean);
}

function splitBullets(text: string): string[] {
  return text
    .split(/\s+-\s+|\n+/)
    .map((item) => item.replace(/^[-*]\s*/, '').trim())
    .filter(Boolean);
}

function titleizeToolName(tool: string): string {
  return tool
    .replace(/^fetch_/, 'Fetch ')
    .replace(/^generate_/, 'Generate ')
    .replace(/^analyze_/, 'Analyze ')
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

const ResultsTabs = ({ result, onRefresh, isRefreshing }: ResultsTabsProps) => {
  const [activeTab, setActiveTab] = useState('thesis');
  const [freshRunArmed, setFreshRunArmed] = useState(false);
  const deleteAnalysis = useDeleteAnalysis();

  // Auto-disarm after 3 seconds if user doesn't confirm
  useEffect(() => {
    if (!freshRunArmed) return;
    const timer = setTimeout(() => setFreshRunArmed(false), 3000);
    return () => clearTimeout(timer);
  }, [freshRunArmed]);

  const handleFreshRun = async () => {
    if (!freshRunArmed) {
      setFreshRunArmed(true);
      return;
    }
    setFreshRunArmed(false);
    await deleteAnalysis.mutateAsync(result.ticker);
    onRefresh();
  };

  const summaryParagraphs = (() => {
    if (result.confidence_reasoning?.trim()) {
      const paragraphs = [
        `Market Sentiment: ${result.overall_sentiment || 'Unavailable'} (${Math.round((result.overall_confidence || 0) * 100)}% confidence).`,
        result.confidence_reasoning,
      ];

      if (result.potential_impact) {
        paragraphs.push(`Expected impact: ${result.potential_impact}.`);
      }

      return paragraphs;
    }

    return splitParagraphs(result.summary);
  })();

  const methodologySteps = (() => {
    if (result.reasoning_steps.length > 0) {
      return result.reasoning_steps;
    }

    if (result.tools_used.length > 0) {
      return result.tools_used.map((tool, index) => `${index + 1}. ${titleizeToolName(tool)}`);
    }

    const summaryBullets = splitBullets(result.summary).filter(
      (item) => !item.toLowerCase().startsWith('stock analysis summary')
    );
    return summaryBullets.slice(0, 5);
  })();

  return (
    <div className="space-y-6">
      {/* Header with Title and Refresh */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight text-foreground">{result.ticker}</h2>
            <Badge variant="outline" className="text-xs font-medium uppercase tracking-wider">
              {result.agent_type} Analysis
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            Generated on {new Date(result.timestamp).toLocaleDateString()} at {new Date(result.timestamp).toLocaleTimeString()}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isRefreshing || deleteAnalysis.isPending}
            className="gap-2 rounded-full border-border/60 bg-background/50 backdrop-blur-sm transition-all hover:bg-background"
          >
            <RefreshCw className={cn("h-4 w-4", isRefreshing && "animate-spin")} />
            <span>Refresh</span>
          </Button>
          <Button
            variant={freshRunArmed ? "destructive" : "outline"}
            size="sm"
            onClick={handleFreshRun}
            disabled={isRefreshing || deleteAnalysis.isPending}
            className={cn(
              "gap-2 rounded-full backdrop-blur-sm transition-all",
              freshRunArmed
                ? "animate-pulse"
                : "border-border/60 bg-background/50 hover:bg-background"
            )}
          >
            <Sparkles className="h-4 w-4" />
            <span>{freshRunArmed ? "Confirm?" : "Fresh Run"}</span>
          </Button>
        </div>
      </div>

      {/* Custom Segmented Control */}
      <div className="no-scrollbar overflow-x-auto pb-1">
        <div className="flex w-fit items-center rounded-xl border border-border/40 bg-secondary/30 p-1 backdrop-blur-sm">
          {tabs.map((tab) => {
             // Disable fundamentals tab if no data
             if (tab.id === 'fundamentals' && !result.fundamental_data) return null;

             const isActive = activeTab === tab.id;
             return (
               <button
                 key={tab.id}
                 onClick={() => setActiveTab(tab.id)}
                 className={cn(
                   "relative flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-all duration-300 outline-none focus-visible:ring-2 focus-visible:ring-primary/20",
                   isActive 
                     ? "text-foreground shadow-sm" 
                     : "text-muted-foreground hover:text-foreground hover:bg-background/40"
                 )}
               >
                 {isActive && (
                   <motion.div
                     layoutId="activeTab"
                     className="absolute inset-0 rounded-lg bg-background"
                     initial={false}
                     transition={{ type: "spring", stiffness: 400, damping: 30 }}
                   />
                 )}
                 <span className="relative z-10 flex items-center gap-2">
                   <tab.icon className="h-4 w-4" />
                   {tab.label}
                 </span>
               </button>
             );
          })}
        </div>
      </div>

      {/* Content Area */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.3 }}
          className="min-h-[400px]"
        >
          {activeTab === 'thesis' && (
            <div className="grid gap-6 md:grid-cols-3">
              {/* Main Thesis Content */}
              <div className="md:col-span-2 space-y-6">
                <Card className="border-border/60 bg-gradient-to-b from-card to-secondary/10 shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-xl">Executive Summary</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {summaryParagraphs.map((paragraph, idx) => (
                        <p key={idx} className="mb-4 text-sm leading-relaxed text-muted-foreground last:mb-0">
                          {paragraph}
                        </p>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Reasoning Steps */}
                <Card className="border-border/60 shadow-sm">
                  <CardHeader>
                    <CardTitle className="text-lg">Analysis Methodology</CardTitle>
                    <CardDescription>Steps taken by the agent</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {methodologySteps.length > 0 ? (
                      <ul className="space-y-4">
                        {methodologySteps.map((step, i) => (
                          <li key={i} className="flex gap-3">
                            <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10 text-xs font-bold text-primary">
                              {i + 1}
                            </div>
                            <p className="text-sm text-muted-foreground">{step.replace(/^\d+\.\s*/, '')}</p>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <div className="rounded-lg border border-dashed border-border/60 bg-muted/20 p-4 text-sm text-muted-foreground">
                        Agent methodology is not available for this run yet.
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>

              {/* Sidebar: Sentiment & Quick Stats */}
              <div className="space-y-6">
                <SentimentCard 
                   data={result}
                />
                
                {/* Tools Used Pill */}
                <div className="rounded-xl border border-border/60 bg-card p-4 shadow-sm">
                  <h4 className="mb-3 text-sm font-semibold text-muted-foreground">Tools Deployed</h4>
                  <div className="flex flex-wrap gap-2">
                    {result.tools_used.map((tool) => (
                      <Badge key={tool} variant="secondary" className="bg-secondary/50 font-normal">
                        {tool}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'skeptic' && (
            <SkepticCard data={result} />
          )}

          {activeTab === 'fundamentals' && result.fundamental_data && (
            <FundamentalsCard data={result.fundamental_data} />
          )}
        </motion.div>
      </AnimatePresence>
    </div>
  );
};

export default ResultsTabs;
