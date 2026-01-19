(function () {
  const body = document.body;
  if (!body) return;

  const prevUrl = body.getAttribute('data-prev-url');
  const nextUrl = body.getAttribute('data-next-url');

  // Only enable swipe if both URLs are present
  if (!prevUrl || !nextUrl) return;

  let startX = null;
  let startY = null;

  function onTouchStart(e) {
    const t = e.touches[0];
    startX = t.clientX;
    startY = t.clientY;
  }

  function onTouchEnd(e) {
    if (startX === null || startY === null) return;

    const t = e.changedTouches[0];
    const dx = t.clientX - startX;
    const dy = t.clientY - startY;

    // Mostly-horizontal swipe
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      window.location.href = (dx < 0) ? nextUrl : prevUrl;
    }

    startX = null;
    startY = null;
  }

  document.addEventListener('touchstart', onTouchStart, { passive: true });
  document.addEventListener('touchend', onTouchEnd, { passive: true });
})();
