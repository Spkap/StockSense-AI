/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx,js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'Geist Mono'", "monospace"],
        serif: ["'Lora'", "serif"],
      },
      colors: {
        canvas: "var(--canvas)",
        "surface-1": "var(--surface-1)",
        "surface-2": "var(--surface-2)",
        "surface-3": "var(--surface-3)",
        
        "border-subtle": "var(--border-subtle)",
        "border-base": "var(--border-base)",
        "border-strong": "var(--border-strong)",
        "border-focus": "var(--border-focus)",
        
        "txt-primary": "var(--text-primary)",
        "txt-secondary": "var(--text-secondary)",
        "txt-tertiary": "var(--text-tertiary)",
        "txt-muted": "var(--text-muted)",
        
        bull: "var(--bull)",
        "bull-dim": "var(--bull-dim)",
        bear: "var(--bear)",
        "bear-dim": "var(--bear-dim)",
        kill: "var(--kill)",
        "kill-dim": "var(--kill-dim)",
        
        accent: "var(--accent)",
        "accent-dim": "var(--accent-dim)",
      },
      spacing: {
        1: "var(--space-1)",
        2: "var(--space-2)",
        3: "var(--space-3)",
        4: "var(--space-4)",
        6: "var(--space-6)",
        8: "var(--space-8)",
        12: "var(--space-12)",
      },
      borderRadius: {
        sm: "var(--radius-sm)",
        md: "var(--radius-md)",
        lg: "var(--radius-lg)",
      },
      fontSize: {
        micro: ["var(--type-micro)", "1.4"],
        sm: ["var(--type-sm)", "1.5"],
        base: ["var(--type-base)", "1.6"],
        md: ["var(--type-md)", "1.5"],
        lg: ["var(--type-lg)", "1.3"],
        xl: ["var(--type-xl)", "1.2"],
        "2xl": ["var(--type-2xl)", "1.1"],
      },
      transitionTimingFunction: {
        terminal: "cubic-bezier(0.16, 1, 0.3, 1)",
      },
      transitionDuration: {
        100: "100ms",
        150: "150ms",
        200: "200ms",
        300: "300ms",
        600: "600ms",
      },
      keyframes: {
        pulseCursor: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0" },
        },
      },
      animation: {
        "pulse-cursor": "pulseCursor 1s step-end infinite",
      },
    },
  },
  plugins: [require("tailwindcss-animate"), require("@tailwindcss/typography")],
}
