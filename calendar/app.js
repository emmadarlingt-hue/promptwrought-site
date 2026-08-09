/* ══════════════════════════════════════════════════════════════════════════
   Promptwrought — The Type Case

   This is the translation of the Claude Design file into ordinary browser
   JavaScript. Where the design had a `class Component extends DCLogic`,
   this has plain functions; where it had <sc-for>, this has a loop; where
   it had <sc-if>, this picks a CSS class. Nothing here needs a build step.

   It reads one global, WORDS, defined in words.js and loaded first.

   The shape of the page:
       buildTray()      draws the fifty-two compartments, once
       selectWeek()     opens one of them
       renderDetail()   fills the panel underneath
   Everything else is a helper for those three.
   ══════════════════════════════════════════════════════════════════════════ */


/* ─────────────────────────────────────────────────────────────────────────
   SETTINGS

   The two facts about this volume that aren't in words.js.
   ───────────────────────────────────────────────────────────────────────── */

// The tray holds the 2026 calendar year: weeks 1 to 52, in order.
const TOTAL_WEEKS = 52;

// Issue numbering starts at week 31 — so week 31 is Issue 001, and the
// issue number for any later week is (week - 30).
const FIRST_ISSUE_WEEK = 31;

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

// The elements we write into. Looked up once, here, rather than every time.
const tray = document.getElementById("tray");
const detailLabel = document.getElementById("detail-label");
const detailDates = document.getElementById("detail-dates");
const detailStatus = document.getElementById("detail-status");
const detailBody = document.getElementById("detail-body");
const struckCount = document.getElementById("struck-count");
const themeToggle = document.getElementById("theme-toggle");

// Which week is open, and which theme is on. These two change as the
// person uses the page; everything else is derived from them.
let selectedWeek = 1;
let theme = "light";


/* ─────────────────────────────────────────────────────────────────────────
   DATES

   Dates in words.js look like "2026-08-04". We compare them as numbers of
   milliseconds, and we build those numbers by hand with Date.UTC rather
   than letting new Date() parse the string — because a bare date string is
   read as midnight UTC, which can land on the previous day for anyone west
   of Greenwich. Doing it explicitly keeps every reader on the same day.
   ───────────────────────────────────────────────────────────────────────── */

/** Turn "2026-08-04" into a number we can compare. Returns null if absent. */
function parseDate(iso) {
  if (!iso) return null;
  const parts = iso.split("-").map(Number);
  return Date.UTC(parts[0], parts[1] - 1, parts[2]);
}

/** Turn "2026-08-04" into "4 Aug 2026" for reading. */
function formatLongDate(iso) {
  const ms = parseDate(iso);
  if (ms === null) return "";
  const d = new Date(ms);
  return d.getUTCDate() + " " + MONTHS[d.getUTCMonth()] + " " + d.getUTCFullYear();
}

/** 7 becomes "007". The tray sets every number to three digits. */
function pad3(n) {
  return String(n).padStart(3, "0");
}


/* ─────────────────────────────────────────────────────────────────────────
   READING THE DATA

   words.js is not guaranteed to be in week order, and a week could be
   missing from it altogether, so nothing below ever uses array position.
   Everything is looked up by the `week` value.
   ───────────────────────────────────────────────────────────────────────── */

/** Find the slot for a week number, or null if words.js hasn't got one. */
function slotFor(week) {
  for (let i = 0; i < WORDS.length; i++) {
    if (WORDS[i].week === week) return WORDS[i];
  }
  return null;
}

/**
 * The issue number readers know a week by — week 31 is Issue 001.
 * Returns null for the weeks before the run began, which have no issue.
 */
function issueNumberFor(week) {
  if (week < FIRST_ISSUE_WEEK) return null;
  return week - FIRST_ISSUE_WEEK + 1;
}

/**
 * Which of the three states a compartment is in.
 *
 *   released — the date has passed and a word is in the slot
 *   sealed   — the date is still in the future
 *   blank    — the date has passed but no word was ever set
 *
 * Note the order: the date is checked first. If a word is filled into
 * words.js before its issue actually goes out, this still reports it as
 * sealed and the tray keeps it hidden. That is a safety net, not the rule
 * — anything written into words.js can be read in the page source, so a
 * word should only go in once its issue has gone out.
 */
