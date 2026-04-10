<script>
  function triggerSystemBackup() {
    fetch("{% url 'backup_system' %}")
      .then(r => r.json())
      .then(data => Swal.fire({ icon: data.status === 'success' ? 'success' : 'error', title: data.message }))
      .catch(err => Swal.fire({ icon: 'error', title: err.toString() }));
}

  $(document).ready(function () {
    $('#searchInput').on('keyup', function () {
      const q = $(this).val().toLowerCase();
      $('#contributionTable tbody tr').each(function () {
        $(this).toggle($(this).text().toLowerCase().includes(q));
      });
    });

  // Registered Users.
  // Handle logout with SweetAlert
  $(document).on('click', '.logoutUserBtn', function () {
    const userId = $(this).data('id');
  Swal.fire({
    title: 'Are you sure?',
  text: 'Force logout this user?',
  icon: 'warning',
  showCancelButton: true,
  confirmButtonText: 'Yes, logout!',
  cancelButtonText: 'Cancel'
    }).then((result) => {
      if (result.isConfirmed) {
    $.post(`/logout_user/${userId}/`, {
      csrfmiddlewaretoken: '{{ csrf_token }}'
    }).done(function (res) {
      Swal.fire(res.status.charAt(0).toUpperCase() + res.status.slice(1), res.message, res.status);
    }).fail(() => {
      Swal.fire('Error', 'Something went wrong.', 'error');
    });
      }
    });
  });

  // Handle CSV download
  function downloadUsers() {
  const table = document.getElementById("usersTable");
  if (!table) {
    alert("Users table not found!");
  return;
  }

  let csv = [];
  const rows = table.querySelectorAll("thead tr, tbody tr");

  rows.forEach(row => {
    const cols = row.querySelectorAll("th, td");
  let rowData = [];
    cols.forEach(col => {
    // Escape double quotes for CSV compliance
    let text = col.innerText.trim().replace(/"/g, '""');
  rowData.push(`"${text}"`);
    });
  csv.push(rowData.join(","));
  });

  const csvContent = csv.join("\n");
  const blob = new Blob([csvContent], {type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);

  const link = document.createElement("a");
  link.href = url;
  const now = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
  link.download = `registered_users_${now}.csv`;
  document.body.appendChild(link);
  link.click();

  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
  // Show contributions in modal
  $(document).on('click', '.viewBtn', function () {
    const name = $(this).data('name');
  const url = `/member_contributions_api/${encodeURIComponent(name)}/`;

  $('#contributionName').text(name);
  $('#memberSearchInput').val('');
  $('#memberContributionTable tbody').empty();
  $('#downloadMemberData').removeData('records');

  $.get(url, function (res) {
      if (res.status === 'success' && res.data.length > 0) {
        const rows = res.data.map(c => `
  <tr data-id="${c.id}">
    <td>${c.case}</td>
    <td><input type="number" class="form-control form-control-sm contributionInput" value="${c.contribution}"></td>
    <td><input type="text" class="form-control form-control-sm dateInput" value="${c.date}"></td>
    <td><input type="text" class="form-control form-control-sm contactInput" value="${c.contact}"></td>
    <td>
      {% if user.is_superuser %}
      <button class="btn btn-sm btn-success updateBtn">Save</button>
      <button class="btn btn-sm btn-danger deleteBtn">Delete</button>
      {% endif %}
    </td>
  </tr>`).join('');
  $('#memberContributionTable tbody').html(rows);
  $('#downloadMemberData').data('records', res.data);
  new bootstrap.Modal(document.getElementById('contributionsModal')).show();
      } else {
    Swal.fire('No Data', 'No contributions found.', 'info');
      }
    }).fail(() => Swal.fire('Error', 'Failed to load contributions.', 'error'));
  });

  // Save update
  $(document).on('click', '.updateBtn', function () {
    const row = $(this).closest('tr');
  const id = row.data('id');
  const data = {
    contribution: row.find('.contributionInput').val(),
  date: row.find('.dateInput').val(),
  contact: row.find('.contactInput').val(),
  csrfmiddlewaretoken: '{{ csrf_token }}'
    };
  $.post(`/update_contribution/${id}/`, data).done(r => {
    Swal.fire(r.status === 'success' ? 'Updated' : 'Error', r.message, r.status);
    });
  });

  // Delete
  $(document).on('click', '.deleteBtn', function () {
    const row = $(this).closest('tr');
  const id = row.data('id');
  Swal.fire({
    title: 'Are you sure?',
  text: 'This contribution will be deleted!',
  icon: 'warning',
  showCancelButton: true
    }).then((res) => {
      if (res.isConfirmed) {
    $.post(`/delete_contribution/${id}/`, { csrfmiddlewaretoken: '{{ csrf_token }}' })
      .done(r => {
        if (r.status === 'success') {
          row.remove();
          Swal.fire('Deleted', r.message, 'success');
        } else {
          Swal.fire('Error', r.message, 'error');
        }
      });
      }
    });
  });

  // Filter modal contributions
  $('#memberSearchInput').on('keyup', function () {
    const query = $(this).val().toLowerCase();
  $('#memberContributionTable tbody tr').each(function () {
    $(this).toggle($(this).text().toLowerCase().includes(query));
    });
  });

  // Excel Download
  $('#downloadMemberData').on('click', function () {
    const data = $(this).data('records');
  if (!data || data.length === 0) {
      return Swal.fire('No Data', 'No records to export.', 'info');
    }

    const exportData = data.map(d => ({
    'Case': d.case,
  'Contribution': d.contribution,
  'Date': d.date,
  'Contact': d.contact
    }));

  const ws = XLSX.utils.json_to_sheet(exportData);
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, ws, 'Contributions');

  const filename = `Contributions_${$('#contributionName').text().replace(/\s+/g, '_')}.xlsx`;
  XLSX.writeFile(wb, filename);
  });
});

  // Disable right-click with SweetAlert2
  document.addEventListener('contextmenu', function (e) {
    e.preventDefault();
  Swal.fire({
    icon: 'info',
  title: 'Disabled',
  text: 'Right-click has been disabled on this system.',
  timer: 2000,
  showConfirmButton: false
    });
  });

  // Disable DevTools keyboard shortcuts
  document.addEventListener('keydown', function (e) {
    if (
  e.key === 'F12' ||                                       // F12
  (e.ctrlKey && e.shiftKey && ['I', 'J', 'C'].includes(e.key)) ||  // Ctrl+Shift+I/J/C
  (e.ctrlKey && e.key.toLowerCase() === 'u')              // Ctrl+U
  ) {
    e.preventDefault();
  Swal.fire({
    icon: 'warning',
  title: 'Access Denied',
  text: 'This action is disabled on this system.',
  timer: 2000,
  showConfirmButton: false
      });
    }
  });
  (function () {
    let check = function () {
    let before = new Date().getTime();
  debugger;
  let after = new Date().getTime();
      if (after - before > 100) {
    document.body.innerHTML = "<h1 style='text-align:center; color:red;'>🚫 Access Not Allowed! Contact Your Administrator for help on 0700667769</h1>";
      }
    };
  setInterval(check, 1000);
  })();

  document.addEventListener('keydown', function (e) {
    // Block Alt + Arrow navigation
    if (e.altKey && (e.key === 'ArrowLeft' || e.key === 'ArrowRight')) {
    e.preventDefault();
  Swal.fire({
    icon: 'warning',
  title: 'Navigation Blocked',
  text: 'Alt + Arrow keys are disabled.',
  timer: 1500,
  showConfirmButton: false
      });
    }

  // Block Backspace outside of input/textarea
  if (e.key === 'Backspace' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
    e.preventDefault();
  Swal.fire({
    icon: 'info',
  title: 'Disabled',
  text: 'Back navigation using Backspace is blocked.',
  timer: 1500,
  showConfirmButton: false
      });
    }
  });

  // Block browser history back/forward buttons
  if (window.history && window.history.pushState) {
    window.history.pushState(null, null, window.location.href);
  window.onpopstate = function () {
    window.history.pushState(null, null, window.location.href);
  Swal.fire({
    icon: 'info',
  title: 'Navigation Blocked',
  text: 'Browser history navigation is disabled.',
  timer: 1500,
  showConfirmButton: false
      });
    };
  }

  function loadAccountability(caseId) {
    fetch(`/cases/${caseId}/accountability/data/`)
      .then(response => response.json())
      .then(data => {
        // Update modal title
        document.querySelector("#accountabilityModal .modal-title").innerText =
          "📊 Accountability Report - " + data.case;

        // Update totals
        document.getElementById("totalContributions").innerText = data.total_contributions;
        document.getElementById("totalExpenses").innerText = data.total_expenses;
        document.getElementById("balance").innerText = data.balance;

        // Fill contributions table
        let contribTable = document.getElementById("contribBody");
        contribTable.innerHTML = "";
        if (data.contributions.length > 0) {
          data.contributions.forEach(c => {
            contribTable.innerHTML += `
            <tr>
              <td>${c.rank__rank_name}</td>
              <td>${c.names}</td>
              <td>${c.contribution}</td>
              <td>${c.contact}</td>
              <td>${c.date_of_contribution}</td>
            </tr>`;
          });
        } else {
          contribTable.innerHTML = `<tr><td colspan="5" class="text-center">No contributions yet</td></tr>`;
        }

        // Fill expenses table
        let expenseTable = document.getElementById("expenseBody");
        expenseTable.innerHTML = "";
        if (data.expenses.length > 0) {
          data.expenses.forEach(e => {
            expenseTable.innerHTML += `
            <tr>
              <td>${e.description}</td>
              <td>${e.amount}</td>
              <td>${e.date}</td>
              <td>${e.added_by__username ?? ""}</td>
            </tr>`;
          });
        } else {
          expenseTable.innerHTML = `<tr><td colspan="4" class="text-center">No expenses yet</td></tr>`;
        }

        // Update download button link
        document.getElementById("downloadReportBtn").href =
          `/cases/${caseId}/accountability/export/`;
      });
}


  // Attempt to blur the address bar (will not prevent copying the URL entirely)
  window.addEventListener('blur', () => {
    window.focus();
  });
</script>
