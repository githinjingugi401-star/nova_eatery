document.addEventListener("DOMContentLoaded", () => {
  const cartForms = document.querySelectorAll('form[action$="/update-cart"]');

  cartForms.forEach((form) => {
    form.addEventListener("submit", (event) => {
      const submitter = event.submitter;
      const cartItem = form.closest(".cart-item");

      if (!submitter) {
        return;
      }

      if (cartItem) {
        cartItem.querySelectorAll("button").forEach((button) => {
          button.disabled = true;
        });
        cartItem.style.opacity = "0.7";
      } else {
        submitter.disabled = true;
      }

      if (submitter.classList.contains("cart-delete-btn")) {
        submitter.setAttribute("aria-label", "Removing item");
      } else {
        submitter.textContent = "…";
      }
    });
  });
});
