(() => {
  'use strict';
  const photos = window.galleryPhotos || [];
  const categoryNames = ['Декорации', 'Коммерческие мероприятия', 'Концерты', 'Фестивали', 'Шоу', 'Бекстейдж'];
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
      img.src = photo.small; img.srcset = `${photo.small} ${photo.smallWidth}w, ${photo.large} ${photo.largeWidth}w`;
      img.sizes = '(min-width: 1024px) 30vw, (min-width: 640px) 45vw, 90vw';
      img.alt = `${label(photo.category)} — работа мастерской дИАБЕТаРТгуу`;
      img.width = photo.width; img.height = photo.height; img.loading = 'lazy'; img.decoding = 'async';
      const arrow = document.createElement('span'); arrow.className = 'image-open'; arrow.textContent = '↗'; arrow.setAttribute('aria-hidden', 'true');
      button.append(img, arrow);
      button.addEventListener('click', () => { currentIndex = index; openDialog(lightbox); showPhoto(); });
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
  function openDialog(dialog) {
    lastFocus = document.activeElement;
    dialog.showModal(); document.body.classList.add('modal-open');
  }
  function showPhoto() {
    const photo = matching[currentIndex];
    largeImage.src = photo.large;
    largeImage.alt = `${label(photo.category)} — фотография ${currentIndex + 1} из ${matching.length}`;
    document.querySelector('.lightbox-caption').textContent = `${label(photo.category)} · ${currentIndex + 1} / ${matching.length}`;
  }
  function step(amount) { currentIndex = (currentIndex + amount + matching.length) % matching.length; showPhoto(); }
  document.querySelector('.lightbox-prev').addEventListener('click', () => step(-1));
  document.querySelector('.lightbox-next').addEventListener('click', () => step(1));
  document.querySelector('.lightbox-close').addEventListener('click', () => lightbox.close());
  lightbox.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft' || event.key === 'ArrowRight') { event.preventDefault(); step(event.key === 'ArrowLeft' ? -1 : 1); }
  });
  let touchX = null;
  largeImage.addEventListener('touchstart', e => { touchX = e.touches.length === 1 ? e.touches[0].clientX : null; }, { passive: true });
  largeImage.addEventListener('touchend', e => { if (touchX !== null && Math.abs(e.changedTouches[0].clientX - touchX) > 50) step(e.changedTouches[0].clientX < touchX ? 1 : -1); touchX = null; }, { passive: true });
  const contact = document.querySelector('.contact-dialog');
  document.querySelector('#contact-open').addEventListener('click', () => openDialog(contact));
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
