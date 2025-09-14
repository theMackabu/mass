export const StackedLayout = ({ navbar, children }: Children<{ navbar: React.ReactNode }>) => (
  <div className="relative isolate flex min-h-svh w-full flex-col bg-white md:bg-zinc-100 dark:bg-zinc-950">
    <header className="flex items-center px-4 border-b border-black/8 dark:border-white/8">
      <div className="min-w-0 flex-1">{navbar}</div>
    </header>

    <main className="flex flex-1 flex-col md:bg-white dark:md:bg-zinc-900">
      <div className="grow">{children}</div>
    </main>
  </div>
);
