document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  
  // Modal elements
  const confirmationModal = document.getElementById("confirmation-modal");
  const participantNameElement = document.getElementById("participant-name");
  const activityNameElement = document.getElementById("activity-name");
  const btnConfirm = document.getElementById("btn-confirm");
  const btnCancel = document.getElementById("btn-cancel");
  const modalClose = document.getElementById("modal-close");
  
  // Store the current deletion context
  let pendingDeletion = null;

  // Function to open the confirmation modal
  function openConfirmationModal(participant, activity) {
    pendingDeletion = { participant, activity };
    participantNameElement.textContent = participant;
    activityNameElement.textContent = activity;
    confirmationModal.classList.remove("hidden");
  }

  // Function to close the confirmation modal
  function closeConfirmationModal() {
    confirmationModal.classList.add("hidden");
    pendingDeletion = null;
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message and the select dropdown
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        const participantsList = details.participants.map(participant => 
          `<li>${participant} <span class='delete-icon' data-participant='${participant}'>&#10006;</span></li>`
        ).join('');

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-section">
            <h5>Participants (${details.participants.length}/${details.max_participants})</h5>
            <ul class="participants-list">
              ${participantsList}
            </ul>
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Attach delete event listeners after DOM is updated
      const deleteIcons = document.querySelectorAll('.delete-icon');
      deleteIcons.forEach(icon => {
        icon.addEventListener('click', (event) => {
          const participant = event.target.dataset.participant;
          const activityName = event.target.closest('.activity-card').querySelector('h4').textContent;
          openConfirmationModal(participant, activityName);
        });
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle confirmation button click
  btnConfirm.addEventListener("click", async () => {
    if (!pendingDeletion) return;
    
    try {
      await fetch(`/activities/${encodeURIComponent(pendingDeletion.activity)}/unregister?email=${encodeURIComponent(pendingDeletion.participant)}`, {
        method: 'DELETE',
      });
      closeConfirmationModal();
      fetchActivities(); // Refresh the activities list
    } catch (error) {
      console.error("Error unregistering participant:", error);
      closeConfirmationModal();
    }
  });

  // Handle cancel button click
  btnCancel.addEventListener("click", closeConfirmationModal);

  // Handle modal close button click
  modalClose.addEventListener("click", closeConfirmationModal);

  // Close modal when clicking on the backdrop
  confirmationModal.addEventListener("click", (event) => {
    if (event.target === confirmationModal || event.target.classList.contains("modal-backdrop")) {
      closeConfirmationModal();
    }
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const email = document.getElementById("email").value;
    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup?email=${encodeURIComponent(email)}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
        fetchActivities(); // Refresh the activities list
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  fetchActivities();
});
