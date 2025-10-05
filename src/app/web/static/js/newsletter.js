(function () {
  document.addEventListener("DOMContentLoaded", () => {
    const form = document.querySelector(".newsletter-form");
    if (!form) {
      return;
    }

    const statusRegion = form.querySelector("#newsletter-status");
    const submitButton = form.querySelector("button[type='submit']");

    const setStatus = (message, tone) => {
      if (!statusRegion) {
        return;
      }
      statusRegion.textContent = message;
      statusRegion.dataset.tone = tone;
    };

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      event.stopPropagation();

      if (!submitButton) {
        return;
      }

      const formData = new FormData(form);
      submitButton.disabled = true;
      setStatus("Mengirim...", "pending");

      try {
        const response = await fetch(form.action, {
          method: "POST",
          headers: {
            Accept: "application/json",
          },
          body: formData,
        });

        const payload = await response.json().catch(() => null);

        if (response.ok) {
          const successMessage = payload?.message ?? "Terima kasih! Email kamu sudah terdaftar.";
          setStatus(successMessage, "success");
          form.reset();
        } else {
          const errorMessage = payload?.message ?? "Alamat email tidak valid. Coba lagi.";
          setStatus(errorMessage, "error");
        }
      } catch (error) {
        setStatus("Terjadi kendala jaringan. Silakan coba lagi.", "error");
      } finally {
        submitButton.disabled = false;
      }
    });
  });
})();
