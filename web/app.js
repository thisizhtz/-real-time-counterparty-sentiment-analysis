const positiveTerms = [
  "investment grade",
  "liquidity buffer",
  "well capitalized",
  "capital raise",
  "approved",
  "beat",
  "compliant",
  "confidence",
  "deleveraging",
  "improved",
  "profitable",
  "recovered",
  "resolved",
  "stable",
  "upgrade",
  "upgraded",
];

const negativeTerms = [
  "systemic financial risks",
  "missed payment",
  "negative outlook",
  "growing links",
  "bankruptcy",
  "contagion",
  "amplify",
  "breach",
  "default",
  "distress",
  "downgrade",
  "fraud",
  "illiquid",
  "insolvent",
  "lawsuit",
  "loss",
  "probe",
  "restructuring",
  "risk",
  "risks",
  "sanction",
  "stress",
  "volatile",
  "warned",
];

const riskTerms = {
  "amplify systemic financial risks": "systemic_risk_amplification",
  "systemic financial risks": "systemic_risk",
  "systemic risk": "systemic_risk",
  "growing links": "interconnectedness_risk",
  "private credit": "private_credit_exposure",
  "banks and private credit": "bank_private_credit_linkage",
  contagion: "contagion_risk",
  default: "credit_default",
  "missed payment": "payment_stress",
  sanction: "sanctions_exposure",
  fraud: "conduct_risk",
  bankruptcy: "bankruptcy_risk",
  insolvent: "solvency_risk",
  breach: "contract_breach",
};

const dimensionLexicons = {
  credit: {
    default: 1.0,
    "missed payment": 1.0,
    downgrade: 0.7,
    "negative outlook": 0.6,
    restructuring: 0.8,
    distress: 0.7,
    loss: 0.45,
  },
  liquidity: {
    illiquid: 1.0,
    "liquidity squeeze": 0.9,
    "funding pressure": 0.85,
    withdrawal: 0.65,
    "liquidity buffer": -0.65,
  },
  systemic: {
    "systemic financial risks": 1.0,
    "systemic risk": 1.0,
    "amplify systemic financial risks": 1.2,
    contagion: 0.9,
    "growing links": 0.7,
    "banks and private credit": 0.85,
    "private credit": 0.45,
    interconnected: 0.7,
    "financial stability board": 0.55,
  },
  legal_conduct: {
    fraud: 1.0,
    lawsuit: 0.75,
    probe: 0.65,
    sanction: 0.95,
    breach: 0.75,
  },
  market: {
    volatile: 0.7,
    selloff: 0.8,
    "spread widening": 0.85,
    drawdown: 0.65,
    "negative outlook": 0.5,
  },
  resilience: {
    "well capitalized": -0.9,
    "investment grade": -0.75,
    stable: -0.55,
    upgrade: -0.7,
    upgraded: -0.7,
    resolved: -0.6,
    compliant: -0.45,
  },
};

const negators = new Set(["not", "no", "never", "without", "hardly"]);
const intensifiers = new Set(["amplify", "growing", "material", "significant", "severe", "sharp", "elevated", "warned"]);

