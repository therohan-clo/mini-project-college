// API base: empty string means same origin. On Vercel this calls /api/... correctly.
// For local dev if you run Flask separately on 127.0.0.1:5000, you can set:
// const API_BASE = "http://127.0.0.1:5000";
const API_BASE = "";

// Helpers: toast messages
const toast = (msg, type = "") => {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast ${type}`.trim();
  el.classList.remove("hidden");
  setTimeout(() => el.classList.add("hidden"), 1800);
};

const $list = document.getElementById("task-list");
const $loading = document.getElementById("loading");
const $form = document.getElementById("add-form");
const $title = document.getElementById("title-input");
const $reload = document.getElementById("reload-btn");

// State rendering
function renderTasks(tasks) {
  $list.innerHTML = "";
  for (const task of tasks) {
    const li = document.createElement("li");
    li.className = "task";

    const titleWrap = document.createElement("div");
    titleWrap.className = "title";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = !!task.done;
    checkbox.addEventListener("change", async () => {
      await toggleDone(task.id, checkbox.checked);
    });

    const titleText = document.createElement("span");
    titleText.textContent = task.title;
    titleText.className = task.done ? "done" : "";

    // Inline edit input (hidden by default)
    const editInput = document.createElement("input");
    editInput.type = "text";
    editInput.value = task.title;
    editInput.className = "hidden";

    titleWrap.appendChild(checkbox);
    titleWrap.appendChild(titleText);
    titleWrap.appendChild(editInput);

    const actions = document.createElement("div");
    actions.className = "actions";

    const editBtn = document.createElement("button");
    editBtn.textContent = "Edit";
    editBtn.className = "secondary";
    editBtn.addEventListener("click", async () => {
      // Toggle between view/edit modes
      const isEditing = !editInput.classList.contains("hidden");
      if (isEditing) {
        const newTitle = editInput.value.trim();
        if (newTitle && newTitle !== task.title) {
          await editTask(task.id, newTitle);
        }
        editInput.classList.add("hidden");
        titleText.classList.remove("hidden");
      } else {
        editInput.value = task.title;
        editInput.classList.remove("hidden");
        titleText.classList.add("hidden");
        editInput.focus();
      }
    });

    const delBtn = document.createElement("button");
    delBtn.textContent = "Delete";
    delBtn.className = "danger";
    delBtn.addEventListener("click", async () => {
      if (confirm("Delete this task?")) {
        await deleteTask(task.id);
      }
    });

    actions.appendChild(editBtn);
    actions.appendChild(delBtn);

    li.appendChild(titleWrap);
    li.appendChild(actions);

    $list.appendChild(li);
  }
}

// API helpers
async function loadTasks() {
  $loading.classList.remove("hidden");
  try {
    const res = await fetch(`${API_BASE}/api/tasks`);
    if (!res.ok) throw new Error(`Failed to load: ${res.status}`);
    const data = await res.json();
    renderTasks(data);
  } catch (err) {
    console.error(err);
    toast("Error loading tasks", "error");
  } finally {
    $loading.classList.add("hidden");
  }
}

async function addTask(title) {
  try {
    const res = await fetch(`${API_BASE}/api/tasks`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.error || `Failed: ${res.status}`);
    }
    toast("Task added");
    await loadTasks();
  } catch (err) {
    console.error(err);
    toast(err.message || "Error adding task", "error");
  }
}

async function toggleDone(id, done) {
  try {
    const res = await fetch(`${API_BASE}/api/tasks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ done }),
    });
    if (!res.ok) throw new Error(`Failed: ${res.status}`);
    await loadTasks();
  } catch (err) {
    console.error(err);
    toast("Error updating", "error");
  }
}

async function editTask(id, title) {
  try {
    const res = await fetch(`${API_BASE}/api/tasks/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    if (!res.ok) throw new Error(`Failed: ${res.status}`);
    toast("Task updated");
    await loadTasks();
  } catch (err) {
    console.error(err);
    toast("Error updating", "error");
  }
}

async function deleteTask(id) {
  try {
    const res = await fetch(`${API_BASE}/api/tasks/${id}`, { method: "DELETE" });
    if (!res.ok) throw new Error(`Failed: ${res.status}`);
    toast("Deleted");
    await loadTasks();
  } catch (err) {
    console.error(err);
    toast("Error deleting", "error");
  }
}

// Events
$form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const title = $title.value.trim();
  if (!title) return;
  $title.value = "";
  await addTask(title);
});

$reload.addEventListener("click", loadTasks);

// Initial load
loadTasks();
