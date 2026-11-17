const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
const reservations = [];
let token = null;
let currentUser = null;
let visibleMonth = startOfMonth(new Date());
let selectedDate = dateKey(new Date());
let authMode = "login";

const calendarDays = document.querySelector("#calendar-days");
const agenda = document.querySelector("#agenda");
const pendingList = document.querySelector("#pending-list");
const pendingCount = document.querySelector("#pending-count");
const pendingMessage = document.querySelector("#pending-message");
const message = document.querySelector("#message");
const apiState = document.querySelector("#api-state");
const bookingDialog = document.querySelector("#booking-dialog");
const reservationForm = document.querySelector("#reservation-form");
const guestForm = document.querySelector("#guest-reservation-form");

function startOfMonth(date) {
  return new Date(date.getFullYear(), date.getMonth(), 1);
}

function dateKey(date) {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, "0"),
    String(date.getDate()).padStart(2, "0"),
  ].join("-");
}

function parseDate(value) {
  const [year, month, day] = value.split("-").map(Number);
  return new Date(year, month - 1, day);
}

function addDays(value, days) {
  const date = parseDate(value);
  date.setDate(date.getDate() + days);
  return dateKey(date);
}

function isActive(reservation) {
  return reservation.estado !== "cancelada";
}

function overlapsDay(reservation, day) {
  return reservation.fecha_entrada <= day &&
    day < reservation.fecha_salida &&
    isActive(reservation);
}

function formatLongDate(value) {
  return new Intl.DateTimeFormat("es-CO", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(parseDate(value));
}

function formatShortDate(value) {
  return new Intl.DateTimeFormat("es-CO", {
    day: "numeric",
    month: "short",
  }).format(parseDate(value));
}

function make(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== undefined) element.textContent = text;
  return element;
}

function setApiState(state, label) {
  apiState.dataset.state = state;
  document.querySelector("#api-state-label").textContent = label;
}

function setMessage(element, text, kind = "") {
  element.textContent = text || "";
  element.dataset.kind = kind;
}

async function apiRequest(path, options = {}) {
  const response = await fetch(API_BASE_URL + path, options);
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || "La API respondió HTTP " + response.status + ".");
  }
  return data;
}

function setAuthMode(mode) {
  authMode = mode;
  const isLogin = mode === "login";
  document.querySelector("#login-form").hidden = !isLogin;
  document.querySelector("#register-form").hidden = isLogin;
  document.querySelector("#login-tab").classList.toggle("active", isLogin);
  document.querySelector("#register-tab").classList.toggle("active", !isLogin);
  document.querySelector("#login-tab").setAttribute("aria-selected", String(isLogin));
  document.querySelector("#register-tab").setAttribute("aria-selected", String(!isLogin));
  document.querySelector("#auth-title").textContent = isLogin ? "Bienvenido" : "Crea tu cuenta";
  document.querySelector("#auth-description").textContent = isLogin
    ? "Vuelve a tu cuenta para consultar los detalles de tu estancia."
    : "Crea tu cuenta y solicita tu próxima estancia en pocos pasos.";
  setMessage(document.querySelector("#auth-message"), "");
}

function showAuthenticatedView(profile) {
  currentUser = profile;
  document.querySelector("#auth-view").hidden = true;
  document.querySelector("#admin-view").hidden = profile.role !== "admin";
  document.querySelector("#user-view").hidden = profile.role !== "user";
  document.querySelector("#session-profile").hidden = false;
  document.querySelector("#auth-button").hidden = false;
  document.querySelector("#profile-name").textContent = profile.name;
  const badge = document.querySelector("#role-badge");
  badge.textContent = profile.role === "admin" ? "Administración" : "Huésped";
  badge.dataset.role = profile.role;

  if (profile.role === "user") {
    document.querySelector("#guest-greeting").textContent = "Hola, " + profile.name;
  }
}

