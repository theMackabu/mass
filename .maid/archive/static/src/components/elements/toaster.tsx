import { cn } from '@/utils/common';
import { useTheme } from '@/providers/theme';
import { Toaster as SonnerToaster, type ToasterProps } from 'sonner';

export function Toaster({ className, ...props }: ToasterProps & { className?: string }) {
  const { computedTheme } = useTheme();

  const classNames = {
    toast: cn(className, 'rounded-xl! select-none cursor-default dark:bg-zinc-900!'),
  };

  return (
    <SonnerToaster
      theme={computedTheme}
      position="bottom-right"
      toastOptions={{ classNames }}
      {...props}
    />
  );
}
