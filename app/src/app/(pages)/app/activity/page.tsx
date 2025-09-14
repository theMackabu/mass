export default function Page() {
  const tape =
    'repeating-linear-gradient(45deg, transparent, transparent 8px, rgba(0,0,0,0.2) 8px, rgba(0,0,0,0.2) 16px)';

  return (
    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
      <h1 className="mt-4 text-6xl font-semibold tracking-tight text-pretty text-zinc-900 dark:text-zinc-50 sm:text-7xl">
        Coming soon
      </h1>
      <div
        className="h-2 w-full bg-yellow-400 overflow-hidden"
        style={{ backgroundImage: tape }}
      ></div>
    </div>
  );
}
