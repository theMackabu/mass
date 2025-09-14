'use client';

import { tw } from '@/service/utils';
import { motion } from 'motion/react';
import { Link } from '@/units/summit/link';
import { usePathname, useSearchParams } from 'next/navigation';

interface Tab {
  id: number;
  name: string;
  href: string;
  wildcard?: boolean;
}

interface TabProps {
  tabs: Tab[];
  root: string;
  isParam?: boolean;
}

export const Tabs = ({ tabs, root, isParam }: TabProps) => {
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const isTabActive = (tab: Tab) => {
    if (isParam) {
      const currentTab = searchParams.get('tab');

      if (tab.href === '') return !currentTab || currentTab === '';
      if (currentTab === tab.href) return true;

      const hasMatchingTab = tabs.some(t => t.href === currentTab);
      return !hasMatchingTab && tab.wildcard;
    }

    if (tab.href === '') return pathname === root;
    if (tab.wildcard) return pathname.startsWith(`${root}/${tab.href}`);

    return pathname.endsWith(`/${tab.href}`);
  };

  const getTabHref = (tab: Tab) => {
    if (isParam) {
      if (tab.href === '') return root;
      return `${root}${root === '/' ? '' : '/'}?tab=${tab.href}`;
    }

    if (tab.href === '') return root;
    return root === '/' ? `/${tab.href}` : `${root}/${tab.href}`;
  };

  return (
    <nav className="flex z-10 sticky top-0 w-full select-none">
      <ul className="flex min-w-full flex-none gap-x-7 px-1 text-sm font-[450] overflow-visible">
        {tabs.map(tab => (
          <li
            key={tab.id}
            className={tw(
              'relative text-zinc-500 hover:text-zinc-600',
              'dark:text-zinc-400 dark:hover:text-zinc-200',
              isTabActive(tab) && 'text-black dark:text-white',
            )}
          >
            {isTabActive(tab) && (
              <motion.span
                layoutId="current-indicator"
                className="absolute -inset-x-1.5 -bottom-[10.5px] h-0.5 bg-zinc-950 dark:bg-white"
              />
            )}
            <Link href={getTabHref(tab)}>{tab.name}</Link>
          </li>
        ))}
      </ul>
    </nav>
  );
};
