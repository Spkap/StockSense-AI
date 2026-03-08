import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-sm font-mono tracking-widest uppercase transition-colors duration-150 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-accent disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-accent text-canvas hover:bg-accent/90 border border-transparent",
        destructive:
          "bg-bear/10 text-bear border border-bear/30 hover:bg-bear/20",
        outline:
          "border border-border-base bg-surface-1 hover:border-border-strong hover:bg-surface-2 hover:text-txt-primary text-txt-secondary",
        secondary:
          "bg-surface-2 text-txt-primary border border-border-base hover:bg-surface-3",
        ghost: "border border-transparent text-txt-secondary hover:border-border-base hover:bg-surface-2 hover:text-txt-primary",
        link: "text-txt-secondary underline-offset-4 hover:underline hover:text-txt-primary",
      },
      size: {
        default: "h-8 px-4 text-micro [&_svg]:size-3",
        sm: "h-7 px-3 text-micro [&_svg]:size-3",
        lg: "h-10 px-6 text-sm [&_svg]:size-4",
        icon: "h-8 w-8",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