const sampleEvents = [
  {
    event_id: "evt-106",
    counterparty: "Global Private Credit Market",
    source: "reuters",
    timestamp: "2026-05-06T11:10:00Z",
    text: "The Financial Stability Board warned that growing links between banks and private credit firms could amplify systemic financial risks.",
  },
  {
    event_id: "evt-107",
    counterparty: "HSBC",
    source: "sec filing",
    timestamp: "2026-05-06T12:00:00Z",
    text: "HSBC disclosed a $400 million fraud loss exposure and a 12% liquidity squeeze after a covenant breach.",
  },
  {
    event_id: "evt-108",
    counterparty: "Omega Bank",
    source: "reuters",
    timestamp: "2026-05-06T12:30:00Z",
    text: "Omega Bank denied fraud allegations and said no evidence of misconduct was found after an internal review.",
  },
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
const simulateButton = document.querySelector("#simulate-button");
const loadSampleButton = document.querySelector("#load-sample");
const resultList = document.querySelector("#result-list");
const resultCount = document.querySelector("#result-count");
const summaryCards = document.querySelector("#summary-cards");
const trendChart = document.querySelector("#trend-chart");
const topCounterparties = document.querySelector("#top-counterparties");
const riskBreakdown = document.querySelector("#risk-breakdown");
const eventTimeline = document.querySelector("#event-timeline");
let simulationTimer = null;

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

function findDimensionScores(text) {
  return Object.fromEntries(
    Object.entries(dimensionLexicons).map(([dimension, lexicon]) => {
      const rawScore = Object.entries(lexicon).reduce(
        (total, [term, weight]) => (containsTerm(text, term) ? total + weight : total),
        0,
      );
      return [dimension, Number(Math.tanh(rawScore / 2).toFixed(4))];
    }),
  );
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

function intensityMultiplier(text) {
  const matchedIntensifiers = [...intensifiers].filter((term) => containsTerm(text, term)).length;
  return Math.min(1.4, 1 + 0.08 * matchedIntensifiers);
}

function analyzeEvent(event) {
  const normalizedText = normalize(event.text || "");
  const matchedPositiveTerms = findTerms(normalizedText, positiveTerms);
  const matchedNegativeTerms = findTerms(normalizedText, negativeTerms);
  const dimensionScores = findDimensionScores(normalizedText);
  const positiveScore = matchedPositiveTerms.reduce((total, term) => total + termWeight(term), 0);
  const negativeScore = matchedNegativeTerms.reduce((total, term) => total + termWeight(term), 0);
  const dimensionRiskPressure = Object.values(dimensionScores)
    .filter((score) => score > 0)
    .reduce((total, score) => total + score, 0);
  const dimensionResilience = Math.abs(
    Object.values(dimensionScores)
      .filter((score) => score < 0)
      .reduce((total, score) => total + score, 0),
  );
  const rawScore =
    ((positiveScore + 0.65 * dimensionResilience) - (negativeScore + 0.75 * dimensionRiskPressure)) *
      intensityMultiplier(normalizedText) +
    negationAdjustment(normalizedText, matchedPositiveTerms, matchedNegativeTerms);
  const score = Math.tanh(rawScore / 4);
  const label = score >= 0.15 ? "positive" : score <= -0.15 ? "negative" : "neutral";
  const riskFlags = buildRiskFlags(normalizedText, dimensionScores);
  const confidence = Math.min(
    1,
    Math.abs(score) + 0.1 * (matchedPositiveTerms.length + matchedNegativeTerms.length) + 0.08 * riskFlags.length,
  );
  const severity = severityFromScores(dimensionScores, score);

  return {
    event,
    label,
    score: Number(score.toFixed(4)),
    confidence: Number(confidence.toFixed(4)),
    matchedPositiveTerms,
    matchedNegativeTerms,
    riskFlags,
    dimensionScores,
    severity,
    explanation: buildExplanation(matchedPositiveTerms, matchedNegativeTerms, dimensionScores, riskFlags),
  };
}

function buildRiskFlags(text, dimensionScores) {
  const flags = Object.entries(riskTerms)
    .filter(([term]) => containsTerm(text, term))
    .map(([, flag]) => flag);
  Object.entries(dimensionScores).forEach(([dimension, score]) => {
    if (score >= 0.45) flags.push(`${dimension}_risk`);
  });
  return [...new Set(flags)].sort();
}

function severityFromScores(dimensionScores, score) {
  const maxDimension = Math.max(...Object.values(dimensionScores), 0);
  if (score <= -0.65 || maxDimension >= 0.75) return "high";
  if (score <= -0.35 || maxDimension >= 0.45) return "medium";
  return "low";
}

function buildExplanation(positiveMatches, negativeMatches, dimensionScores, riskFlags) {
  const topDimensions = Object.entries(dimensionScores)
    .filter(([, score]) => Math.abs(score) > 0.05)
    .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
    .slice(0, 3)
    .map(([dimension, score]) => `${dimension}=${score.toFixed(2)}`);
  const parts = [];
  if (negativeMatches.length) parts.push(`negative terms: ${negativeMatches.slice(0, 4).join(", ")}`);
  if (positiveMatches.length) parts.push(`positive terms: ${positiveMatches.slice(0, 4).join(", ")}`);
  if (topDimensions.length) parts.push(`dimensions: ${topDimensions.join(", ")}`);
  if (riskFlags.length) parts.push(`flags: ${riskFlags.slice(0, 4).join(", ")}`);
  return parts.join("; ") || "no material lexicon signal detected";
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
  const highSeverityEvents = results.filter((result) => result.severity === "high").length;
  const systemicAverage = averageDimension(results, "systemic");

  summaryCards.innerHTML = [
    ["事件数量", results.length],
    ["交易对手方", snapshots.length],
    ["高风险事件", highSeverityEvents],
    ["系统性风险均值", systemicAverage.toFixed(4)],
    ["负面事件", negativeEvents],
    ["平均分", averageScore(results).toFixed(4)],
  ]
    .map(([label, value]) => `<article class="summary-card"><span>${label}</span><strong>${value}</strong></article>`)
    .join("");
}

function averageScore(results) {
  return results.length ? results.reduce((total, result) => total + result.score, 0) / results.length : 0;
}

function averageDimension(results, dimension) {
  return results.length
    ? results.reduce((total, result) => total + (result.dimensionScores[dimension] || 0), 0) / results.length
    : 0;
}

function renderResults(results) {
  resultCount.textContent = `${results.length} events`;
  renderSummary(results);
  renderDashboard(results);

  if (!results.length) {
    resultList.className = "result-list empty-state";
    resultList.innerHTML = "<p>点击“分析事件”后将在这里显示情绪分数、多维风险、命中词与风险旗标。</p>";
    return;
  }

  resultList.className = "result-list";
  resultList.innerHTML = results.map(renderResultCard).join("");
}


function renderDashboard(results) {
  renderTrendChart(results);
  renderTopCounterparties(results);
  renderRiskBreakdown(results);
  renderEventTimeline(results);
}

function renderTrendChart(results) {
  if (!results.length) {
    trendChart.innerHTML = '<p class="placeholder">暂无趋势数据</p>';
    return;
  }
  const points = results.map((result, index) => {
    const x = results.length === 1 ? 50 : (index / (results.length - 1)) * 100;
    const y = 50 - result.score * 42;
    return `${x.toFixed(2)},${y.toFixed(2)}`;
  });
  trendChart.innerHTML = `
    <svg viewBox="0 0 100 100" role="img" aria-label="rolling risk trend">
      <line x1="0" y1="50" x2="100" y2="50" class="axis"></line>
      <polyline points="${points.join(" ")}" class="trend-line"></polyline>
      ${points.map((point) => `<circle cx="${point.split(",")[0]}" cy="${point.split(",")[1]}" r="2.2"></circle>`).join("")}
    </svg>
  `;
}

function renderTopCounterparties(results) {
  const grouped = results.reduce((items, result) => {
    const key = result.event.counterparty;
    if (!items[key]) items[key] = { count: 0, risk: 0 };
    items[key].count += 1;
    items[key].risk += Math.max(0, -result.score) + (result.severity === "high" ? 0.4 : result.severity === "medium" ? 0.2 : 0);
    return items;
  }, {});
  const rows = Object.entries(grouped)
    .map(([name, value]) => [name, value.risk / value.count, value.count])
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);
  topCounterparties.innerHTML = rows.length
    ? rows.map(([name, risk, count]) => `<div class="mini-row"><span>${escapeHtml(name)}</span><strong>${risk.toFixed(2)}</strong><small>${count} events</small></div>`).join("")
    : '<p class="placeholder">暂无交易对手方</p>';
}

function renderRiskBreakdown(results) {
  const counts = results.reduce((items, result) => {
    result.riskFlags.forEach((flag) => {
      items[flag] = (items[flag] || 0) + 1;
    });
    return items;
  }, {});
  const rows = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 6);
  riskBreakdown.innerHTML = rows.length
    ? rows.map(([flag, count]) => `<div class="mini-row"><span>${escapeHtml(flag)}</span><strong>${count}</strong></div>`).join("")
    : '<p class="placeholder">暂无风险标签</p>';
}

