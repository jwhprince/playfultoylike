(() => {
  'use strict';
  const root = document.documentElement;
  const themeButton = document.querySelector('.theme-toggle');
  const systemTheme = matchMedia('(prefers-color-scheme: dark)');
  let hasSavedTheme = false;
  try { hasSavedTheme = ['light', 'dark'].includes(localStorage.getItem('kakoe-media-theme')); } catch { /* Optional storage. */ }
  function setTheme(theme, persist = false) {
    root.dataset.theme = theme;
    const dark = theme === 'dark';
    themeButton.setAttribute('aria-pressed', String(dark));
    themeButton.title = dark ? 'Включить светлую тему' : 'Включить тёмную тему';
    document.querySelector('meta[name="theme-color"]').content = dark ? '#151e27' : '#f6f3e9';
    if (persist) { hasSavedTheme = true; try { localStorage.setItem('kakoe-media-theme', theme); } catch { /* Works without persistence. */ } }
  }
  themeButton.hidden = false;
  setTheme(root.dataset.theme || 'light');
  themeButton.addEventListener('click', () => setTheme(root.dataset.theme === 'dark' ? 'light' : 'dark', true));
  systemTheme.addEventListener('change', event => { if (!hasSavedTheme) setTheme(event.matches ? 'dark' : 'light'); });
  window.addEventListener('storage', event => {
    if (event.key !== 'kakoe-media-theme' && event.key !== null) return;
    hasSavedTheme = ['light', 'dark'].includes(event.newValue);
    setTheme(hasSavedTheme ? event.newValue : (systemTheme.matches ? 'dark' : 'light'));
  });
  const ticker = document.querySelector('.ticker-shell');
  const pause = document.querySelector('.ticker-pause');
  pause.hidden = false;
  pause.addEventListener('click', () => {
    const paused = ticker.dataset.paused !== 'true';
    ticker.dataset.paused = String(paused);
    pause.setAttribute('aria-pressed', String(paused));
    pause.setAttribute('aria-label', paused ? 'Запустить бегущую строку' : 'Приостановить бегущую строку');
    pause.firstElementChild.textContent = paused ? '▷' : 'Ⅱ';
  });
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)');
  if ('IntersectionObserver' in window && !reduceMotion.matches) {
    const observer = new IntersectionObserver(entries => {
      entries.forEach(entry => { if (entry.isIntersecting) { entry.target.classList.add('is-visible'); observer.unobserve(entry.target); } });
    }, { threshold: .12 });
    document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
  }
  // Delegate so newly loaded gallery buttons receive the same touch feedback.
  const touchSelector = '.button,.filter,.theme-toggle,.gallery-image-button,.icon-button,.ticker-pause,.service,.smile-sticker';
  let pressed = null, releaseTimer;
  function clearPress() {
    clearTimeout(releaseTimer);
    pressed?.element.classList.remove('is-touching');
    pressed = null;
  }
  document.addEventListener('pointerdown', event => {
    if (event.pointerType === 'mouse' || !event.isPrimary) return;
    clearPress();
    const element = event.target.closest(touchSelector);
    if (!element || element.disabled) return;
    pressed = { element, x: event.clientX, y: event.clientY, id: event.pointerId };
    element.classList.add('is-touching');
  }, { passive: true });
  document.addEventListener('pointermove', event => {
    if (pressed && event.pointerId === pressed.id && Math.hypot(event.clientX - pressed.x, event.clientY - pressed.y) > 12) clearPress();
  }, { passive: true });
  document.addEventListener('pointerup', event => {
    if (pressed && event.pointerId === pressed.id) releaseTimer = setTimeout(clearPress, 180);
  }, { passive: true });
  document.addEventListener('pointercancel', clearPress, { passive: true });
  window.addEventListener('blur', clearPress);
  document.addEventListener('visibilitychange', () => { if (document.hidden) clearPress(); });
  const photos = window.galleryPhotos || [];
  const photoWord = count => count % 10 === 1 && count % 100 !== 11 ? 'фотография' : count % 10 >= 2 && count % 10 <= 4 && !(count % 100 >= 12 && count % 100 <= 14) ? 'фотографии' : 'фотографий';
  document.querySelector('#photo-count').textContent = `${photos.length} ${photoWord(photos.length)}`;
  const preferredCategories = ['Декорации', 'Коммерческие мероприятия', 'Концерты', 'Фестивали', 'Шоу', 'Бекстейдж'];
  const categoryRank = category => preferredCategories.includes(category) ? preferredCategories.indexOf(category) : preferredCategories.length;
  const categoryNames = [...new Set(photos.map(photo => photo.category))].sort((a, b) => categoryRank(a) - categoryRank(b));
  const labels = { 'Коммерческие мероприятия': 'Для брендов', 'Бекстейдж': 'Бэкстейдж' };
  const curated = [12, 33, 30, 8, 18, 2, 7, 34, 28, 17, 23, 38];
  const ordered = [...photos].sort((a, b) => (curated.includes(a.id) ? curated.indexOf(a.id) : a.id + 100) - (curated.includes(b.id) ? curated.indexOf(b.id) : b.id + 100));
  const gallery = document.querySelector('.gallery');
  const filters = document.querySelector('.filters');
  const more = document.querySelector('.load-more');
  const status = document.querySelector('.gallery-status');
  const lightbox = document.querySelector('.lightbox');
  const largeImage = document.querySelector('.lightbox-image');
  let selected = 'Все работы', visibleCount = 6, currentIndex = 0, lastFocus;
  let matching = ordered;
  const label = category => labels[category] || category;

  ['Все работы', ...categoryNames].forEach(category => {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'filter';
    button.dataset.category = category;
    button.setAttribute('aria-pressed', String(category === selected));
    button.append(document.createTextNode(label(category)));
    const count = document.createElement('small');
    count.textContent = category === 'Все работы' ? photos.length : photos.filter(p => p.category === category).length;
    button.append(count);
    button.addEventListener('click', () => {
      selected = category; visibleCount = 6;
      matching = category === 'Все работы' ? ordered : ordered.filter(p => p.category === category);
      filters.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
      render();
    });
    filters.append(button);
  });

  function render(append = false) {
    const start = append ? gallery.children.length : 0;
    if (!append) gallery.replaceChildren();
    matching.slice(start, visibleCount).forEach((photo, offset) => {
      const index = start + offset;
      const card = document.createElement('figure'); card.className = 'gallery-card';
      const button = document.createElement('button'); button.className = 'gallery-image-button'; button.type = 'button';
      button.setAttribute('aria-label', `Открыть фото: ${label(photo.category)}, ${index + 1}`);
      const img = document.createElement('img');
      img.src = photo.small;
      img.srcset = photo.smallWidth === photo.largeWidth ? '' : `${photo.small} ${photo.smallWidth}w, ${photo.large} ${photo.largeWidth}w`;
      img.sizes = '(min-width: 1024px) 30vw, (min-width: 640px) 45vw, 90vw';
      img.alt = `${label(photo.category)} — работа мастерской Какое-то медиа`;
      img.width = photo.width; img.height = photo.height; img.loading = 'lazy'; img.decoding = 'async';
      const arrow = document.createElement('span'); arrow.className = 'image-open'; arrow.textContent = '↗'; arrow.setAttribute('aria-hidden', 'true');
      button.append(img, arrow);
      button.addEventListener('click', () => { currentIndex = index; showPhoto(); openDialog(lightbox, button); });
      const caption = document.createElement('figcaption');
      const name = document.createElement('span'); name.textContent = label(photo.category);
      const number = document.createElement('span'); number.textContent = `№ ${String(photo.id + 1).padStart(2, '0')}`;
      caption.append(name, number); card.append(button, caption); gallery.append(card);
    });
    more.hidden = visibleCount >= matching.length;
    status.textContent = `${label(selected)}: показано ${Math.min(visibleCount, matching.length)} из ${matching.length} фотографий`;
  }
  more.addEventListener('click', () => {
    const firstNew = gallery.children.length;
    visibleCount += 6; render(true);
    gallery.children[firstNew]?.querySelector('button').focus({ preventScroll: true });
  });
  function openDialog(dialog, trigger = document.activeElement) {
    lastFocus = trigger;
    dialog.showModal(); document.body.classList.add('modal-open');
  }
  function showPhoto() {
    const photo = matching[currentIndex];
    document.querySelector('.lightbox-stage').dataset.loading = 'true';
    largeImage.src = photo.large;
    largeImage.alt = `${label(photo.category)} — фотография ${currentIndex + 1} из ${matching.length}`;
    document.querySelector('.lightbox-caption').textContent = `${label(photo.category)} · ${currentIndex + 1} / ${matching.length}`;
  }
  largeImage.addEventListener('load', () => { document.querySelector('.lightbox-stage').dataset.loading = 'false'; });
  largeImage.addEventListener('error', () => { document.querySelector('.lightbox-stage').dataset.loading = 'false'; document.querySelector('.lightbox-caption').textContent = 'Не удалось загрузить фото. Попробуйте перейти к следующему.'; });
  function step(amount) { currentIndex = (currentIndex + amount + matching.length) % matching.length; showPhoto(); }
  document.querySelector('.lightbox-prev').addEventListener('click', () => step(-1));
  document.querySelector('.lightbox-next').addEventListener('click', () => step(1));
  document.querySelector('.lightbox-close').addEventListener('click', () => lightbox.close());
  lightbox.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); step(event.key === 'ArrowLeft' ? -1 : 1); }
  });
  let touchStart = null;
  largeImage.addEventListener('touchstart', e => { touchStart = e.touches.length === 1 ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : null; }, { passive: true });
  largeImage.addEventListener('touchend', e => {
    if (!touchStart || !e.changedTouches.length) return;
    const dx = e.changedTouches[0].clientX - touchStart.x, dy = e.changedTouches[0].clientY - touchStart.y;
    if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) step(dx < 0 ? 1 : -1);
    touchStart = null;
  }, { passive: true });
  largeImage.addEventListener('touchcancel', () => { touchStart = null; }, { passive: true });
  const contact = document.querySelector('.contact-dialog');
  document.querySelectorAll('[data-social]').forEach(link => link.addEventListener('click', event => {
    event.preventDefault();
    document.querySelector('#contact-dialog-title').textContent = `${link.dataset.social} — скоро!`;
    document.querySelector('#contact-dialog-description').textContent = 'Здесь появится ссылка на наш профиль. Пока это демонстрационная кнопка — контакты ещё не добавлены.';
    openDialog(contact, link);
  }));
  document.querySelectorAll('.contact-close,.contact-ok').forEach(button => button.addEventListener('click', () => contact.close()));
  [lightbox, contact].forEach(dialog => {
    dialog.addEventListener('close', () => { document.body.classList.remove('modal-open'); lastFocus?.focus({ preventScroll: true }); });
    dialog.addEventListener('click', event => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom || dialog === lightbox) dialog.close();
    });
  });
  render();
})();
