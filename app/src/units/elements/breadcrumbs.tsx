'use client';

import { Fragment } from 'react';
import { tw } from '@/service/utils';
import { Link } from '@/units/summit/link';
import { usePathname } from 'next/navigation';

interface BreadcrumbItem {
  segment: string;
  href: string;
}

const generateBreadcrumbs = (pathname: string): BreadcrumbItem[] => {
  const pathSegments = pathname.split('/').filter(Boolean);
  const breadcrumbs: BreadcrumbItem[] = [];

  let currentPath = '';

  pathSegments.slice(0, 2).forEach(segment => {
    currentPath += `/${segment}`;

    breadcrumbs.push({
      segment,
      href: currentPath
    });
  });

  return breadcrumbs;
};

export const Breadcrumbs = () => {
  const pathname = usePathname();
  const breadcrumbs = generateBreadcrumbs(pathname);

  return (
    <nav className="flex items-center space-x-2 text-[14.5px]">
      {breadcrumbs.map((crumb, index) => (
        <div key={crumb.href} className="flex items-center space-x-1 select-none">
          {index === breadcrumbs.length - 1 ? (
            <span className="text-zinc-900 dark:text-zinc-100 font-semibold">{crumb.segment}</span>
          ) : (
            <Fragment>
              <Link
                href={crumb.href}
                className={tw(
                  'py-0.5 px-1 -my-1 -ml-1',
                  'hover:bg-black/5 dark:hover:bg-white/5',
                  'text-zinc-800 dark:text-zinc-200 rounded-sm'
                )}
              >
                {crumb.segment}
              </Link>
              <span className="text-zinc-400 dark:text-zinc-500">/</span>
            </Fragment>
          )}
        </div>
      ))}
    </nav>
  );
};
