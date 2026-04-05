document.addEventListener("DOMContentLoaded", () => {
  const tabButtons = document.querySelectorAll(".tab-btn[data-category]");
  const sections = document.querySelectorAll(".menu-section");
  const popup = document.getElementById("cartPopup");
  const popupCount = document.getElementById("popupCount");
  const popupTotal = document.getElementById("popupTotal");
  const cartBadge = document.getElementById("cartBadge");
  const panel = document.getElementById("ordersPanel");
  const overlay = document.getElementById("panelOverlay");
  const openButton = document.getElementById("openOrdersPanel");
  const closeButton = document.getElementById("closePanelBtn");
  const phoneInput = document.getElementById("orderPhoneInput");
  const lookupButton = document.getElementById("lookupOrdersBtn");
  const ordersContainer = document.getElementById("ordersContainer");
  const initialTotal = Number(document.getElementById("cartTotalHidden")?.value || 0);

  let cartCount = Number.parseInt(cartBadge?.textContent || "0", 10);
  let cartTotal = Number.isFinite(initialTotal) ? initialTotal : 0;

  const filterCategory = (category) => {
    sections.forEach((section) => {
      section.style.display =
        category === "All" || section.dataset.category === category ? "" : "none";
    });

    tabButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.category === category);
    });
  };

  const openPanel = () => {
    panel?.classList.add("open");
    overlay?.classList.add("active");
    document.body.style.overflow = "hidden";
  };

  const closePanel = () => {
    panel?.classList.remove("open");
    overlay?.classList.remove("active");
    document.body.style.overflow = "";
  };

  const renderOrders = (orders) => {
    ordersContainer.innerHTML = orders
      .map(
        (order) => `
          <div class="order-history-card">
            <div class="order-history-header">
              <span class="order-history-id">Order #${order.id}</span>
              ${statusBadge(order.status)}
            </div>
            <div class="order-history-details">
              <span>🪑 Table: ${order.table_number}</span>
              <span>💰 Total: KES ${order.total_amount}</span>
              <span>🕐 ${timeAgo(order.created_at)}</span>
            </div>
          </div>
        `,
      )
      .join("");
  };

  filterCategory("All");

  tabButtons.forEach((button) => {
    button.addEventListener("click", () => {
      filterCategory(button.dataset.category);
    });
  });

  document.querySelectorAll(".add-to-cart-btn").forEach((button) => {
    button.addEventListener("click", async () => {
      const foodId = button.dataset.foodId;
      const price = Number.parseFloat(button.dataset.price);

      button.disabled = true;
      button.textContent = "✓";

      try {
        const formData = new FormData();
        formData.append("food_id", foodId);

        const response = await fetch("/add-to-cart", {
          method: "POST",
          body: formData,
        });
        const data = await response.json();

        if (data.success) {
          cartCount = data.cart_count;
          cartTotal += price;

          if (cartBadge) {
            cartBadge.textContent = cartCount;
            cartBadge.style.display = cartCount > 0 ? "flex" : "none";
          }

          if (popupCount) {
            popupCount.textContent = `${cartCount} item${cartCount === 1 ? "" : "s"}`;
          }

          if (popupTotal) {
            popupTotal.textContent = `KES ${cartTotal.toFixed(0)}`;
          }

          popup?.classList.add("visible");
        }
      } catch (error) {
      } finally {
        setTimeout(() => {
          button.disabled = false;
          button.textContent = "+ Add";
        }, 1200);
      }
    });
  });

  openButton?.addEventListener("click", openPanel);
  closeButton?.addEventListener("click", closePanel);
  overlay?.addEventListener("click", closePanel);

  lookupButton?.addEventListener("click", async () => {
    const phone = phoneInput?.value.trim();

    if (!phone) {
      ordersContainer.innerHTML =
        '<p style="color:var(--text-muted);text-align:center">Please enter your phone number.</p>';
      return;
    }

    ordersContainer.innerHTML =
      '<p style="text-align:center;color:var(--text-muted)">Looking up orders...</p>';

    try {
      const response = await fetch(`/api/my-orders?phone=${encodeURIComponent(phone)}`);
      const orders = await response.json();

      if (!orders.length) {
        ordersContainer.innerHTML =
          '<div class="empty-state"><p>No orders found for this number.</p></div>';
        return;
      }

      renderOrders(orders);
    } catch (error) {
      ordersContainer.innerHTML =
        '<p style="color:red;text-align:center">Error loading orders.</p>';
    }
  });

  phoneInput?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      lookupButton?.click();
    }
  });
});
