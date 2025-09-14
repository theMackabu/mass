import { cn } from '@/utils/common';
import { Navbar } from '#/elements/navbar';
import { ScrollProvider } from '@/providers/scroll';

export const AppShell = ({ children }: Children) => (
  <ScrollProvider className="relative isolate flex h-svh w-full flex-col bg-zinc-50 dark:bg-zinc-900">
    <Navbar />
    <div className="flex flex-1 flex-col pb-1 sm:px-1 min-h-0">
      <div
        className={cn(
          'flex-1 overflow-auto sm:bg-zinc-50 dark:bg-zinc-900 overflow-y-scroll',
          'sm:rounded-md sm:ring-[0.5px] sm:ring-zinc-900/10 dark:sm:ring-zinc-50/10 outline-none',
        )}
      >
        {children}
      </div>
    </div>
  </ScrollProvider>
);
