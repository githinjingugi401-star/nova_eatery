function startCustomerPolling(orderId) {
  const statusBadge = document.getElementById("liveStatusBadge");
  const tracker = document.getElementById("orderTracker");
  const statusOrder = ["Pending", "Preparing", "Ready", "Served"];
  const statusClasses = {
    Pending: "badge-pending",
    Preparing: "badge-preparing",
    Ready: "badge-ready",
    Served: "badge-served",
    Cancelled: "badge-cancelled",
  };

  const updateTracker = (status) => {
    const statusIndex = statusOrder.indexOf(status);

    document.querySelectorAll(".tracker-step").forEach((step, index) => {
      const dot = step.querySelector(".tracker-dot");
      if (!dot) {
        return;
      }

      if (index < statusIndex) {
        dot.className = "tracker-dot done";
        dot.textContent = "✓";
      } else if (index === statusIndex) {
        dot.className = "tracker-dot active";
        dot.textContent = index + 1;
      } else {
        dot.className = "tracker-dot";
        dot.textContent = index + 1;
      }
    });
  };

  const poll = async () => {
    try {
      const response = await fetch(`/api/order-status/${orderId}`);
      const data = await response.json();

      if (data.status && statusBadge) {
        statusBadge.className = `badge ${statusClasses[data.status] || ""}`;
        statusBadge.textContent = data.status;
      }

      if (tracker) {
        updateTracker(data.status);
      }

      if (data.status === "Served" || data.status === "Cancelled") {
        clearInterval(pollInterval);
      }
    } catch (error) {
    }
  };

  const pollInterval = setInterval(poll, 5000);
  poll();
}
