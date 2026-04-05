document.addEventListener("DOMContentLoaded", () => {
  const sidebar = document.querySelector(".sidebar");
  const sidebarToggle = document.querySelector(".sidebar-toggle");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  const addModal = document.getElementById("addFoodModal");
  const editModal = document.getElementById("editFoodModal");
  const editForm = document.getElementById("editFoodForm");

  const showModal = (modal) => modal?.classList.add("open");
  const hideModal = (modal) => modal?.classList.remove("open");

  sidebarToggle?.addEventListener("click", () => {
    sidebar?.classList.toggle("open");
    sidebarOverlay?.classList.toggle("active");
  });

  sidebarOverlay?.addEventListener("click", () => {
    sidebar?.classList.remove("open");
    sidebarOverlay?.classList.remove("active");
  });

  document.getElementById("openAddModal")?.addEventListener("click", () => {
    showModal(addModal);
  });

  document.getElementById("closeAddModal")?.addEventListener("click", () => {
    hideModal(addModal);
  });

  document.getElementById("cancelAddModal")?.addEventListener("click", () => {
    hideModal(addModal);
  });

  addModal?.addEventListener("click", (event) => {
    if (event.target === addModal) {
      hideModal(addModal);
    }
  });

  document.querySelectorAll(".edit-food-btn").forEach((button) => {
    button.addEventListener("click", () => {
      if (editForm) {
        editForm.action = `/admin-food/edit/${button.dataset.id}`;
      }

      document.getElementById("editName").value = button.dataset.name;
      document.getElementById("editCategory").value = button.dataset.category;
      document.getElementById("editPrice").value = button.dataset.price;
      document.getElementById("editAvailable").value = button.dataset.available;

      showModal(editModal);
    });
  });

  document.getElementById("closeEditModal")?.addEventListener("click", () => {
    hideModal(editModal);
  });

  document.getElementById("cancelEditModal")?.addEventListener("click", () => {
    hideModal(editModal);
  });

  editModal?.addEventListener("click", (event) => {
    if (event.target === editModal) {
      hideModal(editModal);
    }
  });

  document.querySelectorAll(".delete-food-btn").forEach((button) => {
    button.addEventListener("click", (event) => {
      const shouldDelete = confirm(
        `Delete "${button.dataset.name}"? This cannot be undone.`,
      );

      if (!shouldDelete) {
        event.preventDefault();
      }
    });
  });

  document.querySelectorAll(".avail-toggle").forEach((checkbox) => {
    checkbox.addEventListener("change", async () => {
      const itemId = checkbox.dataset.id;

      try {
        const response = await fetch(`/admin-food/toggle/${itemId}`, {
          method: "POST",
          body: new FormData(),
        });

        if (!response.ok) {
          throw new Error("Toggle failed");
        }

        const data = await response.json();
        const label = checkbox.closest("td")?.querySelector(".avail-label");

        if (label) {
          label.textContent = data.available ? "Active" : "Off";
          label.style.color = data.available ? "#15803D" : "#B91C1C";
        }
      } catch (error) {
        checkbox.checked = !checkbox.checked;
      }
    });
  });
});
