import { cn } from '../../utils/cn';
import { CSSProperties } from 'react';

interface SkeletonProps {
  className?: string;
  style?: CSSProperties;
}

/**
 * Skeleton loading placeholder with shimmer effect
 */
export function Skeleton({ className, style }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-md bg-muted",
        className
      )}
      style={style}
    />
  );
}

/**
 * Skeleton for a card with header and content
 */
export function CardSkeleton({ className }: SkeletonProps) {
  return (
    <div className={cn("rounded-lg border border-border bg-card p-6", className)}>
      <Skeleton className="h-6 w-1/3 mb-4" />
      <div className="space-y-3">
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-5/6" />
        <Skeleton className="h-4 w-4/6" />
      </div>
    </div>
  );
}

/**
 * Skeleton for analysis results page
 */
export function AnalysisSkeleton() {
  return (
    <div className="rounded-lg border border-border bg-card overflow-hidden">
      {/* Header */}
      <div className="border-b border-border bg-muted/50 p-4 md:p-6">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between mb-6">
          <div className="flex items-center gap-3">
            <Skeleton className="h-8 w-8 rounded-full" />
            <Skeleton className="h-8 w-24" />
            <Skeleton className="h-6 w-16 rounded-full" />
          </div>
          <div className="flex items-center gap-2">
            <Skeleton className="h-6 w-20" />
            <Skeleton className="h-8 w-24 rounded-md" />
          </div>
        </div>
        
        {/* Tabs */}
        <div className="flex gap-2">
          <Skeleton className="h-9 w-20 rounded-md" />
          <Skeleton className="h-9 w-20 rounded-md" />
          <Skeleton className="h-9 w-20 rounded-md" />
          <Skeleton className="h-9 w-20 rounded-md" />
        </div>
      </div>
      
      {/* Content */}
      <div className="p-4 md:p-6">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
          {/* Sentiment Card */}
          <div className="rounded-lg border border-border bg-card p-4">
            <Skeleton className="h-5 w-24 mb-4" />
            <Skeleton className="h-16 w-16 rounded-full mx-auto mb-4" />
            <Skeleton className="h-4 w-32 mx-auto" />
          </div>
          
          {/* Summary */}
          <div className="lg:col-span-2 rounded-lg border border-border bg-card p-4">
            <Skeleton className="h-5 w-32 mb-4" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-5/6" />
              <Skeleton className="h-4 w-4/6" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton for chart area
 */
export function ChartSkeleton() {
  return (
    <div className="h-[300px] md:h-[400px] w-full rounded-lg border border-border bg-card p-4">
      <div className="h-full flex flex-col">
        <div className="flex justify-between mb-4">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-24" />
        </div>
        <div className="flex-1 flex items-end gap-1">
          {Array.from({ length: 20 }).map((_, i) => (
            <Skeleton 
              key={i} 
              className="flex-1"
              style={{ height: `${30 + Math.random() * 60}%` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Skeleton for list items (history, headlines)
 */
export function ListSkeleton({ items = 5 }: { items?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: items }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-2 rounded-md">
          <Skeleton className="h-4 w-4 rounded" />
          <div className="flex-1">
            <Skeleton className="h-4 w-full" />
          </div>
          <Skeleton className="h-4 w-16" />
        </div>
      ))}
    </div>
  );
}
