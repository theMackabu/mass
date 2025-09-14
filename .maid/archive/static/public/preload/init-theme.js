function initTheme() {
  const root = document.documentElement;
  const theme = localStorage.getItem('ui-theme') || 'system';

  if (theme === 'system') {
    const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
      ? 'dark'
      : 'light';
    root.classList.add(systemTheme);
  } else {
    root.classList.add(theme);
  }
}

initTheme();
