import Link from 'next/link';

export default () => (
  <main className="mx-auto w-full max-w-5xl px-6 py-24 sm:py-40 lg:col-span-2 lg:col-start-1 lg:row-start-2 lg:px-8 select-none">
    <div className="max-w-lg">
      <h1 className="mt-4 text-6xl font-semibold tracking-tight text-pretty text-zinc-900 dark:text-zinc-50 sm:text-7xl">
        404 <span className="text-2xl font-medium text-zinc-400 dark:text-zinc-300">not found</span>
      </h1>

      <p className="mt-6 text-lg font-medium text-pretty text-zinc-500 dark:text-zinc-400 sm:text-xl/8">
        The page you were looking for has mysteriously disappeared... or never existed at all.
      </p>

      <div className="mt-8">
        <Link
          href="/app/projects"
          className="text-xl font-semibold text-zinc-900 dark:text-white hover:text-sky-500"
        >
          Back to dashboard &rarr;
        </Link>
      </div>
    </div>
  </main>
);
