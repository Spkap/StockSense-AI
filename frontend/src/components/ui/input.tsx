import * as React from "react"
import { cn } from "@/lib/utils"

const Input = React.forwardRef<HTMLInputElement, React.ComponentProps<"input">>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-sm border border-border-base bg-surface-3 px-3 py-2 font-mono text-sm text-txt-primary shadow-none transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-txt-muted focus-visible:outline-none focus-visible:border-border-focus focus-visible:ring-1 focus-visible:ring-border-focus disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input }
