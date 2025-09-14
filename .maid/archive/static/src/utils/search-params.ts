export const url = {
  get: (key: string) => {
    return new URLSearchParams(location.search).get(key);
  },

  set: (key: string, value: string) => {
    const url = new URL(location.href);
    url.searchParams.set(key, value);
    history.replaceState(null, '', url);
  },

  remove: (key: string) => {
    const url = new URL(location.href);
    url.searchParams.delete(key);
    history.replaceState(null, '', url);
  },

  toggle: (key: string) => {
    const current = url.get(key) === 'true';
    url.set(key, String(!current));
    return !current;
  },
};