function clearSession() {
  token = null;
  currentUser = null;
  reservations.splice(0, reservations.length);
  document.querySelector("#auth-view").hidden = false;
  document.querySelector("#admin-view").hidden = true;
  document.querySelector("#user-view").hidden = true;
  document.querySelector("#session-profile").hidden = true;
  document.querySelector("#auth-button").hidden = true;
  document.querySelector("#guest-reservations").replaceChildren();
  pendingList.replaceChildren();
  pendingCount.textContent = "0";
  setMessage(pendingMessage, "", "");
  document.querySelector("#guest-stays-count").textContent = "0";
  setAuthMode("login");
  setApiState("loading", "Inicia sesión");
}

function renderCalendar() {
  const month = new Intl.DateTimeFormat("es-CO", {
    month: "long",
    year: "numeric",
  }).format(visibleMonth);
  document.querySelector("#month-label").textContent =
    month.charAt(0).toLocaleUpperCase("es-CO") + month.slice(1);
  calendarDays.replaceChildren();

  const first = startOfMonth(visibleMonth);
  const offset = (first.getDay() + 6) % 7;
  const gridStart = new Date(first);
  gridStart.setDate(first.getDate() - offset);
  const today = dateKey(new Date());

  for (let index = 0; index < 42; index += 1) {
    const date = new Date(gridStart);
    date.setDate(gridStart.getDate() + index);
    const key = dateKey(date);
    const dayReservations = reservations.filter((item) => overlapsDay(item, key));
    const statuses = new Set(dayReservations.map((item) => item.estado));
    const classes = ["day"];

    if (date.getMonth() !== visibleMonth.getMonth()) classes.push("outside");
    if (key === selectedDate) classes.push("selected");
    if (key === today) classes.push("today");

    const button = make("button", classes.join(" "));
    button.type = "button";
    button.setAttribute("role", "gridcell");
    button.setAttribute("aria-pressed", String(key === selectedDate));
    button.setAttribute(
      "aria-label",
      formatLongDate(key) + ", " + dayReservations.length + " reserva(s) activa(s)",
    );

    const number = make("span", "day-number", String(date.getDate()));
    const markers = make("span", "day-markers");
    for (const status of statuses) {
      markers.append(make("span", "marker" + (status === "pendiente" ? " pending" : "")));
    }
    const count = dayReservations.length
      ? dayReservations.length + " " + (dayReservations.length === 1 ? "estancia" : "estancias")
      : "";
    button.append(number, markers, make("span", "day-count", count));
    button.addEventListener("click", () => {
      selectedDate = key;
      renderCalendar();
      renderAgenda();
    });
    calendarDays.append(button);
  }

  renderSummary();
}

function renderSummary() {
  if (!currentUser || currentUser.role !== "admin") return;

  const first = dateKey(startOfMonth(visibleMonth));
  const next = dateKey(new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1));
  const monthReservations = reservations.filter((item) =>
    isActive(item) && item.fecha_entrada < next && item.fecha_salida > first
  );
  const today = dateKey(new Date());
  const occupiedRooms = new Set(
    reservations
      .filter((item) => overlapsDay(item, today))
      .map((item) => item.habitacion.trim().toLocaleLowerCase("es")),
  );
  const arrivals = reservations.filter((item) =>
    isActive(item) && item.fecha_entrada >= first && item.fecha_entrada < next
  ).length;

  document.querySelector("#month-count").textContent = String(monthReservations.length);
  document.querySelector("#today-count").textContent = String(occupiedRooms.size);
  document.querySelector("#arrival-count").textContent = String(arrivals);
}

function eventForSelectedDay(reservation) {
  if (reservation.estado === "cancelada") return "Reserva cancelada";
  if (reservation.fecha_entrada === selectedDate) return "Entrada";
  if (reservation.fecha_salida === selectedDate) return "Salida";
  return "En estancia";
}

