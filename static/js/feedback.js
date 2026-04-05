document.addEventListener("DOMContentLoaded", () => {
  const stars = document.querySelectorAll(".star");
  const ratingInput = document.getElementById("ratingInput");
  const commentArea = document.getElementById("commentArea");
  const charCount = document.getElementById("charCount");
  const feedbackForm = document.getElementById("feedbackForm");

  let selectedRating = 0;

  const paintStars = (rating) => {
    stars.forEach((star, index) => {
      star.classList.toggle("active", index < rating);
    });
  };

  const setRating = (rating) => {
    selectedRating = rating;
    if (ratingInput) {
      ratingInput.value = rating;
    }
    paintStars(rating);
  };

  stars.forEach((star, index) => {
    const rating = index + 1;

    star.addEventListener("mouseenter", () => {
      paintStars(rating);
    });

    star.addEventListener("mouseleave", () => {
      paintStars(selectedRating);
    });

    star.addEventListener("click", () => {
      setRating(rating);
    });

    star.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        setRating(rating);
      }
    });
  });

  commentArea?.addEventListener("input", () => {
    if (commentArea.value.length > 500) {
      commentArea.value = commentArea.value.slice(0, 500);
    }

    if (charCount) {
      charCount.textContent = `${commentArea.value.length}`;
    }
  });

  feedbackForm?.addEventListener("submit", (event) => {
    if (!selectedRating) {
      event.preventDefault();
      alert("Please select a star rating.");
    }
  });
});
