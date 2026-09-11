/* Runs before styles so a saved dark theme never flashes light. */
(() => {
  let saved;
  try { saved = localStorage.getItem('kakoe-media-theme'); } catch { /* Storage may be disabled. */ }
  const dark = saved === 'dark' || (saved !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  document.querySelector('meta[name="theme-color"]').content = dark ? '#151e27' : '#f6f3e9';
})();