function renderAgenda() {
  const dateLabel = formatLongDate(selectedDate);
  document.querySelector("#selected-label").textContent =
    dateLabel.charAt(0).toLocaleUpperCase("es-CO") + dateLabel.slice(1);
  agenda.replaceChildren();

  const dayReservations = reservations
    .filter((item) => item.fecha_entrada <= selectedDate && item.fecha_salida >= selectedDate)
    .sort((a, b) => a.fecha_entrada.localeCompare(b.fecha_entrada));

  if (!dayReservations.length) {
    agenda.append(make("p", "empty", "No hay reservas para este día."));
    return;
  }

  for (const reservation of dayReservations) {
    const entry = make("article", "booking fade-in");
    const top = make("div", "booking-top");
    const guest = make("div");
    guest.append(make("p", "booking-guest", reservation.huesped || "Huésped"));
    guest.append(make(
      "p",
      "booking-room",
      "Habitación " + reservation.habitacion + " · " +
        reservation.numero_huespedes + " huésped(es)",
    ));

    const statusClass = reservation.estado === "cancelada"
      ? "cancelled"
      : reservation.estado === "pendiente" ? "pending" : "";
    const statusText = reservation.estado === "cancelada"
      ? "Cancelada"
      : reservation.estado === "pendiente" ? "Pendiente" : "Confirmada";

    top.append(guest, make("span", "status " + statusClass, statusText));
    entry.append(top);
    entry.append(make(
      "p",
      "booking-dates",
      eventForSelectedDay(reservation) + " · " +
        formatShortDate(reservation.fecha_entrada) + " — " +
        formatShortDate(reservation.fecha_salida),
    ));
    agenda.append(entry);
  }
}

function renderPendingRequests() {
  const pending = reservations
    .filter((item) => item.estado === "pendiente")
    .sort((a, b) => a.fecha_entrada.localeCompare(b.fecha_entrada));
  pendingCount.textContent = String(pending.length);
  pendingCount.setAttribute("aria-label", pending.length + " solicitudes pendientes");
  pendingList.replaceChildren();

  if (!pending.length) {
    pendingList.append(make("p", "pending-empty", "No hay solicitudes pendientes por confirmar."));
    return;
  }

  for (const reservation of pending) {
    const row = make("article", "pending-row fade-in");
    const details = make("div", "pending-details");
    const identity = make("div", "pending-identity");
    identity.append(make("p", "pending-guest", reservation.huesped || "Huésped"));
    identity.append(make("p", "pending-email", reservation.correo || ""));
    const dates = make(
      "p",
      "pending-stay",
      formatShortDate(reservation.fecha_entrada) + " — " +
        formatShortDate(reservation.fecha_salida) + " · " +
        reservation.numero_huespedes + " huésped(es)",
    );
    const room = make("span", "pending-room", "Habitación " + reservation.habitacion);
    details.append(identity, room, dates);

    const confirm = make("button", "button small", "Confirmar");
    confirm.type = "button";
    confirm.setAttribute("aria-label", "Confirmar reserva de " + (reservation.huesped || "huésped"));
    confirm.addEventListener("click", () => confirmReservation(reservation, confirm));
    row.append(details, confirm);
    pendingList.append(row);
  }
}

