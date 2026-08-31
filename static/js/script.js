// ---------------------------------------------------------
// SOZLAMALAR
// ---------------------------------------------------------
// Django backend shu domenda ishlaydigan bo'lsa nisbiy yo'l yetarli.
// Agar frontend alohida domenda joylashsa, to'liq manzil yozing:
// masalan "https://api.atlogisticgroup.com/api"
const API_BASE = "/user/api";

// Bu yerda "delivered" statusini backend qanday kod bilan qaytarishini
// belgilaymiz — DRF serializer shu qiymatni yuborishi kerak.
const DELIVERED_CODE = "delivered";

const tg = window.Telegram?.WebApp;

if (tg) {
  tg.ready();
  tg.expand();

  // Optional chaining — eski Telegram client'larda bu metodlar
  // bo'lmasligi mumkin, xatolik chiqarmasin.
  tg.disableVerticalSwipes?.();

  applyTelegramTheme();
  tg.onEvent("themeChanged", applyTelegramTheme);
}

// Telegram theme ranglarini CSS custom property'larga yozib qo'yamiz —
// shunda dizayn dark/light mode bilan avtomatik moslashadi.
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

// DEMO_MODE = true bo'lsa, hech qanday backend kerak emas — pastdagi
// DEMO_DATA'dan javob qaytadi. Django API tayyor bo'lgach shu yerni
// false qiling, boshqa hech narsani o'zgartirish shart emas.
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
      {
        status_display: "Qabul qilindi (Xitoy sklad)",
        location: "Guangzhou",
        timestamp: "2026-08-05T09:15:00",
        comment: "",
      },
      {
        status_display: "Chegaradan o'tdi",
        location: "Xorgos",
        timestamp: "2026-08-08T14:30:00",
        comment: "",
      },
      {
        status_display: "Yo'lda (Qozog'iston)",
        location: "Shymkent",
        timestamp: "2026-08-11T18:00:00",
        comment: "Ob-havo sababli ~1 kunlik kechikish bo'lishi mumkin.",
      },
    ],
  },
  "ATL-24002": {
    tracking_number: "ATL-24002",
    status: "delivered",
    status_display: "Yetkazib berildi",
    origin: "Guangzhou, Xitoy",
    destination: "Samarqand, O'zbekiston",
    history: [
      {
        status_display: "Qabul qilindi (Xitoy sklad)",
        location: "Guangzhou",
        timestamp: "2026-07-20T10:00:00",
        comment: "",
      },
      {
        status_display: "Chegaradan o'tdi",
        location: "Xorgos",
        timestamp: "2026-07-23T11:20:00",
        comment: "",
      },
      {
        status_display: "Toshkent skladiga yetib keldi",
        location: "Toshkent",
        timestamp: "2026-07-27T08:45:00",
        comment: "",
      },
      {
        status_display: "Yetkazib berildi",
        location: "Samarqand",
        timestamp: "2026-07-29T16:10:00",
        comment: "Mijoz tomonidan qabul qilingan.",
      },
    ],
  },
  "ATL-24150": {
    tracking_number: "ATL-24150",
    status: "accepted",
    status_display: "Qabul qilindi (Xitoy sklad)",
    origin: "Guangzhou, Xitoy",
    destination: "Farg'ona, O'zbekiston",
    history: [
      {
        status_display: "Qabul qilindi (Xitoy sklad)",
        location: "Guangzhou",
        timestamp: "2026-08-13T12:00:00",
        comment: "",
      },
    ],
  },
};
// Demo rejimda shu nomerlardan birini kiriting: ATL-24081, ATL-24002, ATL-24150
// Boshqa har qanday nomer "topilmadi" holatini ko'rsatadi.

// ---------------------------------------------------------
// DOM elementlar (barchasi bitta joyda)
// ---------------------------------------------------------
const form = document.getElementById("track-form");
const input = document.getElementById("tracking-input");
const submitBtn = document.getElementById("track-submit");
const formError = document.getElementById("form-error");

const resultSection = document.getElementById("result");
const emptyState = document.getElementById("empty-state");

const historyOpenBtn = document.getElementById("history-open-btn");
const historyCloseBtn = document.getElementById("history-close-btn");
const historyDrawer = document.getElementById("history-drawer");
const historyOverlay = document.getElementById("history-overlay");
const historyList = document.getElementById("history-list");
const historyEmpty = document.getElementById("history-empty");
const historyLoadMoreBtn = document.getElementById("history-load-more");

