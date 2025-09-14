'use client';

import { Fragment } from 'react';
import { MassLogo } from '@/units/elements/mass-logo';
import { UserSidebar } from '@/units/elements/user-sidebar';
import { Breadcrumbs } from '@/units/elements/breadcrumbs';
import { Navbar, NavbarDivider, NavbarSpacer } from '@/units/summit/navbar';

export const NavMenu = ({ isSlug, slot }: { isSlug?: boolean; slot?: React.ReactNode }) => (
  <Navbar>
    <MassLogo size={60} href="/app/projects" />

    {isSlug && (
      <Fragment>
        <NavbarDivider className="max-md:hidden" />
        <Breadcrumbs />
      </Fragment>
    )}

    {slot && (
      <Fragment>
        <NavbarDivider className="max-md:hidden" />
        {slot}
      </Fragment>
    )}

    <NavbarSpacer />
    <UserSidebar />
  </Navbar>
);
