document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("checkoutForm");
  const checkbox = document.getElementById("mpesaConfirm");
  const submitButton = document.getElementById("submitOrderBtn");

  const updateSubmitState = () => {
    if (!submitButton) {
      return;
    }

    submitButton.disabled = !checkbox?.checked;
    submitButton.style.opacity = checkbox?.checked ? "1" : "0.5";
  };

  checkbox?.addEventListener("change", updateSubmitState);
  updateSubmitState();

  form?.addEventListener("submit", (event) => {
    const name = document.getElementById("customerName")?.value.trim();
    const phone = document.getElementById("customerPhone")?.value.trim();
    const table = document.getElementById("tableNumber")?.value;

    if (!name || !phone || !table) {
      event.preventDefault();
      alert("Please fill in all required fields.");
      return;
    }

    if (!checkbox?.checked) {
      event.preventDefault();
      alert("Please confirm you have sent the M-PESA payment.");
      return;
    }

    submitButton.textContent = "Placing order...";
    submitButton.disabled = true;
  });
});
