// ---------------------------------------------------------
// SOZLAMALAR
// ---------------------------------------------------------

const API_BASE = "/user/api";
const DELIVERED_CODE = "delivered";

const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();
  tg.disableVerticalSwipes?.();
  applyTelegramTheme();
  tg.onEvent("themeChanged", applyTelegramTheme);
}

function applyTelegramTheme() {
  const p = tg.themeParams;
  const root = document.documentElement.style;

  if (p.bg_color) root.setProperty("--tg-bg", p.bg_color);
  if (p.text_color) root.setProperty("--tg-text", p.text_color);
  if (p.hint_color) root.setProperty("--tg-hint", p.hint_color);
  if (p.button_color) root.setProperty("--tg-button", p.button_color);
  if (p.button_text_color) root.setProperty("--tg-button-text", p.button_text_color);
  if (p.secondary_bg_color) root.setProperty("--tg-secondary-bg", p.secondary_bg_color);
}

const DEMO_MODE = false;
const DEMO_NETWORK_DELAY_MS = 600;

const DEMO_DATA = {
  "ATL-24081": {
    tracking_number: "ATL-24081",
    status: "in_transit",
    status_display: "Yo'lda (Qozog'iston)",
    origin: "Guangzhou, Xitoy",
    destination: "Toshkent, O'zbekiston",
    history: [
      { status_display: "Qabul qilindi (Xitoy sklad)", location: "Guangzhou", timestamp: "2026-08-05T09:15:00", comment: "" },
      { status_display: "Chegaradan o'tdi", location: "Xorgos", timestamp: "2026-08-08T14:30:00", comment: "" },
      { status_display: "Yo'lda (Qozog'iston)", location: "Shymkent", timestamp: "2026-08-11T18:00:00", comment: "Ob-havo sababli ~1 kunlik kechikish bo'lishi mumkin." },
    ],
  },
  "ATL-24002": {
    tracking_number: "ATL-24002",
    status: "delivered",
    status_display: "Yetkazib berildi",
    origin: "Guangzhou, Xitoy",
    destination: "Samarqand, O'zbekiston",
    history: [
      { status_display: "Qabul qilindi (Xitoy sklad)", location: "Guangzhou", timestamp: "2026-07-20T10:00:00", comment: "" },
      { status_display: "Chegaradan o'tdi", location: "Xorgos", timestamp: "2026-07-23T11:20:00", comment: "" },
      { status_display: "Toshkent skladiga yetib keldi", location: "Toshkent", timestamp: "2026-07-27T08:45:00", comment: "" },
      { status_display: "Yetkazib berildi", location: "Samarqand", timestamp: "2026-07-29T16:10:00", comment: "Mijoz tomonidan qabul qilingan." },
    ],
  },
  "ATL-24150": {
    tracking_number: "ATL-24150",
    status: "accepted",
    status_display: "Qabul qilindi (Xitoy sklad)",
    origin: "Guangzhou, Xitoy",
    destination: "Farg'ona, O'zbekiston",
    history: [
      { status_display: "Qabul qilindi (Xitoy sklad)", location: "Guangzhou", timestamp: "2026-08-13T12:00:00", comment: "" },
    ],
  },
};

// ---------------------------------------------------------
// DOM elementlar
// ---------------------------------------------------------
const resultSection = document.getElementById("result");
const emptyState = document.getElementById("empty-state");

const historyList = document.getElementById("history-list");
const historyEmpty = document.getElementById("history-empty");
const historyLoadMoreBtn = document.getElementById("history-load-more");
const listError = document.getElementById("list-error"); // yangi element, HTML'ga qo'shildi

//document.getElementById("year").textContent = new Date().getFullYear();

// ---------------------------------------------------------
// LOCALSTORAGE — YUKLAR TARIXI (Telegram tashqarisidagi fallback)
// ---------------------------------------------------------
const HISTORY_KEY = "atl_tracking_history";
const HISTORY_LIMIT = 15;

const resultBackBtn = document.getElementById("result-back-btn");
const cargoListSection = document.querySelector(".cargo-list-section");

resultBackBtn.addEventListener("click", goBackToList);

function goBackToList() {
  hideAllResultBlocks();
  cargoListSection.scrollIntoView({ behavior: "smooth" });

  if (tg?.BackButton) {
    tg.BackButton.hide();
    tg.BackButton.offClick(goBackToList);
  }
}

function getHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveToHistory(cargo) {
  const existing = getHistory().filter(
    (item) => item.tracking_number !== cargo.tracking_number
  );

  existing.unshift({
    tracking_number: cargo.tracking_number,
    status: cargo.status,
    status_display: cargo.status_display,
    checked_at: new Date().toISOString(),
  });

  const trimmed = existing.slice(0, HISTORY_LIMIT);
  localStorage.setItem(HISTORY_KEY, JSON.stringify(trimmed));

  // Telegram rejimida bu chaqirilmaydi (tarix backend'dan), shu sabab
  // faqat localStorage rejimida ro'yxatni qayta chizamiz.
  if (!isTelegramMode()) {
    renderHistoryList(getHistory());
  }
}

