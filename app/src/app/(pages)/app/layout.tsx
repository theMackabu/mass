import { Tabs } from '@/units/elements/tab-menu';
import { NavMenu } from '@/units/elements/nav-menu';
import { StackedLayout } from '@/units/elements/stacked-layout';

import { redirect } from 'next/navigation';
import { getSession } from '@/actions/get-session';

const tabs = [
  { id: 0, name: 'Projects', href: 'projects', wildcard: true },
  { id: 1, name: 'Activity', href: 'activity' },
  { id: 2, name: 'Explore', href: 'explore' },
];

export default async ({ children }: Children) => {
  const session = await getSession();
  if (!session.user) redirect('/login');

  return (
    <StackedLayout navbar={<NavMenu slot={<Tabs tabs={tabs} root="/app" />} />}>
      {children}
    </StackedLayout>
  );
};