document.getElementById("year").textContent = new Date().getFullYear();

// ---------------------------------------------------------
// LOCALSTORAGE — YUKLAR TARIXI (Telegram tashqarisidagi fallback)
// ---------------------------------------------------------
async function openHistoryDrawer() {
  historyDrawer.classList.add("is-open");
  historyOverlay.hidden = false;
  requestAnimationFrame(() => historyOverlay.classList.add("is-open"));
  historyDrawer.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";

  // Native orqaga tugmasi drawer'ni yopsin
  if (tg?.BackButton) {
    tg.BackButton.show();
    tg.BackButton.onClick(closeHistoryDrawer);
  }

  if (isTelegramMode()) {
    await loadHistoryFirstPage();
  } else {
    renderHistoryList(getHistory());
  }
}

function closeHistoryDrawer() {
  historyDrawer.classList.remove("is-open");
  historyOverlay.classList.remove("is-open");
  historyDrawer.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  setTimeout(() => {
    historyOverlay.hidden = true;
  }, 200);

  if (tg?.BackButton) {
    tg.BackButton.hide();
    tg.BackButton.offClick(closeHistoryDrawer);
  }
}


const HISTORY_KEY = "atl_tracking_history";
const HISTORY_LIMIT = 15;

function getHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    // localStorage o'chirilgan yoki ma'lumot buzilgan bo'lishi mumkin —
    // bunday holatda ilova qulab tushmasligi uchun bo'sh ro'yxat qaytaramiz.
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

  // Telegram ichida bu funksiya umuman chaqirilmaydi (tarix backend'dan olinadi),
  // shuning uchun bu yerda har doim localStorage ro'yxatini chizamiz.
  renderHistoryList(getHistory());
}

// ---------------------------------------------------------
// YUKLAR TARIXI — PAGINATION HOLATI (faqat Telegram rejimi uchun)
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

// Drawer har ochilganda birinchi sahifadan boshlanadi
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
    // Backend javob bermasa — qurilmadagi tarixga qaytamiz (fallback)
    historyState.hasMore = false;
    renderHistoryList(getHistory());
  } finally {
    setHistoryLoading(false);
  }
}

// "Yana yuklash" bosilganda keyingi sahifani so'raymiz va ro'yxatga qo'shamiz
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
    showHistoryLoadError();
  } finally {
    setHistoryLoading(false);
  }
}

function setHistoryLoading(isLoading) {
  historyState.isLoading = isLoading;
  historyLoadMoreBtn.classList.toggle("is-loading", isLoading);
  historyLoadMoreBtn.disabled = isLoading;
  // Telegram rejimida emasmiz — tugma umuman ko'rinmasin
  historyLoadMoreBtn.hidden = !isTelegramMode() || !historyState.hasMore;
}

function showHistoryLoadError() {
  // Oddiy holatda tugma matnini vaqtincha o'zgartiramiz — alohida error blok shart emas
  const text = historyLoadMoreBtn.querySelector(".btn-text");
  const original = text.textContent;
  text.textContent = "Xatolik, qayta urinish";
  setTimeout(() => {
    text.textContent = original;
  }, 2000);
}

// ---------------------------------------------------------
// Forma yuborilishi
// ---------------------------------------------------------
form.addEventListener("submit", (event) => {
  event.preventDefault();
  performSearch(input.value.trim());
});

// Qidiruvni bitta joyda jamlaganmiz — forma orqali ham,
// tarix ro'yxatidan bosilganda ham shu funksiya ishlaydi.
async function performSearch(trackingNumber) {
  hideError();

  if (!trackingNumber) {
    showError("Track-nomerni kiriting.");
    return;
  }

  input.value = trackingNumber;
  setLoading(true);
  hideAllResultBlocks();

  try {
      const cargo = await fetchCargo(trackingNumber);
      renderResult(cargo);
      saveToHistory(cargo);
      tg?.HapticFeedback?.notificationOccurred("success");
    } catch (err) {
      if (err.status === 404) {
        emptyState.hidden = false;
        tg?.HapticFeedback?.notificationOccurred("warning");
      } else {
        showError("Server bilan bog'lanishda xatolik. Birozdan so'ng qayta urinib ko'ring.");
        tg?.HapticFeedback?.notificationOccurred("error");
      }
    } finally {
    setLoading(false);
  }
}

