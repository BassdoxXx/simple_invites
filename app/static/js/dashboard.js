/**
 * Dashboard functionality for Simple Invites
 */

document.addEventListener('DOMContentLoaded', function() {
  initDashboard();
});

/**
 * Initialize the dashboard functionality
 */
function initDashboard() {
  const selectAllCheckbox = document.getElementById('selectAll');
  const inviteCheckboxes = document.querySelectorAll('.invite-checkbox');
  const pdfExportBtn = document.getElementById('pdfExportBtn');
  const csvExportBtn = document.getElementById('csvExportBtn');
  
  // Select all checkboxes
  if (selectAllCheckbox) {
    selectAllCheckbox.addEventListener('change', function() {
      const isChecked = this.checked;
      
      inviteCheckboxes.forEach(checkbox => {
        if (checkbox.closest('tr').style.display !== 'none') {
          checkbox.checked = isChecked;
        }
      });
      
      updateButtons();
    });
  }
  
  // When any invite checkbox is clicked
  inviteCheckboxes.forEach(checkbox => {
    checkbox.addEventListener('change', function() {
      updateButtons();
      
      // Update "select all" checkbox
      if (selectAllCheckbox) {
        const allVisible = Array.from(inviteCheckboxes)
          .filter(cb => cb.closest('tr').style.display !== 'none')
          .every(cb => cb.checked);
          
        selectAllCheckbox.checked = allVisible;
      }
    });
  });
  
  // Update button states based on checkbox selection
  function updateButtons() {
    const hasSelectedInvites = Array.from(inviteCheckboxes).some(cb => cb.checked);
    if (pdfExportBtn) pdfExportBtn.disabled = !hasSelectedInvites;
    if (csvExportBtn) csvExportBtn.disabled = !hasSelectedInvites;
  }
  
  // Initialize button states
  updateButtons();
  
  // Export button event listeners
  if (pdfExportBtn) {
    pdfExportBtn.addEventListener('click', function() {
      submitExportForm('pdf');
    });
  }
  
  if (csvExportBtn) {
    csvExportBtn.addEventListener('click', function() {
      submitExportForm('csv');
    });
  }
}

/**
 * Handle form submission for exports
 * @param {string} type - Export type ('pdf' or 'csv')
 */
function submitExportForm(type) {
  const selectedCheckboxes = document.querySelectorAll('.invite-checkbox:checked');
  
  if (selectedCheckboxes.length === 0) {
    alert('Bitte wählen Sie mindestens eine Einladung aus.');
    return;
  }
  
  // Create a form for submission
  const form = document.createElement('form');
  form.method = 'POST';
  
  // Set the action based on export type
  if (type === 'pdf') {
    form.action = PDF_EXPORT_URL; // Set from the template
  } else if (type === 'csv') {
    form.action = CSV_EXPORT_URL; // Set from the template
    // For CSV, use different selection type based on count
    const selectionType = document.createElement('input');
    selectionType.type = 'hidden';
    selectionType.name = 'selection_type';
    selectionType.value = selectedCheckboxes.length === 1 ? 'single' : 'selected';
    form.appendChild(selectionType);
  }
  
  // Add CSRF token
  const csrfToken = document.createElement('input');
  csrfToken.type = 'hidden';
  csrfToken.name = 'csrf_token';
  csrfToken.value = CSRF_TOKEN; // Set from the template
  form.appendChild(csrfToken);
  
  // For PDF, always use 'selected'
  if (type === 'pdf') {
    const selectionType = document.createElement('input');
    selectionType.type = 'hidden';
    selectionType.name = 'selection_type';
    selectionType.value = 'selected';
    form.appendChild(selectionType);
  }
  
  // Add selected tokens
  selectedCheckboxes.forEach(checkbox => {
    const input = document.createElement('input');
    input.type = 'hidden';
    input.name = 'selected_invites';
    input.value = checkbox.value;
    form.appendChild(input);
  });
  
  // Submit the form
  document.body.appendChild(form);
  form.submit();
  
  // Remove the form after submission to prevent DOM cluttering
  setTimeout(() => {
    if (form && form.parentNode) {
      form.parentNode.removeChild(form);
    }
  }, 1000);
}

/**
 * Legacy function for backwards compatibility
 */
function generateSelectedPdfs() {
  const pdfExportBtn = document.getElementById('pdfExportBtn');
  if (pdfExportBtn) {
    pdfExportBtn.click();
  }
}
