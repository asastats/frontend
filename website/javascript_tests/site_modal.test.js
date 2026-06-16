const jquery = require('../static/js/jquery-2.2.4.min.js');

window.$ = jquery;

$.prototype.sidenav = jest.fn();
$.prototype.modal = jest.fn();

const site = require('../static/js/site.js');

const TABS_HTML =
  '<ul class="tabs"><li class="tab">' +
  '<a class="active" href="#modal-tab-login">Log in</a></li></ul>';

function withFooter(inner) {
  return '<footer id="footer" data-mode="light"></footer>' + inner;
}

function modalDom() {
  return withFooter('<div id="modalLogin" class="modal">' + TABS_HTML + '</div>');
}

function makeTabs() {
  return { updateTabIndicator: jest.fn() };
}

beforeEach(() => {
  document.body.innerHTML = withFooter('');
  delete global.M;
});

describe("in SECTION: Proprietary widgets - initLoginModalTabs", function () {
  // # structure guards
  it('does nothing when the login modal is absent', function () {
    document.body.innerHTML = withFooter('<div id="other"></div>');
    global.M = { Tabs: { getInstance: jest.fn(), init: jest.fn() } };
    expect(() => site.initLoginModalTabs()).not.toThrow();
    expect(global.M.Tabs.init).not.toHaveBeenCalled();
  });

  it('does nothing when the modal has no tabs', function () {
    document.body.innerHTML = withFooter('<div id="modalLogin" class="modal"></div>');
    global.M = { Tabs: { getInstance: jest.fn(), init: jest.fn() } };
    site.initLoginModalTabs();
    expect(global.M.Tabs.init).not.toHaveBeenCalled();
  });

  it('does nothing when Materialize (M) is undefined', function () {
    document.body.innerHTML = modalDom();
    global.M = undefined;
    expect(() => site.initLoginModalTabs()).not.toThrow();
  });

  it('does nothing when M.Tabs is undefined', function () {
    document.body.innerHTML = modalDom();
    global.M = {};
    expect(() => site.initLoginModalTabs()).not.toThrow();
  });

  // # happy paths
  it('reuses an existing Tabs instance and wires the open hook', function () {
    document.body.innerHTML = modalDom();
    const tabs = makeTabs();
    const modalInstance = { options: {} };
    global.M = {
      Tabs: { getInstance: jest.fn(() => tabs), init: jest.fn() },
      Modal: { getInstance: jest.fn(() => modalInstance) }
    };
    site.initLoginModalTabs();
    expect(global.M.Tabs.getInstance).toHaveBeenCalled();
    expect(global.M.Tabs.init).not.toHaveBeenCalled();
    expect(typeof modalInstance.options.onOpenEnd).toBe('function');
    modalInstance.options.onOpenEnd();
    expect(tabs.updateTabIndicator).toHaveBeenCalledTimes(1);
  });

  it('initializes tabs when none exists; no modal instance means no hook', function () {
    document.body.innerHTML = modalDom();
    const tabs = makeTabs();
    global.M = {
      Tabs: { getInstance: jest.fn(() => undefined), init: jest.fn(() => tabs) }
    };
    site.initLoginModalTabs();
    expect(global.M.Tabs.init).toHaveBeenCalled();
  });

  it('skips the hook when the modal instance is not yet created', function () {
    document.body.innerHTML = modalDom();
    const tabs = makeTabs();
    global.M = {
      Tabs: { getInstance: jest.fn(() => undefined), init: jest.fn(() => tabs) },
      Modal: { getInstance: jest.fn(() => null) }
    };
    expect(() => site.initLoginModalTabs()).not.toThrow();
    expect(global.M.Modal.getInstance).toHaveBeenCalled();
  });
});
