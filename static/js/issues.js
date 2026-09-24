requireAuth();

function badge(value) { return `<span class="badge badge-${value}">${value}</span>`; }

async function loadIssues() {
  const status = document.getElementById("filter-status").value;
  const priority = document.getElementById("filter-priority").value;
  const search = document.getElementById("filter-search").value;

  const params = new URLSearchParams();
  if (status) params.set("status", status);
  if (priority) params.set("priority", priority);
  if (search) params.set("search", search);

  const res = await API.get(`/issues?${params.toString()}`);
  const items = res.data.items;
  const tbody = document.getElementById("issues-tbody");
  const emptyState = document.getElementById("empty-state");

  if (!items.length) {
    tbody.innerHTML = "";
    emptyState.style.display = "block";
    return;
  }
  emptyState.style.display = "none";

  tbody.innerHTML = items.map(i => `
    <tr>
      <td><a href="/issues/${i.id}">#${i.id}</a></td>
      <td>${i.title}</td>
      <td>${i.category || "—"}</td>
      <td>${badge(i.priority)}</td>
      <td>${badge(i.status)}</td>
      <td>${i.vehicle || "—"}</td>
      <td>${i.hub || "—"}</td>
      <td>${new Date(i.created_at).toLocaleString()}</td>
    </tr>
  `).join("");
}

document.getElementById("apply-filters").addEventListener("click", loadIssues);
loadIssues();
