const positiveTerms = [
  "investment grade",
  "liquidity buffer",
  "well capitalized",
  "approved",
  "beat",
  "compliant",
  "confidence",
  "improved",
  "profitable",
  "recovered",
  "resolved",
  "stable",
  "upgrade",
  "upgraded",
];

const negativeTerms = [
  "missed payment",
  "negative outlook",
  "bankruptcy",
  "breach",
  "default",
  "downgrade",
  "fraud",
  "illiquid",
  "insolvent",
  "lawsuit",
  "loss",
  "probe",
  "restructuring",
  "sanction",
  "volatile",
];

const riskTerms = {
  default: "credit_default",
  "missed payment": "payment_stress",
  sanction: "sanctions_exposure",
  fraud: "conduct_risk",
  bankruptcy: "bankruptcy_risk",
  insolvent: "solvency_risk",
  breach: "contract_breach",
};

const negators = new Set(["not", "no", "never", "without", "hardly"]);

const sampleEvents = [
  {
    event_id: "evt-001",
    counterparty: "Northwind Capital",
    source: "news",
    timestamp: "2026-05-10T09:00:00Z",
    text: "Northwind Capital received an upgrade after reporting a stable liquidity buffer.",
  },
  {
    event_id: "evt-002",
    counterparty: "Contoso Trading",
    source: "filing",
    timestamp: "2026-05-10T09:01:00Z",
    text: "Contoso Trading disclosed a missed payment and warned of possible restructuring.",
  },
  {
    event_id: "evt-003",
    counterparty: "Northwind Capital",
    source: "analyst-note",
    timestamp: "2026-05-10T09:02:00Z",
    text: "Analysts said the firm is well capitalized and compliant with covenant requirements.",
  },
];

const input = document.querySelector("#event-input");
const analyzeButton = document.querySelector("#analyze-button");
const clearButton = document.querySelector("#clear-button");
const loadSampleButton = document.querySelector("#load-sample");
const resultList = document.querySelector("#result-list");
const resultCount = document.querySelector("#result-count");
const summaryCards = document.querySelector("#summary-cards");

function normalize(text) {
  return (text.toLowerCase().match(/[a-z][a-z\- ]*[a-z]|[a-z]/g) || [])
    .map((token) => token.replaceAll("-", " "))
    .join(" ");
}

function containsTerm(text, term) {
  return new RegExp(`(^|\\W)${escapeRegExp(term)}($|\\W)`).test(text);
}

function escapeRegExp(value) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function findTerms(text, terms) {
  return terms.filter((term) => containsTerm(text, term));
}

function termWeight(term) {
  return 1 + 0.25 * (term.split(" ").length - 1);
}

function negationAdjustment(text, positiveMatches, negativeMatches) {
  const words = text.split(" ");
  let adjustment = 0;

  words.forEach((word, index) => {
    if (!negators.has(word)) return;
    const window = words.slice(index + 1, index + 4).join(" ");
    if (positiveMatches.some((term) => window.includes(term))) adjustment -= 1;
    if (negativeMatches.some((term) => window.includes(term))) adjustment += 1;
  });

  return adjustment;
}

function analyzeEvent(event) {
  const normalizedText = normalize(event.text || "");
  const matchedPositiveTerms = findTerms(normalizedText, positiveTerms);
  const matchedNegativeTerms = findTerms(normalizedText, negativeTerms);
  const positiveScore = matchedPositiveTerms.reduce((total, term) => total + termWeight(term), 0);
  const negativeScore = matchedNegativeTerms.reduce((total, term) => total + termWeight(term), 0);
  const rawScore = positiveScore - negativeScore + negationAdjustment(normalizedText, matchedPositiveTerms, matchedNegativeTerms);
  const score = Math.tanh(rawScore / 3);
  const label = score >= 0.15 ? "positive" : score <= -0.15 ? "negative" : "neutral";
  const confidence = Math.min(1, Math.abs(score) + 0.15 * (matchedPositiveTerms.length + matchedNegativeTerms.length));
  const riskFlags = Object.entries(riskTerms)
    .filter(([term]) => containsTerm(normalizedText, term))
    .map(([, flag]) => flag);

  return {
    event,
    label,
    score: Number(score.toFixed(4)),
    confidence: Number(confidence.toFixed(4)),
    matchedPositiveTerms,
    matchedNegativeTerms,
    riskFlags,
  };
}

