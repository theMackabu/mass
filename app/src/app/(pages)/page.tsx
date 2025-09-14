import { getSession } from '@/actions/get-session';

export default async () => {
  const session = await getSession();

  if (!session.user) {
    return <div>Not authenticated</div>;
  }

  return <div>authenticated</div>;
};