// ---------------------------------------------------------
// YUKLAR RO'YXATI — PAGINATION HOLATI (faqat Telegram rejimi uchun)
// ---------------------------------------------------------
const HISTORY_PAGE_LIMIT = 15;

let historyState = {
  items: [],
  offset: 0,
  hasMore: true,
  isLoading: false,
};

function isTelegramMode() {
  return Boolean(tg && tg.initData);
}

function mapApiCargoToHistoryItem(cargo) {
  return {
    tracking_number: cargo.tracking_number,
    status: cargo.status,
    status_display: cargo.status_display,
    checked_at: cargo.created_at,
  };
}

async function fetchCargoHistoryPage(offset) {
  const url = `${API_BASE}/history/?limit=${HISTORY_PAGE_LIMIT}&offset=${offset}`;

  const response = await fetch(url, {
    method: "GET",
    headers: {
      Accept: "application/json",
      "X-Telegram-Init-Data": tg.initData,
    },
  });

  if (!response.ok) {
    const error = new Error(`History request failed: ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return response.json(); // { count, next, previous, results }
}

// Sahifa birinchi ochilganda ishga tushadi (avvalgi versiyada drawer ochilganda edi)
async function loadHistoryFirstPage() {
  historyState = { items: [], offset: 0, hasMore: true, isLoading: false };

  setHistoryLoading(true);
  try {
    const page = await fetchCargoHistoryPage(0);
    historyState.items = page.results.map(mapApiCargoToHistoryItem);
    historyState.offset = page.results.length;
    historyState.hasMore = Boolean(page.next);
    renderHistoryList(historyState.items);
  } catch {
    historyState.hasMore = false;
    renderHistoryList(getHistory());
  } finally {
    setHistoryLoading(false);
  }
}

async function loadHistoryNextPage() {
  if (!historyState.hasMore || historyState.isLoading) return;

  setHistoryLoading(true);
  try {
    const page = await fetchCargoHistoryPage(historyState.offset);
    const newItems = page.results.map(mapApiCargoToHistoryItem);

    historyState.items = historyState.items.concat(newItems);
    historyState.offset += newItems.length;
    historyState.hasMore = Boolean(page.next);

    renderHistoryList(historyState.items);
  } catch {
    showListLoadError();
  } finally {
    setHistoryLoading(false);
  }
}

function setHistoryLoading(isLoading) {
  historyState.isLoading = isLoading;
  historyLoadMoreBtn.classList.toggle("is-loading", isLoading);
  historyLoadMoreBtn.disabled = isLoading;
  historyLoadMoreBtn.hidden = !isTelegramMode() || !historyState.hasMore;
}

function showListLoadError() {
  const text = historyLoadMoreBtn.querySelector(".btn-text");
  const original = text.textContent;
  text.textContent = "Xatolik, qayta urinish";
  setTimeout(() => {
    text.textContent = original;
  }, 2000);
}

// ---------------------------------------------------------
// Sahifa yuklanganda ro'yxatni chizish
// ---------------------------------------------------------
async function initCargoList() {
  if (isTelegramMode()) {
    await loadHistoryFirstPage();
  } else {
    renderHistoryList(getHistory());
  }
}

initCargoList();

// ---------------------------------------------------------
// Qidiruv — endi ro'yxatdagi elementga bosilganda chaqiriladi
// ---------------------------------------------------------
async function performSearch(trackingNumber) {
  hideListError();
  if (!trackingNumber) return;

  hideAllResultBlocks();

  try {
    const cargo = await fetchCargo(trackingNumber);
    renderResult(cargo);
    saveToHistory(cargo);
    tg?.HapticFeedback?.notificationOccurred("success");
    resultSection.scrollIntoView({ behavior: "smooth" });

    // Telegram ichida bo'lsa — native orqaga tugmasi ro'yxatga qaytaradi
    if (tg?.BackButton) {
      tg.BackButton.show();
      tg.BackButton.onClick(goBackToList);
    }
  } catch (err) {
    if (err.status === 404) {
      emptyState.hidden = false;
      tg?.HapticFeedback?.notificationOccurred("warning");
      if (tg?.BackButton) {
        tg.BackButton.show();
        tg.BackButton.onClick(goBackToList);
      }
    } else {
      showListError("Server bilan bog'lanishda xatolik. Birozdan so'ng qayta urinib ko'ring.");
      tg?.HapticFeedback?.notificationOccurred("error");
    }
  }
}

// ---------------------------------------------------------
// API chaqiruvi (demo yoki real)
// ---------------------------------------------------------
async function fetchCargo(trackingNumber) {
  if (DEMO_MODE) {
    return fetchCargoDemo(trackingNumber);
  }

  const url = `${API_BASE}/track/${encodeURIComponent(trackingNumber)}/`;

  const response = await fetch(url, {
    method: "GET",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    const error = new Error(`Request failed: ${response.status}`);
    error.status = response.status;
    throw error;
  }

  return response.json();
}

function fetchCargoDemo(trackingNumber) {
  return new Promise((resolve, reject) => {
    setTimeout(() => {
      const key = trackingNumber.toUpperCase();
      const cargo = DEMO_DATA[key];
      if (cargo) {
        resolve(cargo);
      } else {
        const error = new Error("Not found (demo)");
        error.status = 404;
        reject(error);
      }
    }, DEMO_NETWORK_DELAY_MS);
  });
}

// ---------------------------------------------------------
// Natijani chizish
// ---------------------------------------------------------
function renderResult(cargo) {
  resultSection.hidden = false;

  document.getElementById("res-track-number").textContent = cargo.tracking_number;
  document.getElementById("res-origin").textContent = cargo.origin;
  document.getElementById("res-destination").textContent = cargo.destination;

  const image = document.getElementById("res-cargo-image");
  if (cargo.image) {
    image.src = cargo.image;
    image.alt = `Yuk rasmi — ${cargo.tracking_number}`;
    image.hidden = false;
  } else {
    image.hidden = true;
    image.src = "";
  }

  const badge = document.getElementById("res-status-badge");
  document.getElementById("res-status-text").textContent = cargo.status_display;
  badge.classList.toggle("is-delivered", cargo.status === DELIVERED_CODE);

  renderTimeline(cargo.history || []);
}

function renderTimeline(history) {
  const list = document.getElementById("timeline");
  list.textContent = "";

  if (history.length === 0) {
    const li = document.createElement("li");
    li.className = "timeline-item";
    li.textContent = "Hozircha holat tarixi mavjud emas.";
    list.appendChild(li);
    return;
  }

  const events = [...history].reverse();

  events.forEach((event, index) => {
    const li = document.createElement("li");
    li.className = "timeline-item" + (index === 0 ? " is-current" : "");

    li.appendChild(buildMarkIcon());

    const body = document.createElement("div");
    body.className = "timeline-body";

    const status = document.createElement("p");
    status.className = "timeline-status";
    status.textContent = event.status_display;
    body.appendChild(status);

    const meta = document.createElement("p");
    meta.className = "timeline-meta";
    meta.textContent = formatMeta(event.location, event.timestamp);
    body.appendChild(meta);

    if (event.comment) {
      const comment = document.createElement("p");
      comment.className = "timeline-comment";
      comment.textContent = event.comment;
      body.appendChild(comment);
    }

    li.appendChild(body);
    list.appendChild(li);
  });
}

function buildMarkIcon() {
  const svgNS = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(svgNS, "svg");
  svg.setAttribute("class", "timeline-mark");
  svg.setAttribute("viewBox", "0 0 100 100");
  svg.setAttribute("aria-hidden", "true");

  const rect = document.createElementNS(svgNS, "rect");
  rect.setAttribute("x", "8");
  rect.setAttribute("y", "8");
  rect.setAttribute("width", "84");
  rect.setAttribute("height", "24");
  rect.setAttribute("fill", "currentColor");

  const triangle = document.createElementNS(svgNS, "polygon");
  triangle.setAttribute("points", "50,38 92,92 8,92");
  triangle.setAttribute("fill", "currentColor");

  svg.appendChild(rect);
  svg.appendChild(triangle);
  return svg;
}

function formatMeta(location, timestamp) {
  const date = new Date(timestamp);
  const formatted = date.toLocaleString("uz-UZ", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
  return location ? `${location} · ${formatted}` : formatted;
}

// ---------------------------------------------------------
// Ro'yxatni chizish (endi sahifada doim ko'rinib turadi)
// ---------------------------------------------------------
function renderHistoryList(items) {
  historyList.textContent = "";

  const hasItems = items.length > 0;
  historyEmpty.hidden = hasItems;
  historyLoadMoreBtn.hidden = !isTelegramMode() || !historyState.hasMore;

  items.forEach((item) => {
    const li = document.createElement("li");

    const button = document.createElement("button");
    button.type = "button";
    button.className = "history-item";

    const top = document.createElement("div");
    top.className = "history-item-top";

    const number = document.createElement("span");
    number.className = "history-item-number";
    number.textContent = item.tracking_number;

    const status = document.createElement("span");
    status.className =
      "history-item-status" + (item.status === DELIVERED_CODE ? " is-delivered" : "");
    status.textContent = item.status_display;

    top.appendChild(number);
    top.appendChild(status);

    const time = document.createElement("p");
    time.className = "history-item-time";
    time.textContent = "Tekshirilgan: " + formatMeta(null, item.checked_at);

    button.appendChild(top);
    button.appendChild(time);

    // Endi drawer yopish shart emas — shunchaki tanlangan yukni ko'rsatamiz
    button.addEventListener("click", () => {
      performSearch(item.tracking_number);
    });

    li.appendChild(button);
    historyList.appendChild(li);
  });
}

historyLoadMoreBtn.addEventListener("click", loadHistoryNextPage);

// ---------------------------------------------------------
// Yordamchi funksiyalar
// ---------------------------------------------------------
function hideAllResultBlocks() {
  resultSection.hidden = true;
  emptyState.hidden = true;
}

function showListError(message) {
  if (!listError) {
    console.warn("list-error elementi HTML'da topilmadi");
    return;
  }
  listError.textContent = message;
  listError.hidden = false;
}

function hideListError() {
  if (!listError) return;
  listError.hidden = true;
}