async function confirmReservation(reservation, button) {
  if (!currentUser || currentUser.role !== "admin") return;
  button.disabled = true;
  button.textContent = "Confirmando…";
  setMessage(pendingMessage, "", "");

  const booking = {
    huesped: reservation.huesped,
    correo: reservation.correo,
    habitacion: reservation.habitacion,
    fecha_entrada: reservation.fecha_entrada,
    fecha_salida: reservation.fecha_salida,
    numero_huespedes: reservation.numero_huespedes,
    estado: "confirmada",
  };

  try {
    const result = await apiRequest("/reservas/" + reservation.id, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
        Accept: "application/json",
      },
      body: JSON.stringify(booking),
    });
    await loadReservations();
    setMessage(pendingMessage, "Reserva de " + reservation.huesped + " confirmada.", "success");
  } catch (error) {
    setMessage(pendingMessage, error.message, "error");
    if (button.isConnected) {
      button.disabled = false;
      button.textContent = "Confirmar";
    }
  }
}
function renderGuestReservations() {
  const list = document.querySelector("#guest-reservations");
  list.replaceChildren();
  document.querySelector("#guest-stays-count").textContent = String(reservations.length);

  if (!reservations.length) {
    list.append(make(
      "p",
      "guest-empty",
      "Todavía no tienes reservas. Envía una solicitud y aparecerá aquí.",
    ));
    return;
  }

  for (const reservation of reservations) {
    const item = make("article", "guest-reservation");
    const details = make("div", "guest-reservation-main");
    details.append(make("p", "guest-reservation-title", "Habitación " + reservation.habitacion));
    details.append(make(
      "p",
      "guest-reservation-dates",
      formatShortDate(reservation.fecha_entrada) + " — " +
        formatShortDate(reservation.fecha_salida) + " · " +
        reservation.numero_huespedes + " huésped(es)",
    ));

    const statusClass = reservation.estado === "cancelada"
      ? "cancelled"
      : reservation.estado === "pendiente" ? "pending" : "";
    const statusLabel = reservation.estado === "cancelada"
      ? "Cancelada"
      : reservation.estado === "pendiente" ? "Pendiente de confirmación" : "Confirmada";
    details.append(make("span", "guest-reservation-status " + statusClass, statusLabel));
    item.append(details);

    if (reservation.estado !== "cancelada") {
      const cancel = make("button", "guest-cancel", "Cancelar");
      cancel.type = "button";
      cancel.addEventListener("click", () => cancelGuestReservation(reservation.id, cancel));
      item.append(cancel);
    }
    list.append(item);
  }
}

async function cancelGuestReservation(reservationId, button) {
  button.disabled = true;
  try {
    const result = await apiRequest("/reservas/" + reservationId, {
      method: "DELETE",
      headers: { Authorization: "Bearer " + token, Accept: "application/json" },
    });
    setMessage(document.querySelector("#guest-message"), result.message, "success");
    await loadReservations();
  } catch (error) {
    setMessage(document.querySelector("#guest-message"), error.message, "error");
    button.disabled = false;
  }
}

function updateAdminDateRange() {
  const entry = reservationForm.elements.fecha_entrada;
  const exit = reservationForm.elements.fecha_salida;
  exit.min = entry.value ? addDays(entry.value, 1) : "";
  if (entry.value && exit.value && exit.value <= entry.value) {
    exit.value = addDays(entry.value, 1);
  }
}

function updateGuestDateRange() {
  const entry = guestForm.elements.fecha_entrada;
  const exit = guestForm.elements.fecha_salida;
  exit.min = entry.value ? addDays(entry.value, 1) : "";
  if (entry.value && exit.value && exit.value <= entry.value) {
    exit.value = addDays(entry.value, 1);
  }
}

