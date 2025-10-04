(function () {
  const tabLists = document.querySelectorAll('[role="tablist"]');

  if (!tabLists.length) {
    return;
  }

  const activateTab = (tabs, panels, tab, { focus = true } = {}) => {
    const panelId = tab.getAttribute('aria-controls');
    const nextPanel = panelId ? document.getElementById(panelId) : null;

    tabs.forEach((candidate) => {
      const isSelected = candidate === tab;
      candidate.setAttribute('aria-selected', String(isSelected));
      candidate.tabIndex = isSelected ? 0 : -1;
      candidate.classList.toggle('is-active', isSelected);
    });

    panels.forEach((panel) => {
      if (!panel) {
        return;
      }

      const shouldShow = panel === nextPanel;

      if (shouldShow) {
        panel.removeAttribute('hidden');
      } else {
        panel.setAttribute('hidden', '');
      }
    });

    if (focus) {
      tab.focus();
    }
  };

  tabLists.forEach((tabList) => {
    const tabs = Array.from(tabList.querySelectorAll('[role="tab"]'));
    const panels = tabs.map((tab) => {
      const panelId = tab.getAttribute('aria-controls');
      return panelId ? document.getElementById(panelId) : null;
    });

    if (!tabs.length) {
      return;
    }

    const initiallySelected =
      tabs.find((tab) => tab.getAttribute('aria-selected') === 'true') || tabs[0];

    activateTab(tabs, panels, initiallySelected, { focus: false });

    tabList.addEventListener('click', (event) => {
      const target = event.target.closest('[role="tab"]');

      if (!target || !tabList.contains(target)) {
        return;
      }

      event.preventDefault();
      activateTab(tabs, panels, target);
    });

    tabList.addEventListener('keydown', (event) => {
      const { key } = event;
      const currentIndex = tabs.indexOf(document.activeElement);

      let nextIndex = null;

      if (key === 'ArrowRight' || key === 'ArrowDown') {
        nextIndex = (currentIndex + 1) % tabs.length;
      } else if (key === 'ArrowLeft' || key === 'ArrowUp') {
        nextIndex = (currentIndex - 1 + tabs.length) % tabs.length;
      } else if (key === 'Home') {
        nextIndex = 0;
      } else if (key === 'End') {
        nextIndex = tabs.length - 1;
      }

      if (nextIndex === null) {
        return;
      }

      event.preventDefault();
      const nextTab = tabs[nextIndex];
      activateTab(tabs, panels, nextTab);
    });
  });
})();
