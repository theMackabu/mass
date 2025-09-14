import { clsx } from 'clsx';
import { cn } from '@/utils/common';
import { motion, AnimatePresence } from 'motion/react';

type SpinnerSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl';

interface SpinnerProps {
  loading: boolean;
  size?: SpinnerSize;
  className?: string;
}

const sizeClasses: Record<SpinnerSize, string> = {
  xs: 'size-2.5 border',
  sm: 'size-3 border',
  md: 'size-3.5 border-2',
  lg: 'size-5 border-2',
  xl: 'size-7 border-[3px]',
};

export const Spinner = ({ loading, size = 'md', className }: SpinnerProps) => (
  <AnimatePresence>
    {loading && (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.2 }}
        className={cn(className)}
      >
        <motion.div
          className={clsx(
            sizeClasses[size],
            'border-zinc-300 border-t-zinc-600 dark:border-t-zinc-300 dark:border-zinc-600 rounded-full',
          )}
          animate={{ rotate: 360 }}
          transition={{ duration: 1, ease: 'linear', repeat: Infinity }}
        />
      </motion.div>
    )}
  </AnimatePresence>
);
