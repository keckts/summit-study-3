// this file mostly generates the ai creator page

function setupAiWidget({
  triggerBtnId,
  modalId,
  formId,
  aiPromptCallback,    // function that builds AI prompt from form data
  apiUrl,
  onSuccessRedirect
}) {
  const triggerBtn = document.getElementById(triggerBtnId);
  const modal = document.getElementById(modalId);
  const form = document.getElementById(formId);
  const closeBtn = modal.querySelector(".close");

  triggerBtn.addEventListener("click", () => modal.classList.add("show"));
  closeBtn.addEventListener("click", () => modal.classList.remove("show"));
  modal.addEventListener("click", e => { if (e.target === modal) modal.classList.remove("show"); });

  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const formData = new FormData(form);

    // Add AI-specific prompt from callback
    const aiPrompt = aiPromptCallback(form);
    formData.append("prompt", aiPrompt.prompt);
    if (aiPrompt.numItems) formData.append(aiPrompt.numItemsKey || "num_items", aiPrompt.numItems);

    // Disable button and show loading
    const submitBtn = form.querySelector("button[type='submit']");
    submitBtn.disabled = true;
    submitBtn.innerText = "Generating...";

    try {
      const response = await fetch(apiUrl, {
        method: "POST",
        headers: { "X-CSRFToken": getCSRF() },
        body: formData
      });

      const data = await response.json();
      if (data.success) {
        alert("AI Flashcards created!");
        form.reset();
        modal.classList.remove("show");
        if (data.redirect_url) window.location.href = data.redirect_url;
      } else {
        alert("Error creating AI flashcards.");
      }
    } catch (err) {
      console.error(err);
      alert("Unexpected error occurred.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerText = "Generate";
    }
  });

  function getCSRF() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : "";
  }
}
