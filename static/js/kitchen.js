document.addEventListener("DOMContentLoaded", () => {
  let currentFilter = "All";
  let lastOrders = [];

  const renderOrders = (orders) => {
    lastOrders = Array.isArray(orders) ? orders : [];

    const container = document.getElementById("ordersContainer");
    if (!container) {
      return;
    }

    const filteredOrders =
      currentFilter === "All"
        ? lastOrders
        : lastOrders.filter((order) => order.status === currentFilter);

    const countPending = lastOrders.filter((order) => order.status === "Pending").length;
    const countPreparing = lastOrders.filter((order) => order.status === "Preparing").length;
    const countReady = lastOrders.filter((order) => order.status === "Ready").length;

    const statPending = document.getElementById("statPending");
    const statPreparing = document.getElementById("statPreparing");
    const statReady = document.getElementById("statReady");

    if (statPending) {
      statPending.textContent = countPending;
    }
    if (statPreparing) {
      statPreparing.textContent = countPreparing;
    }
    if (statReady) {
      statReady.textContent = countReady;
    }

    if (!filteredOrders.length) {
      container.innerHTML = '<div class="empty-state"><p>No orders in this category.</p></div>';
      return;
    }

    container.innerHTML = filteredOrders
      .map((order) => {
        const itemsHtml = order.items
          .map(
            (item) =>
              `<div class="order-item-entry"><span><strong>${item.qty}x</strong> ${item.name}</span></div>`,
          )
          .join("");

        const statuses = ["Pending", "Preparing", "Ready", "Served"];
        const statusButtons = statuses
          .map((status) => {
            const buttonClass =
              order.status === status ? `current-${status.toLowerCase()}` : "";
            return `<button class="status-btn ${buttonClass}" data-order-id="${order.id}" data-status="${status}">${status}</button>`;
          })
          .join("");

        return `
          <div class="order-card" data-status="${order.status}">
            <div class="order-card-header">
              <span class="order-card-id">Order #${order.id}</span>
              <span class="order-card-time">${timeAgo(order.created_at)}</span>
            </div>
            <div class="order-card-info">
              <span class="order-info-item">👤 ${order.customer_name}</span>
              <span class="order-info-item">🪑 Table ${order.table_number}</span>
              <span class="order-info-item">📞 ${order.phone_number}</span>
            </div>
            <div class="order-items-list">${itemsHtml}</div>
            <div class="order-card-total">
              <span>Total</span>
              <span>KES ${order.total_amount}</span>
            </div>
            <div class="status-buttons">${statusButtons}</div>
          </div>
        `;
      })
      .join("");
  };

  const fetchOrders = async () => {
    try {
      const response = await fetch("/api/orders");
      if (!response.ok) {
        throw new Error("Could not load orders");
      }

      const orders = await response.json();
      renderOrders(orders);
    } catch (error) {
      renderOrders([]);
    }
  };

  document.querySelectorAll(".filter-tab").forEach((button) => {
    button.addEventListener("click", () => {
      currentFilter = button.dataset.filter;

      document.querySelectorAll(".filter-tab").forEach((tab) => {
        tab.classList.remove("active");
      });

      button.classList.add("active");
      renderOrders(lastOrders);
    });
  });

  document.addEventListener("click", async (event) => {
    const button = event.target.closest(".status-btn");
    if (!button) {
      return;
    }

    button.disabled = true;

    try {
      const formData = new FormData();
      formData.append("order_id", button.dataset.orderId);
      formData.append("status", button.dataset.status);

      const response = await fetch("/update-order-status", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Status update failed");
      }

      await fetchOrders();
    } catch (error) {
      button.disabled = false;
      return;
    }

    button.disabled = false;
  });

  fetchOrders();
  setInterval(fetchOrders, 2000);
});
