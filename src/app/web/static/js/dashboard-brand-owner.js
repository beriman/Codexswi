(function () {
  function normalise(value) {
    return (value || "").toString().toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "");
  }

  function activateTabGroup(
    buttons,
    targetKey,
    { buttonDatasetKey, panels, panelDatasetKey, shouldFocus = true } = {}
  ) {
    let activeButton = null;
    buttons.forEach((button) => {
      const key = buttonDatasetKey ? button.dataset[buttonDatasetKey] : undefined;
      const isActive = key === targetKey;
      button.classList.toggle("is-active", isActive);
      button.setAttribute("aria-selected", String(isActive));
      button.setAttribute("tabindex", isActive ? "0" : "-1");
      if (isActive) {
        activeButton = button;
      }
    });

    if (panels && panelDatasetKey) {
      panels.forEach((panel) => {
        const panelKey = panel.dataset[panelDatasetKey];
        const isMatch = panelKey === targetKey;
        panel.classList.toggle("is-hidden", !isMatch);
        if (isMatch) {
          panel.removeAttribute("hidden");
          panel.setAttribute("aria-hidden", "false");
        } else {
          panel.setAttribute("hidden", "hidden");
          panel.setAttribute("aria-hidden", "true");
        }
      });
    }

    if (activeButton && shouldFocus) {
      activeButton.focus();
    }

    return activeButton;
  }

  function bindProductFilters() {
    const buttons = Array.from(document.querySelectorAll("[data-product-filter]"));
    const rows = document.querySelectorAll("[data-product-row]");
    const searchInput = document.querySelector("[data-product-search]");
    if (!buttons.length) return;
    let activeFilter =
      buttons.find((button) => button.classList.contains("is-active"))?.dataset.productFilter ||
      "semua";

    activateTabGroup(buttons, activeFilter, {
      buttonDatasetKey: "productFilter",
      shouldFocus: false,
    });

    function apply() {
      const query = normalise(searchInput ? searchInput.value.trim() : "");
      rows.forEach((row) => {
        const status = row.dataset.status || "";
        const name = normalise(row.dataset.name || "");
        const sku = normalise(row.dataset.sku || "");
        const matchesFilter = activeFilter === "semua" || status === activeFilter;
        const matchesQuery = !query || name.includes(query) || sku.includes(query);
        const shouldShow = matchesFilter && matchesQuery;
        row.hidden = !shouldShow;
      });
    }

    buttons.forEach((button, index) => {
      button.addEventListener("click", () => {
        const target = button.dataset.productFilter;
        if (!target) return;
        activeFilter = target;
        activateTabGroup(buttons, target, { buttonDatasetKey: "productFilter" });
        apply();
      });

      button.addEventListener("keydown", (event) => {
        const { key } = event;
        const isNext = key === "ArrowRight" || key === "ArrowDown";
        const isPrev = key === "ArrowLeft" || key === "ArrowUp";
        if (!isNext && !isPrev) return;
        event.preventDefault();
        const offset = isNext ? 1 : -1;
        const nextIndex = (index + offset + buttons.length) % buttons.length;
        const nextButton = buttons[nextIndex];
        const target = nextButton?.dataset.productFilter;
        if (!target) return;
        activeFilter = target;
        activateTabGroup(buttons, target, { buttonDatasetKey: "productFilter" });
        apply();
      });
    });

    if (searchInput) {
      ["input", "change"].forEach((eventName) => {
        searchInput.addEventListener(eventName, apply);
      });
    }
  }

  function bindOrderFilters() {
    const buttons = Array.from(document.querySelectorAll("[data-order-filter]"));
    const rows = document.querySelectorAll("[data-order-row]");
    const searchInput = document.querySelector("[data-order-search]");
    if (!buttons.length) return;
    let activeFilter =
      buttons.find((button) => button.classList.contains("is-active"))?.dataset.orderFilter ||
      "semua";

    activateTabGroup(buttons, activeFilter, {
      buttonDatasetKey: "orderFilter",
      shouldFocus: false,
    });

    function apply() {
      const query = normalise(searchInput ? searchInput.value.trim() : "");
      rows.forEach((row) => {
        const status = normalise(row.dataset.status || "");
        const invoice = normalise(row.dataset.invoice || "");
        const customer = normalise(row.dataset.customer || "");
        const matchesFilter = activeFilter === "semua" || status === normalise(activeFilter);
        const matchesQuery = !query || invoice.includes(query) || customer.includes(query);
        const shouldShow = matchesFilter && matchesQuery;
        row.hidden = !shouldShow;
      });
    }

    buttons.forEach((button, index) => {
      button.addEventListener("click", () => {
        const target = button.dataset.orderFilter;
        if (!target) return;
        activeFilter = target;
        activateTabGroup(buttons, target, { buttonDatasetKey: "orderFilter" });
        apply();
      });

      button.addEventListener("keydown", (event) => {
        const { key } = event;
        const isNext = key === "ArrowRight" || key === "ArrowDown";
        const isPrev = key === "ArrowLeft" || key === "ArrowUp";
        if (!isNext && !isPrev) return;
        event.preventDefault();
        const offset = isNext ? 1 : -1;
        const nextIndex = (index + offset + buttons.length) % buttons.length;
        const nextButton = buttons[nextIndex];
        const target = nextButton?.dataset.orderFilter;
        if (!target) return;
        activeFilter = target;
        activateTabGroup(buttons, target, { buttonDatasetKey: "orderFilter" });
        apply();
      });
    });

    if (searchInput) {
      ["input", "change"].forEach((eventName) => {
        searchInput.addEventListener(eventName, apply);
      });
    }
  }

  function renderChart(chartEl) {
    const pointsAttr = chartEl.dataset.chartPoints;
    if (!pointsAttr) return;

    const points = pointsAttr
      .split(",")
      .map((value) => Number.parseFloat(value.trim()))
      .filter((value) => Number.isFinite(value));

    if (points.length < 2) return;

    const labelsAttr = chartEl.dataset.chartLabels || "";
    const labels = labelsAttr.split(",").map((label) => label.trim());

    const maxValue = Math.max(...points);
    const minValue = Math.min(...points);
    const range = maxValue - minValue || 1;

    const svgWidth = 100;
    const svgHeight = 40;
    const verticalPadding = 6;
    const usableHeight = svgHeight - verticalPadding * 2;
    const stepX = svgWidth / (points.length - 1);

    const line = chartEl.querySelector("[data-chart-line]");
    const area = chartEl.querySelector("[data-chart-area]");

    if (!line || !area) return;

    const coordinates = points.map((value, index) => {
      const normalised = (value - minValue) / range;
      const y = svgHeight - verticalPadding - normalised * usableHeight;
      const x = index * stepX;
      return [x, y];
    });

    const polylinePoints = coordinates.map(([x, y]) => `${x},${y}`).join(" ");
    line.setAttribute("points", polylinePoints);

    const areaPath = [
      `M0 ${svgHeight}`,
      `L${coordinates[0][0]} ${coordinates[0][1]}`,
      ...coordinates.slice(1).map(([x, y]) => `L${x} ${y}`),
      `L${coordinates[coordinates.length - 1][0]} ${svgHeight}`,
      "Z",
    ].join(" ");
    area.setAttribute("d", areaPath);

    if (labels.length === points.length) {
      const existingLabels = chartEl.querySelectorAll(".chart-label");
      existingLabels.forEach((label) => label.remove());
      labels.forEach((label, index) => {
        const marker = document.createElement("span");
        marker.className = "chart-label";
        marker.textContent = label;
        marker.style.left = `${(index / (labels.length - 1 || 1)) * 100}%`;
        chartEl.appendChild(marker);
      });
    }
  }

  function initialiseAnalytics() {
    const buttons = Array.from(document.querySelectorAll("[data-analytics-range]"));
    const panels = Array.from(document.querySelectorAll("[data-analytics-panel]"));
    if (!buttons.length) return;

    let activeRange =
      buttons.find((button) => button.classList.contains("is-active"))?.dataset.analyticsRange ||
      buttons[0]?.dataset.analyticsRange;

    activateTabGroup(buttons, activeRange, {
      buttonDatasetKey: "analyticsRange",
      panels,
      panelDatasetKey: "analyticsPanel",
      shouldFocus: false,
    });

    buttons.forEach((button, index) => {
      button.addEventListener("click", () => {
        const target = button.dataset.analyticsRange;
        if (!target) return;
        activeRange = target;
        activateTabGroup(buttons, target, {
          buttonDatasetKey: "analyticsRange",
          panels,
          panelDatasetKey: "analyticsPanel",
        });
      });

      button.addEventListener("keydown", (event) => {
        const { key } = event;
        const isNext = key === "ArrowRight" || key === "ArrowDown";
        const isPrev = key === "ArrowLeft" || key === "ArrowUp";
        if (!isNext && !isPrev) return;
        event.preventDefault();
        const offset = isNext ? 1 : -1;
        const nextIndex = (index + offset + buttons.length) % buttons.length;
        const nextButton = buttons[nextIndex];
        const target = nextButton?.dataset.analyticsRange;
        if (!target) return;
        activeRange = target;
        activateTabGroup(buttons, target, {
          buttonDatasetKey: "analyticsRange",
          panels,
          panelDatasetKey: "analyticsPanel",
        });
      });
    });

    document.querySelectorAll("[data-chart]").forEach((chartEl) => {
      renderChart(chartEl);
    });
  }

  function bindNotificationActions() {
    const list = document.querySelector("[data-notification-list]");
    if (!list) return;
    const emptyState = document.querySelector("[data-notification-empty]");

    list.addEventListener("click", (event) => {
      const target = event.target;
      if (!(target instanceof HTMLElement)) return;
      if (!target.matches("[data-dismiss-notification]")) return;
      const item = target.closest(".notification-item");
      if (!item) return;
      item.remove();
      if (!list.children.length && emptyState) {
        emptyState.hidden = false;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    bindProductFilters();
    bindOrderFilters();
    initialiseAnalytics();
    bindNotificationActions();
  });
})();
