(() => {
  'use strict';
  const root = document.currentScript.dataset.brandRoot;
  const key = 'hub-i3-brand-preview';
  const names = ['Azul e roxo', 'Verde e amarelo', 'Conexoes - monocromatico'];
  let current = 1, timer;
  try { const saved = Number(sessionStorage.getItem(key)); if ([1,2,3].includes(saved)) current = saved; } catch (_) {}
  function apply(notify = false) {
    document.documentElement.dataset.hubBrand = String(current);
    const favicon = document.getElementById('hub-brand-favicon');
    if (favicon) favicon.href = root + current + '-icon.svg?v=3';
    document.querySelectorAll('[data-hub-logo]').forEach(img => {
      img.src = root + current + (img.dataset.hubLogo === 'footer' ? '-footer.svg' : '-logo.svg') + '?v=3';
    });
    if (notify && document.body) {
      let el = document.getElementById('hub-brand-notice');
      if (!el) { el = document.createElement('div'); el.id = 'hub-brand-notice'; el.setAttribute('role','status'); document.body.append(el); }
      el.textContent = `Proposta ${current}/3: ${names[current-1]}`;
      clearTimeout(timer); timer = setTimeout(() => el.remove(), 2400);
    }
  }
  apply();
  document.addEventListener('DOMContentLoaded', () => apply());
  document.addEventListener('keydown', e => {
    if (!e.ctrlKey || e.altKey || e.metaKey || e.repeat || e.isComposing) return;
    if (!['ç','Ç'].includes(e.key) && !(e.code === 'Semicolon' && e.key !== ';' && e.key !== ':')) return;
    e.preventDefault(); current = current % 3 + 1;
    try { sessionStorage.setItem(key, String(current)); } catch (_) {}
    apply(true);
  });
})();
