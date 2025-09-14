import { cn } from '@/utils/common';

type HeadingProps = {
  level?: 1 | 2 | 3 | 4 | 5 | 6;
} & React.ComponentPropsWithoutRef<'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6'>;

export const Divider = () => <div className="h-2.5 w-[1px] bg-zinc-300 dark:bg-zinc-600" />;

export function Header({ className, level = 1, ...props }: HeadingProps) {
  const Element: `h${typeof level}` = `h${level}`;
  return (
    <Element
      {...props}
      className={cn(
        className,
        'text-3xl/8 font-medium text-zinc-950 tracking-tight dark:text-white',
      )}
    />
  );
}

export function Heading({ className, level = 1, ...props }: HeadingProps) {
  const Element: `h${typeof level}` = `h${level}`;
  return (
    <Element
      {...props}
      className={cn(
        className,
        'text-2xl/8 font-semibold text-zinc-950 sm:text-xl/8 dark:text-white',
      )}
    />
  );
}

export function Subheading({ className, level = 2, ...props }: HeadingProps) {
  const Element: `h${typeof level}` = `h${level}`;
  return (
    <Element
      {...props}
      className={cn(
        className,
        'text-base/7 font-semibold text-zinc-950 sm:text-sm/6 dark:text-white',
      )}
    />
  );
}
