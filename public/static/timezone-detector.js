function TimezoneDetector(userTimezone, csrfMiddlewareToken, updateUrl) {
  this.browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
  this.userTimezone = userTimezone;
  this.csrfMiddlewareToken = csrfMiddlewareToken;
  this.updateUrl = updateUrl;
  this.modal = null;
  this.saving = false;
  this.storageKey = 'timezone_prompt_dismissed';

  this.init();
}

TimezoneDetector.prototype.init = function() {
  if (this.shouldShowPrompt()) {
    if (this.browserTimezone && this.userTimezone && this.browserTimezone !== this.userTimezone) {
      this.createModal();
      this.showModal();
    }
  }
};

TimezoneDetector.prototype.shouldShowPrompt = function() {
  const dismissed = localStorage.getItem(this.storageKey);
  if (!dismissed) return true;

  const dismissedTime = parseInt(dismissed, 10),
        oneWeek = 7 * 24 * 60 * 60 * 1000; // one week in milliseconds
  return Date.now() > dismissedTime + oneWeek;
};

TimezoneDetector.prototype.createModal = function() {
  const modalHtml = `
          <div class="modal fade" id="timezoneModal" tabindex="-1" aria-labelledby="timezoneModalLabel" aria-hidden="true">
              <div class="modal-dialog">
                  <div class="modal-content">
                      <div class="modal-header">
                          <h5 class="modal-title" id="timezoneModalLabel">Update Timezone?</h5>
                          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                      </div>
                      <div class="modal-body">
                          <p>Your browser's timezone (${this.browserTimezone}) is different from your account timezone (${this.userTimezone}). Would you like to update it?</p>
                          <div class="alert alert-danger d-none" id="timezoneError"></div>
                      </div>
                      <div class="modal-footer">
                          <button type="button" class="btn btn-secondary" id="dismissTimezoneBtn" data-bs-dismiss="modal">
                              No, keep current timezone
                          </button>
                          <button type="button" class="btn btn-primary" id="updateTimezoneBtn">
                              Yes, update timezone
                          </button>
                      </div>
                  </div>
              </div>
          </div>
      `;

  document.body.insertAdjacentHTML('beforeend', modalHtml);

  this.modal = new bootstrap.Modal(document.getElementById('timezoneModal')); // eslint-disable-line no-undef
  this.errorElement = document.getElementById('timezoneError');
  this.updateButton = document.getElementById('updateTimezoneBtn');
  this.dismissButton = document.getElementById('dismissTimezoneBtn');

  this.updateButton.addEventListener('click', this.updateTimezone.bind(this));
  const modalElement = document.getElementById('timezoneModal');
  modalElement.addEventListener('hidden.bs.modal', (event) => {
    if (event.target === modalElement) {
      this.dismissPrompt();
    }
  });
};

TimezoneDetector.prototype.dismissPrompt = function() {
  localStorage.setItem(this.storageKey, Date.now().toString());
  this.hideModal();
};

TimezoneDetector.prototype.showModal = function() {
  this.modal.show();
};

TimezoneDetector.prototype.hideModal = function() {
  if (this.modal) {
    this.modal.hide();
  }
};

TimezoneDetector.prototype.showError = function(message) {
  this.errorElement.textContent = message;
  this.errorElement.classList.remove('d-none');
};

TimezoneDetector.prototype.hideError = function() {
  this.errorElement.classList.add('d-none');
  this.errorElement.textContent = '';
};

TimezoneDetector.prototype.updateTimezone = async function() {
  if (this.saving) return;

  this.saving = true;
  this.hideError();
  this.updateButton.disabled = true;
  this.updateButton.textContent = 'Updating...';

  try {
    const formData = new FormData();
    formData.append('timezone', this.browserTimezone);

    const response = await fetch(this.updateUrl, {
      method: 'POST',
      body: formData,
      headers: {
        'X-CSRFToken': this.csrfMiddlewareToken,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to update timezone');
    }

    // Success - reload the page to reflect the new timezone
    window.location.reload();
  } catch (err) {
    this.showError('Failed to update timezone. Please try again.');
    this.updateButton.disabled = false;
    this.updateButton.textContent = 'Yes, update timezone';
  } finally {
    this.saving = false;
  }
};