// ---------------------------------------------------------
// API chaqiruvi (demo yoki real)
// ---------------------------------------------------------
async function fetchCargo(trackingNumber) {
  if (DEMO_MODE) {
    return fetchCargoDemo(trackingNumber);
  }

  // encodeURIComponent — track-nomer ichida "/" yoki bo'shliq bo'lsa ham
  // URL buzilib ketmasligi uchun.
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
// Kutilayotgan JSON shakli (Django/DRF tomonidan):
// {
//   "tracking_number": "ATL-24081",
//   "status": "in_transit",
//   "status_display": "Yo'lda (Qozog'iston)",
//   "origin": "Guangzhou, Xitoy",
//   "destination": "Toshkent, O'zbekiston",
//   "history": [
//     {
//       "status_display": "Qabul qilindi (Xitoy)",
//       "location": "Guangzhou",
//       "timestamp": "2026-08-01T10:00:00Z",
//       "comment": ""
//     },
//     ...
//   ]
// }
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
    // Rasm bo'lmasa elementni butunlay yashiramiz — bo'sh "broken image" ikonkasi ko'rinmasin
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
  list.textContent = ""; // avvalgi natijani tozalash

  if (history.length === 0) {
    const li = document.createElement("li");
    li.className = "timeline-item";
    li.textContent = "Hozircha holat tarixi mavjud emas.";
    list.appendChild(li);
    return;
  }

  // Backend odatda eskidan yangiga qarab yuboradi — ekranda
  // eng yangi voqea tepada chiqishi uchun teskari aylantiramiz.
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

// Logotipdagi belgini (panel + uchburchak) timeline nuqtasi sifatida
// qayta yasaydi — sahifaning "imzo" elementi shu yerda takrorlanadi.
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
// YUKLAR TARIXI PANELI — ochish/yopish va chizish
// ---------------------------------------------------------
function renderHistoryList(items) {
  historyList.textContent = "";

  const hasItems = items.length > 0;
  historyEmpty.hidden = hasItems;

  // "Yana yuklash" faqat Telegram + hasMore bo'lganda ko'rinadi
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

    button.addEventListener("click", () => {
      closeHistoryDrawer();
      performSearch(item.tracking_number);
      document.getElementById("track-form").scrollIntoView({ behavior: "smooth" });
    });

    li.appendChild(button);
    historyList.appendChild(li);
  });
}

async function openHistoryDrawer() {
  historyDrawer.classList.add("is-open");
  historyOverlay.hidden = false;
  requestAnimationFrame(() => historyOverlay.classList.add("is-open"));
  historyDrawer.setAttribute("aria-hidden", "false");
  document.body.style.overflow = "hidden";

  if (isTelegramMode()) {
    await loadHistoryFirstPage();
  } else {
    // Telegram tashqarisida pagination shart emas — localStorage HISTORY_LIMIT'dan oshmaydi
    renderHistoryList(getHistory());
  }
}

function closeHistoryDrawer() {
  historyDrawer.classList.remove("is-open");
  historyOverlay.classList.remove("is-open");
  historyDrawer.setAttribute("aria-hidden", "true");
  document.body.style.overflow = "";
  setTimeout(() => {
    historyOverlay.hidden = true;
  }, 200);
}

historyOpenBtn.addEventListener("click", openHistoryDrawer);
historyCloseBtn.addEventListener("click", closeHistoryDrawer);
historyOverlay.addEventListener("click", closeHistoryDrawer);
historyLoadMoreBtn.addEventListener("click", loadHistoryNextPage);

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && historyDrawer.classList.contains("is-open")) {
    closeHistoryDrawer();
  }
});

// ---------------------------------------------------------
// Yordamchi funksiyalar
// ---------------------------------------------------------
function setLoading(isLoading) {
  submitBtn.classList.toggle("is-loading", isLoading);
  submitBtn.disabled = isLoading;
}

function hideAllResultBlocks() {
  resultSection.hidden = true;
  emptyState.hidden = true;
}

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
}

function hideError() {
  formError.hidden = true;
}