async function refreshAvailableRooms(formElement, hintElement) {
  const select = formElement.elements.habitacion;
  const entry = formElement.elements.fecha_entrada.value;
  const exit = formElement.elements.fecha_salida.value;
  select.replaceChildren(new Option("Selecciona fechas primero", ""));
  select.disabled = true;

  if (!entry || !exit || exit <= entry || !token) {
    hintElement.textContent = "Selecciona fechas de entrada y salida para consultar disponibilidad.";
    return;
  }

  select.replaceChildren(new Option("Buscando habitaciones…", ""));
  hintElement.textContent = "Consultando disponibilidad para esas fechas…";
  try {
    const query = new URLSearchParams({ fecha_entrada: entry, fecha_salida: exit });
    const rooms = await apiRequest("/habitaciones/disponibles?" + query.toString(), {
      headers: { Accept: "application/json", Authorization: "Bearer " + token },
    });
    if (
      formElement.elements.fecha_entrada.value !== entry ||
      formElement.elements.fecha_salida.value !== exit
    ) return;

    select.replaceChildren(new Option(
      rooms.length ? "Elige una habitación" : "No hay habitaciones libres en esas fechas",
      "",
    ));
    for (const room of rooms) {
      select.add(new Option(`Habitación ${room.habitacion} · Piso ${room.piso}`, room.habitacion));
    }
    select.disabled = rooms.length === 0;
    hintElement.textContent = rooms.length
      ? `${rooms.length} habitación(es) libre(s) en las fechas seleccionadas.`
      : "Prueba otras fechas; las solicitudes pendientes y confirmadas ocupan habitación.";
  } catch (error) {
    select.replaceChildren(new Option("No se pudo cargar disponibilidad", ""));
    hintElement.textContent = error.message;
  }
}

function openAdminBookingDialog() {
  if (!currentUser || currentUser.role !== "admin") return;
  reservationForm.reset();
  reservationForm.elements.fecha_entrada.value = selectedDate;
  reservationForm.elements.fecha_salida.value = addDays(selectedDate, 1);
  updateAdminDateRange();
  bookingDialog.showModal();
  refreshAvailableRooms(reservationForm, document.querySelector("#admin-room-hint"));
}

async function loadReservations() {
  if (!token || !currentUser) return;
  setApiState("loading", "Conectando");

  try {
    const data = await apiRequest("/reservas", {
      headers: { Accept: "application/json", Authorization: "Bearer " + token },
    });
    if (!Array.isArray(data)) throw new Error("La API devolvió una lista inválida.");

    reservations.splice(0, reservations.length, ...data);
    setApiState("online", "API conectada");

    if (currentUser.role === "admin") {
      const rooms = await apiRequest("/habitaciones", {
        headers: { Accept: "application/json", Authorization: "Bearer " + token },
      });
      document.querySelector("#room-inventory-summary").textContent =
        `Inventario: ${rooms.length} habitaciones · pisos 1 a 4`;
      renderCalendar();
      renderAgenda();
      renderPendingRequests();
      setMessage(message, data.length + " reserva(s) cargada(s).", "success");
    } else {
      renderGuestReservations();
      setMessage(document.querySelector("#guest-message"), "", "");
    }
  } catch (error) {
    setApiState("error", "API sin conexión");
    if (currentUser.role === "user") {
      setMessage(document.querySelector("#guest-message"), error.message, "error");
    } else {
      setMessage(message, error.message, "error");
    }
  }
}

async function startSession(data) {
  token = data.token;
  showAuthenticatedView(data);
  setApiState("loading", "Conectando");
  await loadReservations();
}

document.querySelector("#login-tab").addEventListener("click", () => setAuthMode("login"));
document.querySelector("#register-tab").addEventListener("click", () => setAuthMode("register"));

document.querySelector("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  const status = document.querySelector("#auth-message");
  setMessage(status, "Validando credenciales…");
  try {
    const data = await apiRequest("/login", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        username: form.get("username"),
        clave: form.get("clave"),
      }),
    });
    formElement.reset();
    await startSession(data);
  } catch (error) {
    setMessage(status, error.message, "error");
  }
});

document.querySelector("#register-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const formElement = event.currentTarget;
  const form = new FormData(formElement);
  const status = document.querySelector("#auth-message");
  setMessage(status, "Creando cuenta…");
  try {
    const data = await apiRequest("/register", {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify({
        huesped: form.get("huesped"),
        correo: form.get("correo"),
        clave: form.get("clave"),
      }),
    });
    formElement.reset();
    await startSession(data);
  } catch (error) {
    setMessage(status, error.message, "error");
  }
});

document.querySelector("#auth-button").addEventListener("click", clearSession);

