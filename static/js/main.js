document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach((flash) => {
    setTimeout(() => {
      flash.style.transition = "opacity 0.5s";
      flash.style.opacity = "0";
      setTimeout(() => flash.remove(), 500);
    }, 4000);
  });
});

function timeAgo(dateString) {
  const now = new Date();
  const then = new Date(dateString);
  const diffInSeconds = Math.floor((now - then) / 1000);

  if (diffInSeconds < 60) {
    return `${diffInSeconds} sec ago`;
  }

  if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return `${minutes} min ago`;
  }

  if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return `${hours} hr ago`;
  }

  const days = Math.floor(diffInSeconds / 86400);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function statusBadge(status) {
  const badges = {
    Pending: "badge-pending",
    Preparing: "badge-preparing",
    Ready: "badge-ready",
    Served: "badge-served",
    Cancelled: "badge-cancelled",
    Paid: "badge-paid",
    Unpaid: "badge-unpaid",
  };

  return `<span class="badge ${badges[status] || ""}">${status}</span>`;
}