function stateOf(week) {
  const slot = slotFor(week);
  if (!slot) return "blank";

  const releaseMs = parseDate(slot.releaseDate);
  if (releaseMs === null) return "blank";
  if (releaseMs > Date.now()) return "sealed";

  return slot.word ? "released" : "blank";
}

/**
 * The most recent word out — the compartment ringed in the accent colour,
 * and the one the page opens on. Chosen by date rather than by position in
 * the tray, so it stays right however words.js is ordered.
 *
 * If nothing has been released yet, fall back to the next week due to open.
 */
function currentWeek() {
  let bestWeek = null;
  let bestMs = -Infinity;
  let earliestSealed = null;
  let earliestSealedMs = Infinity;

  for (let week = 1; week <= TOTAL_WEEKS; week++) {
    const slot = slotFor(week);
    if (!slot) continue;
    const ms = parseDate(slot.releaseDate);
    if (ms === null) continue;

    if (stateOf(week) === "released" && ms > bestMs) {
      bestMs = ms;
      bestWeek = week;
    }
    if (stateOf(week) === "sealed" && ms < earliestSealedMs) {
      earliestSealedMs = ms;
      earliestSealed = week;
    }
  }

  return bestWeek || earliestSealed || 1;
}

/** How many words are out. Shown in the colophon. */
function releasedTotal() {
  let n = 0;
  for (let week = 1; week <= TOTAL_WEEKS; week++) {
    if (stateOf(week) === "released") n++;
  }
  return n;
}


/* ─────────────────────────────────────────────────────────────────────────
   BUILDING THE TRAY

   This replaces the design's <sc-for list="{{ cells }}">: an ordinary loop
   that runs fifty-two times and builds one button each pass. The design's
   three <sc-if> branches become a choice of CSS class.
   ───────────────────────────────────────────────────────────────────────── */

/**
 * Draw all fifty-two compartments. Called once, at startup — after that,
 * selecting a week only changes which button is reachable by Tab, so the
 * buttons themselves are left alone and keyboard focus is never lost.
 */
function buildTray() {
  const current = currentWeek();
  tray.replaceChildren();

  for (let week = 1; week <= TOTAL_WEEKS; week++) {
    const slot = slotFor(week);
    const state = stateOf(week);
    const isCurrent = week === current && state === "released";
    const issue = issueNumberFor(week);
    const dateText = slot ? formatLongDate(slot.releaseDate) : "";

    const cell = document.createElement("button");
    cell.type = "button";
    cell.setAttribute("role", "gridcell");
    cell.dataset.week = week;

    // "current" is a released compartment that happens to be the newest,
    // so it is checked before the plain released case.
    cell.className = "cell cell--" + (isCurrent ? "current" : state);

    // aria-current="date" marks this as the one happening now.
    if (isCurrent) cell.setAttribute("aria-current", "date");

    /* ── the number line ──────────────────────────────────────────────
       Two numbers, and each has a side.

       The week number is the compartment's coordinate, so it sits left in
       every one of the fifty-two, quiet and unbroken. Reading down the
       left edge gives you the year whether or not a word was struck.

       The issue number is what a reader knows the word by, so where one
       exists it is added on the right and set larger. Because the two
       never share a side, a week number can't be misread as an issue
       number — which is what went wrong when both led from the left. */
    const nums = document.createElement("span");
    nums.className = "cell__num";

    const weekEl = document.createElement("span");
    weekEl.className = "cell__wk";
    weekEl.textContent = pad3(week);
    nums.append(weekEl);

    if (state === "released" && issue !== null) {
      const issueEl = document.createElement("span");
      issueEl.className = "cell__issue";
      issueEl.textContent = pad3(issue);
      nums.append(issueEl);
    }

    cell.append(nums);

    /* ── what sits under the number ───────────────────────────────── */
    if (state === "released") {
      const wordEl = document.createElement("span");
      wordEl.className = "cell__word";
      wordEl.textContent = slot.word;
      cell.append(wordEl);

      cell.setAttribute("aria-label",
        "Issue " + pad3(issue) + ", " + slot.word + ", released " + dateText);

    } else if (state === "sealed") {
      // the hatched bar standing in for a word not yet set
      const hatch = document.createElement("span");
      hatch.className = "cell__hatch";
      cell.append(hatch);

      cell.title = "Week " + pad3(week) + " — sealed, opens " + dateText;
      cell.setAttribute("aria-label",
        "Week " + pad3(week) + ", sealed, opens " + dateText);

    } else {
      cell.title = "Week " + pad3(week) + " — no issue";
      cell.setAttribute("aria-label", "Week " + pad3(week) + ", no issue");
    }

    cell.addEventListener("click", function () { selectWeek(week); });
    tray.append(cell);
  }
}