document.querySelector("#previous-month").addEventListener("click", () => {
  visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() - 1, 1);
  selectedDate = dateKey(visibleMonth);
  renderCalendar();
  renderAgenda();
});

document.querySelector("#next-month").addEventListener("click", () => {
  visibleMonth = new Date(visibleMonth.getFullYear(), visibleMonth.getMonth() + 1, 1);
  selectedDate = dateKey(visibleMonth);
  renderCalendar();
  renderAgenda();
});

document.querySelector("#today-button").addEventListener("click", () => {
  const today = new Date();
  visibleMonth = startOfMonth(today);
  selectedDate = dateKey(today);
  renderCalendar();
  renderAgenda();
});

document.querySelector("#new-booking-button").addEventListener("click", openAdminBookingDialog);
document.querySelector("#side-new-button").addEventListener("click", openAdminBookingDialog);
reservationForm.elements.fecha_entrada.addEventListener("change", updateAdminDateRange);
reservationForm.elements.fecha_salida.addEventListener("change", updateAdminDateRange);
reservationForm.elements.fecha_entrada.addEventListener("change", () => refreshAvailableRooms(
  reservationForm,
  document.querySelector("#admin-room-hint"),
));
reservationForm.elements.fecha_salida.addEventListener("change", () => refreshAvailableRooms(
  reservationForm,
  document.querySelector("#admin-room-hint"),
));

reservationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!token || !currentUser || currentUser.role !== "admin") return;

  const button = document.querySelector("#save-booking-button");
  const form = new FormData(reservationForm);
  const booking = Object.fromEntries(form.entries());
  booking.numero_huespedes = Number(booking.numero_huespedes);
  button.disabled = true;
  button.textContent = "Guardando…";

  try {
    const result = await apiRequest("/reservas", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
        Accept: "application/json",
      },
      body: JSON.stringify(booking),
    });
    bookingDialog.close();
    setMessage(message, result.message || "Reserva creada.", "success");
    await loadReservations();
  } catch (error) {
    setMessage(message, error.message, "error");
  } finally {
    button.disabled = false;
    button.textContent = "Guardar reserva";
  }
});

guestForm.elements.fecha_entrada.addEventListener("change", updateGuestDateRange);
guestForm.elements.fecha_salida.addEventListener("change", updateGuestDateRange);
guestForm.elements.fecha_entrada.addEventListener("change", () => refreshAvailableRooms(
  guestForm,
  document.querySelector("#guest-room-hint"),
));
guestForm.elements.fecha_salida.addEventListener("change", () => refreshAvailableRooms(
  guestForm,
  document.querySelector("#guest-room-hint"),
));

guestForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!token || !currentUser || currentUser.role !== "user") return;

  const button = document.querySelector("#guest-submit");
  const form = new FormData(guestForm);
  const booking = Object.fromEntries(form.entries());
  booking.numero_huespedes = Number(booking.numero_huespedes);
  button.disabled = true;
  button.textContent = "Enviando…";

  try {
    const result = await apiRequest("/reservas", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: "Bearer " + token,
        Accept: "application/json",
      },
      body: JSON.stringify(booking),
    });
    guestForm.reset();
    guestForm.elements.numero_huespedes.value = "1";
    setMessage(document.querySelector("#guest-message"), result.message, "success");
    await loadReservations();
  } catch (error) {
    setMessage(document.querySelector("#guest-message"), error.message, "error");
  } finally {
    button.disabled = false;
    button.textContent = "Enviar solicitud";
  }
});

document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => {
    document.getElementById(button.dataset.close).close();
  });
});

bookingDialog.addEventListener("click", (event) => {
  const bounds = bookingDialog.getBoundingClientRect();
  if (
    event.clientX < bounds.left || event.clientX > bounds.right ||
    event.clientY < bounds.top || event.clientY > bounds.bottom
  ) bookingDialog.close();
});

setAuthMode(authMode);
setApiState("loading", "Inicia sesión");
