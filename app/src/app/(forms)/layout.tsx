import { Flex } from 'summit';

import { tw } from '@/service/utils';
import { redirect } from 'next/navigation';
import { getSession } from '@/actions/get-session';

export default async ({ children }: Children) => {
  const session = await getSession();
  if (session.user) redirect('/app/projects');

  return (
    <main className="flex min-h-dvh flex-col p-2 select-none">
      <Flex
        justify="center"
        className={tw(
          'flex grow items-center justify-center p-2',
          'md:rounded-sm md:bg-white md:shadow-xs md:ring-1',
          'md:ring-zinc-950/5 dark:md:bg-zinc-900 dark:md:ring-white/10'
        )}
      >
        {children}
      </Flex>
    </main>
  );
};
