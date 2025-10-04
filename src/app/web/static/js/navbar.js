document.addEventListener("DOMContentLoaded", () => {
  const navbars = Array.from(document.querySelectorAll(".navbar"));
  const configs = [];

  navbars.forEach((nav) => {
    const toggle = nav.querySelector(".navbar-toggle");
    const collapsible = nav.querySelector(".navbar-collapsible");

    if (!toggle || !collapsible) {
      return;
    }

    const setOpenState = (isOpen) => {
      nav.dataset.open = isOpen ? "true" : "false";
      toggle.setAttribute("aria-expanded", isOpen ? "true" : "false");
      collapsible.setAttribute("aria-hidden", isOpen ? "false" : "true");

      if (isOpen) {
        nav.classList.add("navbar--open");
      } else {
        nav.classList.remove("navbar--open");
      }
    };

    setOpenState(false);

    const toggleOpen = () => {
      const isOpen = nav.dataset.open === "true";
      setOpenState(!isOpen);
    };

    const close = () => setOpenState(false);

    toggle.addEventListener("click", (event) => {
      event.preventDefault();
      toggleOpen();
    });

    collapsible.addEventListener("click", (event) => {
      const interactive = event.target.closest("a, button");
      if (!interactive || interactive === toggle) {
        return;
      }
      close();
    });

    configs.push({ toggle, close, nav });
  });

  if (configs.length === 0) {
    return;
  }

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") {
      return;
    }

    configs.forEach(({ nav, toggle, close }) => {
      if (nav.dataset.open === "true") {
        close();
        toggle.focus();
      }
    });
  });
});
