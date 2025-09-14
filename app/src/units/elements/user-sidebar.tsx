'use client';

import { useState } from 'react';
import { useSession } from '@/service/auth/client';

import { Drawer } from 'vaul';
import { Flex, Text } from 'summit';
import BoringAvatar from 'boring-avatars';
import { XIcon } from '@phosphor-icons/react';
import { Avatar } from '@/units/summit/avatar';

import {
  Sidebar,
  SidebarItem,
  SidebarLabel,
  SidebarIcon,
  SidebarSection,
  SidebarDivider
} from '@/units/summit/sidebar';

import {
  BookBookmarkIcon,
  BrowserIcon,
  PlanetIcon,
  FlaskIcon,
  GearSixIcon,
  BookOpenTextIcon,
  SignOutIcon
} from '@phosphor-icons/react';

export const UserSidebar = () => {
  const { data } = useSession();
  const [open, setOpen] = useState(false);

  return (
    <Drawer.Root direction="right" open={open} onOpenChange={setOpen}>
      <Drawer.Trigger>
        <Avatar
          square
          src={data?.user.image}
          initials={data?.user.username?.slice(0, 1)}
          className="size-6 -mr-1 -mt-1 bg-zinc-100 dark:bg-zinc-800"
        />
      </Drawer.Trigger>
      <Drawer.Portal>
        <Drawer.Overlay className="fixed inset-0 bg-zinc-900/50" />
        <Drawer.Content
          className="right-1.5 top-1.5 bottom-1.5 fixed z-10 outline-none w-[310px] flex"
          style={{ '--initial-transform': 'calc(100% + 8px)' } as React.CSSProperties}
        >
          <Flex
            direction="column"
            gap="8px"
            className="bg-zinc-50 dark:bg-zinc-900 ring-1 ring-zinc-950/5 dark:ring-white/8 grow p-3 rounded-lg"
          >
            <Flex justify="between" align="start">
              <Drawer.Title>
                <Flex align="center" gap="10px">
                  <Avatar
                    src={data?.user.image}
                    initials={data?.user.username?.slice(0, 1)}
                    className="size-8.5 bg-zinc-100 dark:bg-zinc-800"
                  />
                  <Flex direction="column">
                    <Text className="text-sm font-bold leading-4!">{data?.user.username}</Text>
                  </Flex>
                </Flex>
              </Drawer.Title>

              <Drawer.Close className="p-2 -m-1 text-zinc-500 dark:text-zinc-300 hover:bg-zinc-950/5 dark:hover:bg-white/5 rounded-md">
                <XIcon />
              </Drawer.Close>
            </Flex>

            <Sidebar>
              <SidebarSection>
                <SidebarDivider />
                <SidebarItem href="/app/projects" onClick={() => setOpen(false)}>
                  <SidebarIcon icon={BookBookmarkIcon} />
                  <SidebarLabel>Your projects</SidebarLabel>
                </SidebarItem>
                <SidebarItem href="/app/projects/pages">
                  <SidebarIcon icon={BrowserIcon} />
                  <SidebarLabel>Your pages</SidebarLabel>
                </SidebarItem>
                <SidebarItem href="/app/settings/workspaces" onClick={() => setOpen(false)}>
                  <SidebarIcon icon={PlanetIcon} />
                  <SidebarLabel>Your workspaces</SidebarLabel>
                </SidebarItem>
                <SidebarDivider />
                <SidebarItem href="https://docs.ship.ci">
                  <SidebarIcon icon={BookOpenTextIcon} />
                  <SidebarLabel>Documentation</SidebarLabel>
                </SidebarItem>
                <SidebarItem href="/app/settings/preview" onClick={() => setOpen(false)}>
                  <SidebarIcon icon={FlaskIcon} />
                  <SidebarLabel>Feature preview</SidebarLabel>
                </SidebarItem>
                <SidebarItem href="/app/settings" onClick={() => setOpen(false)}>
                  <SidebarIcon icon={GearSixIcon} />
                  <SidebarLabel>Account Settings</SidebarLabel>
                </SidebarItem>
              </SidebarSection>

              <SidebarSection>
                <SidebarDivider />
                <SidebarItem href="/api/service/logout">
                  <SidebarIcon icon={SignOutIcon} />
                  <SidebarLabel>Sign out</SidebarLabel>
                </SidebarItem>
              </SidebarSection>
            </Sidebar>
          </Flex>
        </Drawer.Content>
      </Drawer.Portal>
    </Drawer.Root>
  );
};
