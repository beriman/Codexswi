(function () {
  function normalise(value) {
    return (value || "").toString().toLowerCase().normalize("NFD").replace(/\p{Diacritic}/gu, "");
  }

  function bindProductFilters() {
    const buttons = document.querySelectorAll("[data-product-filter]");
    const rows = document.querySelectorAll("[data-product-row]");
    const searchInput = document.querySelector("[data-product-search]");
    let activeFilter = "semua";

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

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.dataset.productFilter;
        if (!target) return;
        activeFilter = target;
        buttons.forEach((chip) => {
          const isActive = chip === button;
          chip.classList.toggle("is-active", isActive);
          chip.setAttribute("aria-selected", String(isActive));
        });
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
    const buttons = document.querySelectorAll("[data-order-filter]");
    const rows = document.querySelectorAll("[data-order-row]");
    const searchInput = document.querySelector("[data-order-search]");
    let activeFilter = "semua";

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

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.dataset.orderFilter;
        if (!target) return;
        activeFilter = target;
        buttons.forEach((chip) => {
          const isActive = chip === button;
          chip.classList.toggle("is-active", isActive);
          chip.setAttribute("aria-selected", String(isActive));
        });
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
    const buttons = document.querySelectorAll("[data-analytics-range]");
    const panels = document.querySelectorAll("[data-analytics-panel]");

    buttons.forEach((button) => {
      button.addEventListener("click", () => {
        const target = button.dataset.analyticsRange;
        if (!target) return;
        buttons.forEach((chip) => {
          const isActive = chip === button;
          chip.classList.toggle("is-active", isActive);
          chip.setAttribute("aria-selected", String(isActive));
        });
        panels.forEach((panel) => {
          const isMatch = panel.dataset.analyticsPanel === target;
          panel.classList.toggle("is-hidden", !isMatch);
          if (isMatch) {
            panel.removeAttribute("hidden");
          } else {
            panel.setAttribute("hidden", "hidden");
          }
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