/* ─────────────────────────────────────────────────────────────────────────
   THE PANEL UNDERNEATH

   This replaces the design's {{ sel.* }} values and its two <sc-if>
   branches: one block of markup when there is a word, another when there
   isn't.
   ───────────────────────────────────────────────────────────────────────── */

/** Fill the panel for a given week. */
function renderDetail(week) {
  const slot = slotFor(week);
  const state = stateOf(week);
  const issue = issueNumberFor(week);
  const dateText = slot ? formatLongDate(slot.releaseDate) : "";
  const isCurrent = week === currentWeek() && state === "released";

  /* ── the two lines across the top ─────────────────────────────────── */

  // Released compartments are titled by issue; the rest by week alone.
  if (state === "released" && issue !== null) {
    detailLabel.innerHTML = "Issue " + pad3(issue) + " &nbsp;·&nbsp; Week " + pad3(week);
  } else {
    detailLabel.textContent = "Week " + pad3(week);
  }

  if (state === "sealed") {
    detailDates.textContent = "Opens " + dateText;
  } else if (state === "released") {
    detailDates.textContent = "Released " + dateText;
  } else {
    detailDates.textContent = dateText ? "Dated " + dateText : "";
  }

  detailStatus.textContent =
    isCurrent ? "This week" :
    state === "released" ? "Released" :
    state === "sealed" ? "Sealed" : "No issue";

  /* ── the body ─────────────────────────────────────────────────────── */

  detailBody.replaceChildren();

  // Nothing to show: sealed weeks and blank weeks each get their own note.
  if (state !== "released") {
    const panel = document.createElement("div");
    panel.className = "empty-panel";

    const title = document.createElement("h2");
    title.className = "empty-panel__title";

    const body = document.createElement("p");
    body.className = "empty-panel__body";

    if (state === "sealed") {
      title.textContent = "Not yet struck";
      body.textContent = "The compartment for this week is sealed. Its word is set on the day it opens.";
    } else {
      title.textContent = "No issue";
      body.textContent = "No word was struck for this week.";
    }

    panel.append(title, body);
    detailBody.append(panel);
    return;
  }

  // A released word.
  const entry = document.createElement("div");

  const head = document.createElement("div");
  head.className = "entry__head";

  const wordEl = document.createElement("h2");
  wordEl.className = "entry__word";
  wordEl.textContent = slot.word;

  const posEl = document.createElement("span");
  posEl.className = "entry__pos";
  posEl.textContent = slot.pos;

  head.append(wordEl, posEl);

  // definition and note may contain <em>, as documented in words.js, so
  // they go in as markup rather than as plain text.
  const defEl = document.createElement("p");
  defEl.className = "entry__def";
  defEl.innerHTML = slot.definition;

  entry.append(head, defEl);

  if (slot.note) {
    const noteEl = document.createElement("p");
    noteEl.className = "entry__note";
    noteEl.innerHTML = slot.note;
    entry.append(noteEl);
  }

  /* The footer carries a category chip and a link to the issue. Both are
     left out when the data for them is missing — words.js has no `tag`
     field yet, and issueUrl is blank until the Substack link is pasted in.
     An empty chip or a link that goes nowhere is worse than neither. */
  const tag = slot.tag || "";
  const href = slot.issueUrl || "";

  if (tag || href) {
    const foot = document.createElement("div");
    foot.className = "entry__foot";

    if (tag) {
      const tagEl = document.createElement("span");
      tagEl.className = "entry__tag";
      tagEl.textContent = tag;
      foot.append(tagEl);
    }

    if (href) {
      const link = document.createElement("a");
      link.className = "entry__link";
      link.href = href;
      link.innerHTML =
        "Read issue n&#8202;<sup>o</sup>&thinsp;" + pad3(issue) + " &#8594;";
      foot.append(link);
    }

    entry.append(foot);
  }

  detailBody.append(entry);
}