function renderEventTimeline(results) {
  const rows = [...results].slice(-6).reverse();
  eventTimeline.innerHTML = rows.length
    ? rows.map((result) => `<div class="timeline-item"><b class="severity-dot ${result.severity}"></b><span>${escapeHtml(result.event.counterparty)}</span><small>${escapeHtml(result.event.event_id || result.event.source || "event")}</small></div>`).join("")
    : '<p class="placeholder">暂无事件</p>';
}

function toggleSimulation() {
  if (simulationTimer) {
    clearInterval(simulationTimer);
    simulationTimer = null;
    simulateButton.textContent = "模拟直播";
    return;
  }
  simulateButton.textContent = "停止模拟";
  let index = 0;
  input.value = "";
  renderResults([]);
  simulationTimer = setInterval(() => {
    input.value += `${JSON.stringify(sampleEvents[index % sampleEvents.length])}\n`;
    analyzeInput();
    index += 1;
    if (index >= sampleEvents.length) toggleSimulation();
  }, 700);
}

function renderResultCard(result) {
  const terms = [...result.matchedPositiveTerms, ...result.matchedNegativeTerms];
  const chips = [
    ...terms.map((term) => `<span class="term-chip">${escapeHtml(term)}</span>`),
    ...result.riskFlags.map((flag) => `<span class="risk-chip">${escapeHtml(flag)}</span>`),
  ].join("");
  const dimensions = Object.entries(result.dimensionScores)
    .map(([dimension, score]) => renderDimensionBar(dimension, score))
    .join("");

  return `
    <article class="result-card severity-${result.severity}">
      <header>
        <div>
          <h4>${escapeHtml(result.event.counterparty)}</h4>
          <small>${escapeHtml(result.event.source || "unknown")} · confidence ${result.confidence.toFixed(4)} · severity ${result.severity}</small>
        </div>
        <span class="score-badge ${result.label}">${result.label} ${result.score.toFixed(4)}</span>
      </header>
      <p class="result-text">${escapeHtml(result.event.text)}</p>
      <p class="explanation">${escapeHtml(result.explanation)}</p>
      <div class="dimension-grid">${dimensions}</div>
      <div class="chip-row">${chips || '<span class="term-chip">no matched terms</span>'}</div>
    </article>
  `;
}

function renderDimensionBar(dimension, score) {
  const width = Math.min(100, Math.abs(score) * 100);
  const direction = score >= 0 ? "risk" : "resilience";
  return `
    <div class="dimension-row">
      <span>${escapeHtml(dimension)}</span>
      <div class="dimension-track"><i class="${direction}" style="width:${width}%"></i></div>
      <strong>${score.toFixed(2)}</strong>
    </div>
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
simulateButton.addEventListener("click", toggleSimulation);

loadSample();
analyzeInput();