function parseJsonl(value) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) => {
      try {
        const event = JSON.parse(line);
        if (!event.counterparty || !event.text) {
          throw new Error("缺少 counterparty 或 text 字段");
        }
        return event;
      } catch (error) {
        throw new Error(`第 ${index + 1} 行无效：${error.message}`);
      }
    });
}

function buildSnapshots(results) {
  return results.reduce((snapshots, result) => {
    const key = result.event.counterparty;
    if (!snapshots[key]) {
      snapshots[key] = { counterparty: key, events: 0, totalScore: 0, latestLabel: result.label, riskFlags: new Set() };
    }
    snapshots[key].events += 1;
    snapshots[key].totalScore += result.score;
    snapshots[key].latestLabel = result.label;
    result.riskFlags.forEach((flag) => snapshots[key].riskFlags.add(flag));
    return snapshots;
  }, {});
}

function renderSummary(results) {
  const snapshots = Object.values(buildSnapshots(results));
  const negativeEvents = results.filter((result) => result.label === "negative").length;
  const counterparties = snapshots.length;
  const averageScore = results.length
    ? results.reduce((total, result) => total + result.score, 0) / results.length
    : 0;

  summaryCards.innerHTML = [
    ["事件数量", results.length],
    ["交易对手方", counterparties],
    ["负面事件", negativeEvents],
    ["平均分", averageScore.toFixed(4)],
  ]
    .map(([label, value]) => `<article class="summary-card"><span>${label}</span><strong>${value}</strong></article>`)
    .join("");
}

function renderResults(results) {
  resultCount.textContent = `${results.length} events`;
  renderSummary(results);

  if (!results.length) {
    resultList.className = "result-list empty-state";
    resultList.innerHTML = "<p>点击“分析事件”后将在这里显示情绪分数、标签、命中词与风险旗标。</p>";
    return;
  }

  resultList.className = "result-list";
  resultList.innerHTML = results.map(renderResultCard).join("");
}

function renderResultCard(result) {
  const terms = [...result.matchedPositiveTerms, ...result.matchedNegativeTerms];
  const chips = [
    ...terms.map((term) => `<span class="term-chip">${escapeHtml(term)}</span>`),
    ...result.riskFlags.map((flag) => `<span class="risk-chip">${escapeHtml(flag)}</span>`),
  ].join("");

  return `
    <article class="result-card">
      <header>
        <div>
          <h4>${escapeHtml(result.event.counterparty)}</h4>
          <small>${escapeHtml(result.event.source || "unknown")} · confidence ${result.confidence.toFixed(4)}</small>
        </div>
        <span class="score-badge ${result.label}">${result.label} ${result.score.toFixed(4)}</span>
      </header>
      <p class="result-text">${escapeHtml(result.event.text)}</p>
      <div class="chip-row">${chips || '<span class="term-chip">no matched terms</span>'}</div>
    </article>
  `;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function loadSample() {
  input.value = sampleEvents.map((event) => JSON.stringify(event)).join("\n");
}

function analyzeInput() {
  try {
    const events = parseJsonl(input.value);
    renderResults(events.map(analyzeEvent));
  } catch (error) {
    resultCount.textContent = "input error";
    summaryCards.innerHTML = "";
    resultList.className = "result-list empty-state";
    resultList.innerHTML = `<p>${escapeHtml(error.message)}</p>`;
  }
}

loadSampleButton.addEventListener("click", loadSample);
analyzeButton.addEventListener("click", analyzeInput);
clearButton.addEventListener("click", () => renderResults([]));

loadSample();
analyzeInput();
