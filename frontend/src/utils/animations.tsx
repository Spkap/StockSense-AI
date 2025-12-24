import { motion, AnimatePresence, Variants } from 'framer-motion';
import { ReactNode } from 'react';

// Page transition variants
export const pageVariants: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.4, ease: 'easeOut' }
  },
  exit: { 
    opacity: 0, 
    y: -20,
    transition: { duration: 0.3, ease: 'easeIn' }
  },
};

// Fade variants
export const fadeVariants: Variants = {
  initial: { opacity: 0 },
  animate: { 
    opacity: 1,
    transition: { duration: 0.3 }
  },
  exit: { opacity: 0 },
};

// Scale variants for cards
export const scaleVariants: Variants = {
  initial: { opacity: 0, scale: 0.95 },
  animate: { 
    opacity: 1, 
    scale: 1,
    transition: { duration: 0.3, ease: 'easeOut' }
  },
  exit: { opacity: 0, scale: 0.95 },
};

// Stagger children animation
export const staggerContainerVariants: Variants = {
  initial: {},
  animate: {
    transition: {
      staggerChildren: 0.1,
    },
  },
};

export const staggerItemVariants: Variants = {
  initial: { opacity: 0, y: 20 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.3 }
  },
};

// Slide variants
export const slideUpVariants: Variants = {
  initial: { opacity: 0, y: 30 },
  animate: { 
    opacity: 1, 
    y: 0,
    transition: { duration: 0.4, ease: [0.25, 0.46, 0.45, 0.94] }
  },
};

// Pulse animation for loading states
export const pulseVariants: Variants = {
  animate: {
    scale: [1, 1.02, 1],
    opacity: [0.7, 1, 0.7],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: 'easeInOut',
    },
  },
};

// Animated wrapper component
interface AnimatedDivProps {
  children: ReactNode;
  variants?: Variants;
  className?: string;
  delay?: number;
}

export const AnimatedDiv = ({ 
  children, 
  variants = fadeVariants, 
  className,
  delay = 0 
}: AnimatedDivProps) => (
  <motion.div
    variants={variants}
    initial="initial"
    animate="animate"
    exit="exit"
    className={className}
    style={{ transitionDelay: `${delay}ms` }}
  >
    {children}
  </motion.div>
);

// Export AnimatePresence for use in components
export { motion, AnimatePresence };
