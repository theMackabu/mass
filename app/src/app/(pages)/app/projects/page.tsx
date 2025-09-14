import Link from 'next/link';

import { CreateDialog } from './create';
import { ChevronRightIcon } from '@heroicons/react/20/solid';
import { CircleStackIcon, ServerStackIcon, GlobeAltIcon } from '@heroicons/react/24/outline';

import { tw } from '@/service/utils';
import { redirect } from 'next/navigation';
import { getSession } from '@/actions/get-session';
import { listProjects } from '@/actions/list-projects';

const statuses = {
  offline: 'bg-zinc-400 dark:bg-zinc-500',
  online: 'bg-green-500 dark:bg-green-400',
  error: 'bg-rose-500 dark:bg-rose-400'
};

const items = [
  {
    kind: 'script',
    name: 'Nebula',
    description: 'Lorem Ipsum',
    iconColor: 'bg-cyan-500',
    icon: ServerStackIcon
  },
  {
    kind: 'website',
    name: 'Pages',
    description: 'Lorem Ipsum',
    iconColor: 'bg-pink-500',
    icon: GlobeAltIcon
  },
  {
    kind: 'database',
    name: 'Database',
    description: 'Lorem Ipsum',
    iconColor: 'bg-yellow-500',
    icon: CircleStackIcon
  }
];

export default async () => {
  const session = await getSession();
  if (!session.user) redirect('/login');

  const list = await listProjects();

  if (list.length === 0)
    return (
      <div className="mx-auto max-w-lg absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
        <h2 className="text-base font-semibold text-zinc-900 dark:text-white">
          Create your first project
        </h2>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Get started by selecting a template or start from an empty project.
        </p>
        <ul
          role="list"
          className="mt-6 divide-y divide-zinc-200 border-y border-zinc-200 dark:divide-white/10 dark:border-white/10"
        >
          {items.map((item, itemIdx) => (
            <CreateDialog selected={item.kind} key={itemIdx}>
              <div className="group relative flex items-start space-x-3 py-4 cursor-pointer">
                <div className="shrink-0">
                  <span
                    className={tw(
                      item.iconColor,
                      'inline-flex size-10 items-center justify-center rounded-lg'
                    )}
                  >
                    <item.icon aria-hidden="true" className="size-6 text-white" />
                  </span>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="text-sm font-medium text-zinc-900 dark:text-white">
                    <span aria-hidden="true" className="absolute inset-0" />
                    {item.name}
                  </div>
                  <p className="text-sm text-zinc-500 dark:text-zinc-400">{item.description}</p>
                </div>
                <div className="shrink-0 self-center">
                  <ChevronRightIcon
                    aria-hidden="true"
                    className="size-5 text-zinc-400 group-hover:text-zinc-500 dark:text-zinc-500 dark:group-hover:text-zinc-400"
                  />
                </div>
              </div>
            </CreateDialog>
          ))}
        </ul>
        <div className="mt-6 flex">
          <CreateDialog title="Or start from an empty project" selected="blank" />
        </div>
      </div>
    );

  return (
    <div className="flex flex-col">
      <ul role="list" className="divide-y divide-zinc-100 dark:divide-white/5">
        {list.map(deployment => (
          <Link href={`/projects/${deployment.id}`} key={deployment.id} className="flex p-2">
            <div className={tw('size-2 rounded-full', statuses[deployment.metadata?.status])} />
            {deployment.name}
          </Link>
        ))}
      </ul>

      <div className="select-none fixed bottom-4 right-4 z-50 hidden md:block">
        <div className="group flex items-center gap-2 px-4 py-1.5 bg-black/90 hover:bg-black/95 dark:bg-white/10 dark:hover:bg-white/20 backdrop-blur-sm text-white dark:text-white font-medium rounded-full border border-white/10 shadow-lg shadow-black/20 transition-all duration-200 ease-in-out hover:scale-101 active:scale-98 cursor-pointer">
          <CreateDialog title="Create a new project" selected="script" />
        </div>
      </div>
    </div>
  );
};
