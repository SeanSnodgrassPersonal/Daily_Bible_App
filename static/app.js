(function () {
  const root = document.body;
  if (!root) return;

  const prevUrl = root.dataset.prevUrl;
  const nextUrl = root.dataset.nextUrl;

  // Only enable swipe navigation on pages that provide URLs (e.g., day view).
  if (!prevUrl || !nextUrl) return;

  let startX = null;
  let startY = null;

  function onTouchStart(e) {
    const t = e.touches && e.touches[0];
    if (!t) return;
    startX = t.clientX;
    startY = t.clientY;
  }

  function onTouchEnd(e) {
    if (startX === null || startY === null) return;

    const t = e.changedTouches && e.changedTouches[0];
    if (!t) return;

    const dx = t.clientX - startX;
    const dy = t.clientY - startY;

    // Only treat mostly-horizontal gestures as swipes.
    if (Math.abs(dx) > 60 && Math.abs(dx) > Math.abs(dy) * 1.5) {
      window.location.href = (dx < 0) ? nextUrl : prevUrl;
    }

    startX = null;
    startY = null;
  }

  document.addEventListener('touchstart', onTouchStart, { passive: true });
  document.addEventListener('touchend', onTouchEnd, { passive: true });
})();