/* ─────────────────────────────────────────────────────────────────────────
   SELECTING A WEEK

   Roving tabindex: of the fifty-two buttons, exactly one is reachable with
   the Tab key at any moment — the selected one, at tabindex="0". The other
   fifty-one are at tabindex="-1", which keeps them focusable by script but
   skipped by Tab. Without this, tabbing past the tray would take fifty-two
   presses. The arrow keys move around inside it instead.
   ───────────────────────────────────────────────────────────────────────── */

/** Open a week: move the tab stop, fill the panel, update the address bar. */
function selectWeek(week) {
  selectedWeek = week;

  const cells = tray.querySelectorAll("[data-week]");
  for (let i = 0; i < cells.length; i++) {
    const cellWeek = Number(cells[i].dataset.week);
    cells[i].tabIndex = cellWeek === week ? 0 : -1;
  }

  renderDetail(week);

  // replaceState rather than pushState: the open compartment is worth
  // linking to, but not worth a back-button step for every one tried.
  try {
    history.replaceState(null, "", "#week-" + week);
  } catch (e) {
    // Fails when the page is opened straight from disk in some browsers.
    // The page works fine without it, so there is nothing to do here.
  }
}

/**
 * Work out how many columns the tray currently has, so that the up and
 * down arrows move by exactly one row. It is read back from the browser
 * rather than assumed, because the count changes at each breakpoint.
 */
function columnCount() {
  try {
    const columns = getComputedStyle(tray).gridTemplateColumns.split(" ");
    if (columns.length > 0) return columns.length;
  } catch (e) { /* fall through to the default below */ }
  return 13;
}

/** Arrow keys, Home and End move around the tray. */
function onTrayKeyDown(event) {
  const cols = columnCount();
  const steps = {
    ArrowRight: 1,
    ArrowLeft: -1,
    ArrowDown: cols,
    ArrowUp: -cols
  };

  let target;
  if (event.key === "Home") {
    target = 1;
  } else if (event.key === "End") {
    target = TOTAL_WEEKS;
  } else if (event.key in steps) {
    target = selectedWeek + steps[event.key];
  } else {
    return; // not a key we handle — let the browser have it
  }

  // Stop at the ends of the tray rather than wrapping around.
  target = Math.max(1, Math.min(TOTAL_WEEKS, target));

  event.preventDefault();
  selectWeek(target);

  // The button has to exist and be tabbable before it can take focus,
  // so this waits for the browser's next paint.
  requestAnimationFrame(function () {
    const el = tray.querySelector('[data-week="' + target + '"]');
    if (el) el.focus();
  });
}


/* ─────────────────────────────────────────────────────────────────────────
   LIGHT AND DARK

   The switch sets one attribute on <html>; the CSS at the top of style.css
   does the rest. The choice is not remembered between visits — that is how
   the design behaved.
   ───────────────────────────────────────────────────────────────────────── */

/** Apply a theme and relabel the button to offer the other one. */
function setTheme(next) {
  theme = next;
  document.documentElement.setAttribute("data-theme", theme);
  themeToggle.textContent = theme === "dark" ? "Light" : "Dark";
  themeToggle.setAttribute("aria-label",
    "Switch to " + (theme === "dark" ? "light" : "dark") + " surface");
}

function toggleTheme() {
  setTheme(theme === "dark" ? "light" : "dark");
}


/* ─────────────────────────────────────────────────────────────────────────
   ROUTING

   A link ending #week-31 opens that compartment. Selecting a compartment
   rewrites the address to match, so the address bar can always be copied.
   ───────────────────────────────────────────────────────────────────────── */

/** Read a week number out of the address bar, or null if there isn't one. */
function weekFromHash() {
  const match = /^#week-(\d{1,2})$/.exec(window.location.hash || "");
  if (!match) return null;
  const week = Number(match[1]);
  if (week < 1 || week > TOTAL_WEEKS) return null;
  return week;
}


/* ─────────────────────────────────────────────────────────────────────────
   START

   Draw everything, then open either the week named in the address bar or
   the most recent word out.
   ───────────────────────────────────────────────────────────────────────── */

function init() {
  setTheme(theme);
  themeToggle.addEventListener("click", toggleTheme);

  buildTray();
  tray.addEventListener("keydown", onTrayKeyDown);

  struckCount.textContent = pad3(releasedTotal());

  selectWeek(weekFromHash() || currentWeek());
}

init();
