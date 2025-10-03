(function () {
  function copyToClipboard(text) {
    if (!text) return Promise.resolve(false);
    if (navigator.clipboard && typeof navigator.clipboard.writeText === "function") {
      return navigator.clipboard
        .writeText(text)
        .then(
          function () {
            return true;
          },
          function () {
            return legacyCopy(text);
          }
        );
    }
    return Promise.resolve(legacyCopy(text));
  }

  function legacyCopy(text) {
    var textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.setAttribute("readonly", "readonly");
    textarea.style.position = "fixed";
    textarea.style.top = "-1000px";
    document.body.appendChild(textarea);
    textarea.select();
    var succeeded = false;
    try {
      succeeded = document.execCommand("copy");
    } catch (err) {
      succeeded = false;
    }
    document.body.removeChild(textarea);
    return succeeded;
  }

  function toggleState(element, attribute, state) {
    if (!element) return;
    element.setAttribute(attribute, String(Boolean(state)));
    if (state) {
      element.classList.add("is-active");
    } else {
      element.classList.remove("is-active");
    }
  }

  function activateTab(trigger, options) {
    if (!trigger) return;
    var opts = options || {};
    var container = trigger.closest("[data-tab-group]");
    if (!container) return;
    var tabs = container.querySelectorAll('[data-action="jump-section"]');
    Array.prototype.forEach.call(tabs, function (tab) {
      tab.classList.remove("is-active");
      tab.setAttribute("aria-selected", "false");
    });
    trigger.classList.add("is-active");
    trigger.setAttribute("aria-selected", "true");
    if (!opts.silent) {
      ensureTabVisible(container, trigger);
    }
    requestFrame(function () {
      updateTabIndicator(container, trigger);
    });
  }

  function scrollToTarget(targetSelector) {
    if (!targetSelector) return false;
    var target = document.querySelector(targetSelector);
    if (!target) return false;
    if (typeof target.scrollIntoView === "function") {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      return true;
    }
    return false;
  }

  function handleAction(trigger, action, event) {
    switch (action) {
      case "share-report": {
        var shareUrl = trigger.dataset.shareUrl || window.location.href;
        copyToClipboard(shareUrl).then(function (success) {
          var message = success
            ? trigger.dataset.feedbackSuccess || "Tautan laporan disalin"
            : trigger.dataset.feedbackError || "Tidak dapat menyalin tautan";
          trigger.setAttribute("data-feedback", message);
          trigger.classList.add("has-feedback");
          window.setTimeout(function () {
            trigger.classList.remove("has-feedback");
            trigger.removeAttribute("data-feedback");
          }, 2000);
        });
        break;
      }
      case "refresh-snapshot": {
        window.location.reload();
        break;
      }
      case "focus-mode": {
        var focusTarget = trigger.dataset.focusTarget;
        if (focusTarget) {
          window.location.href = focusTarget;
          return;
        }
        document.body.classList.toggle("is-focus-mode");
        toggleState(trigger, "aria-pressed", document.body.classList.contains("is-focus-mode"));
        break;
      }
      case "bulk-action": {
        var targetSelector = trigger.dataset.bulkTarget;
        var bulkContainer = targetSelector ? document.querySelector(targetSelector) : null;
        var isActive = trigger.getAttribute("aria-pressed") === "true";
        isActive = !isActive;
        toggleState(trigger, "aria-pressed", isActive);
        if (bulkContainer) {
          bulkContainer.classList.toggle("is-bulk-select", isActive);
        }
        break;
      }
      case "invite-resend": {
        var email = trigger.dataset.inviteEmail || "pengguna";
        dispatchToast("Undangan dikirim ulang ke " + email + ".");
        break;
      }
      case "invite-cancel": {
        var cancelEmail = trigger.dataset.inviteEmail || "pengguna";
        dispatchToast("Undangan untuk " + cancelEmail + " dibatalkan.");
        break;
      }
      case "invite-open": {
        dispatchToast("Panel undangan dibuka.");
        break;
      }
      case "jump-section": {
        if (event && typeof event.preventDefault === "function") {
          event.preventDefault();
        }
        var targetSelector = trigger.dataset.target || trigger.getAttribute("href");
        var scrolled = scrollToTarget(targetSelector);
        if (scrolled) {
          activateTab(trigger);
        } else if (targetSelector) {
          window.location.hash = targetSelector.replace(/^#/, "");
        }
        return true;
      }
      case "scroll-top": {
        if (event && typeof event.preventDefault === "function") {
          event.preventDefault();
        }
        if (typeof window.scrollTo === "function") {
          window.scrollTo({ top: 0, behavior: "smooth" });
        } else {
          window.scrollTo(0, 0);
        }
        return true;
      }
      case "view-sop":
      case "add-moderator":
      default: {
        break;
      }
    }
  }

  function dispatchToast(message) {
    if (!message) return;
    var event;
    try {
      event = new CustomEvent("mod:toast", { detail: { message: message } });
    } catch (error) {
      // IE fallback
      event = document.createEvent("CustomEvent");
      event.initCustomEvent("mod:toast", false, false, { message: message });
    }
    document.dispatchEvent(event);
  }

  function bindActions() {
    document.addEventListener("click", function (event) {
      var target = event.target;
      if (!(target instanceof Element)) {
        return;
      }
      var trigger = target.closest("[data-action]");
      if (!trigger) {
        return;
      }
      var action = trigger.dataset.action;
      if (!action) {
        return;
      }
      var handled = handleAction(trigger, action, event);
      if (handled === true && typeof event.preventDefault === "function") {
        event.preventDefault();
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindActions();
    setupTabGroups();
    updateAllTabIndicators();
  });

  if (typeof window !== "undefined") {
    window.addEventListener("resize", function () {
      updateAllTabIndicators();
    });
    window.addEventListener("orientationchange", function () {
      updateAllTabIndicators();
    });
  }

  function ensureTabVisible(container, tab) {
    if (!container || !tab) return;
    var scroller = container.querySelector(".tab-scroller");
    if (!scroller) {
      return;
    }
    var left = tab.offsetLeft;
    var right = left + tab.offsetWidth;
    var viewStart = scroller.scrollLeft;
    var viewEnd = viewStart + scroller.clientWidth;
    var targetLeft = null;

    if (left < viewStart) {
      targetLeft = left;
    } else if (right > viewEnd) {
      targetLeft = right - scroller.clientWidth;
    }

    if (targetLeft === null) {
      return;
    }

    if (typeof scroller.scrollTo === "function") {
      scroller.scrollTo({ left: targetLeft, behavior: "smooth" });
    } else {
      scroller.scrollLeft = targetLeft;
    }
  }

  function requestFrame(callback) {
    if (typeof window !== "undefined" && typeof window.requestAnimationFrame === "function") {
      window.requestAnimationFrame(callback);
      return;
    }
    callback();
  }

  function updateTabIndicator(container, activeTab) {
    if (!container || !activeTab) return;
    var indicator = container.querySelector(".tab-indicator");
    if (!indicator) return;
    var scroller = container.querySelector(".tab-scroller") || container;
    var activeRect = activeTab.getBoundingClientRect();
    var scrollerRect = scroller.getBoundingClientRect();
    var scrollLeft = typeof scroller.scrollLeft === "number" ? scroller.scrollLeft : 0;
    var offset = activeRect.left - scrollerRect.left + scrollLeft;
    indicator.style.transform = "translateX(" + offset + "px)";
    indicator.style.width = activeRect.width + "px";
    indicator.classList.add("is-visible");
  }

  function updateAllTabIndicators() {
    var groups = document.querySelectorAll("[data-tab-group]");
    if (!groups.length) {
      return;
    }
    requestFrame(function () {
      Array.prototype.forEach.call(groups, function (group) {
        var active = group.querySelector(".tab-link.is-active");
        if (active) {
          updateTabIndicator(group, active);
        }
      });
    });
  }

  function setupTabGroups() {
    var groups = document.querySelectorAll("[data-tab-group]");
    if (!groups.length) {
      return;
    }

    Array.prototype.forEach.call(groups, function (group) {
      var tabs = group.querySelectorAll('[data-action="jump-section"]');
      if (!tabs.length) {
        return;
      }

      var initialActive = group.querySelector(".tab-link.is-active") || tabs[0];
      if (initialActive) {
        activateTab(initialActive, { silent: true });
      }

      if (typeof IntersectionObserver !== "function") {
        return;
      }

      var tabSections = [];
      Array.prototype.forEach.call(tabs, function (tab) {
        var targetSelector = tab.dataset.target || tab.getAttribute("href");
        if (!targetSelector) {
          return;
        }
        var section = document.querySelector(targetSelector);
        if (!section) {
          return;
        }
        tabSections.push({ tab: tab, section: section });
      });

      if (!tabSections.length) {
        return;
      }

      var observer = new IntersectionObserver(
        function (entries) {
          var candidate = null;
          for (var i = 0; i < entries.length; i += 1) {
            var entry = entries[i];
            if (!entry.isIntersecting) {
              continue;
            }
            if (!candidate || entry.boundingClientRect.top < candidate.boundingClientRect.top) {
              candidate = entry;
            }
          }

          if (!candidate) {
            return;
          }

          var matched = null;
          for (var j = 0; j < tabSections.length; j += 1) {
            if (tabSections[j].section === candidate.target) {
              matched = tabSections[j];
              break;
            }
          }

          if (matched) {
            activateTab(matched.tab, { silent: true });
          }
        },
        {
          rootMargin: "-55% 0px -35% 0px",
          threshold: [0.25, 0.5, 0.75],
        }
      );

      for (var index = 0; index < tabSections.length; index += 1) {
        observer.observe(tabSections[index].section);
      }
    });
  }
})();
