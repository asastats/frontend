const reveal = require('../static/js/swap-reveal.js');

describe('swap-reveal: applySwapReveal', () => {
  afterEach(() => {
    document.body.className = '';
    document.body.innerHTML = '';
  });

  it('adds swap-enabled when the gate marker is present', () => {
    document.body.innerHTML =
      '<span id="id-swap-enabled"></span><div class="swap-asa-entry"></div>';
    expect(reveal.applySwapReveal(document)).toBe(true);
    expect(document.body.classList.contains('swap-enabled')).toBe(true);
  });

  it('leaves swap-enabled off when the marker is absent', () => {
    document.body.innerHTML = '<div class="swap-asa-entry"></div>';
    expect(reveal.applySwapReveal(document)).toBe(false);
    expect(document.body.classList.contains('swap-enabled')).toBe(false);
  });

  it('removes swap-enabled when the marker disappears', () => {
    document.body.classList.add('swap-enabled');
    document.body.innerHTML = '';
    expect(reveal.applySwapReveal(document)).toBe(false);
    expect(document.body.classList.contains('swap-enabled')).toBe(false);
  });
});
