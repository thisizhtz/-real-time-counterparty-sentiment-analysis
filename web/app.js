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
  "buyback",
  "guidance raise",
  "margin expansion",
  "strong demand",
  "监管批准",
  "流动性充足",
  "评级上调",
  "超预期",
  "盈利改善",
  "订单增长",
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
  "liquidity squeeze",
  "spread widening",
  "missed estimates",
  "监管调查",
  "违约",
  "流动性压力",
  "下调评级",
  "亏损",
  "欺诈",
  "制裁",
  "诉讼",
  "重组",
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
  "liquidity squeeze": "liquidity_stress",
  "spread widening": "market_stress",
  违约: "credit_default",
  欺诈: "conduct_risk",
  制裁: "sanctions_exposure",
  诉讼: "legal_risk",
  流动性压力: "liquidity_stress",
  重组: "restructuring_risk",
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
    违约: 1.0,
    下调评级: 0.7,
    重组: 0.75,
  },
  liquidity: {
    illiquid: 1.0,
    "liquidity squeeze": 0.9,
    "funding pressure": 0.85,
    withdrawal: 0.65,
    "liquidity buffer": -0.65,
    流动性压力: 0.9,
    流动性充足: -0.65,
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
    传染: 0.9,
    系统性风险: 1.0,
  },
  legal_conduct: {
    fraud: 1.0,
    lawsuit: 0.75,
    probe: 0.65,
    sanction: 0.95,
    breach: 0.75,
    欺诈: 1.0,
    诉讼: 0.75,
    制裁: 0.95,
    监管调查: 0.7,
  },
  market: {
    volatile: 0.7,
    selloff: 0.8,
    "spread widening": 0.85,
    drawdown: 0.65,
    "negative outlook": 0.5,
    波动: 0.7,
    抛售: 0.8,
  },
  resilience: {
    "well capitalized": -0.9,
    "investment grade": -0.75,
    stable: -0.55,
    upgrade: -0.7,
    upgraded: -0.7,
    resolved: -0.6,
    compliant: -0.45,
    "guidance raise": -0.65,
    评级上调: -0.7,
    稳定: -0.55,
    超预期: -0.55,
    盈利改善: -0.6,
  },
};

const negators = new Set(["not", "no", "never", "without", "hardly", "denied", "否认", "没有", "未"]);
const intensifiers = new Set(["amplify", "growing", "material", "significant", "severe", "sharp", "elevated", "warned", "重大", "显著", "严重"]);

const sampleText = `Reuters: The Financial Stability Board warned that growing links between banks and private credit firms could amplify systemic financial risks.

HSBC disclosed a $400 million fraud loss exposure and a 12% liquidity squeeze after a covenant breach.

Omega Bank denied fraud allegations and said no evidence of misconduct was found after an internal review.

Northwind Capital received an upgrade after reporting a stable liquidity buffer and stronger demand.

Contoso Trading disclosed a missed payment and warned of possible restructuring.`;

const liveNewsItems = [
  "14:01 Reuters - Northwind Capital received an upgrade as analysts cited a stable liquidity buffer and improved profitability.",
  "14:03 MarketWire - Contoso Trading warned of a missed payment and possible restructuring after spread widening.",
  "14:05 Exchange filing - Apex Semiconductor beat guidance with strong demand and margin expansion.",
  "14:08 Global News - HSBC disclosed a fraud loss exposure, but management said capital remains well capitalized.",
  "14:11 Credit desk - Meridian Bank faces liquidity squeeze rumors after large withdrawals.",
  "14:15 公司公告 - Orion Energy 获得监管批准，订单增长且现金流稳定。",
  "14:18 快讯 - Delta Retail 因诉讼和亏损被下调评级。",
];

const stockUniverse = [
  { ticker: "APX", name: "Apex Semiconductor", sector: "AI Chips" },
  { ticker: "NWC", name: "Northwind Capital", sector: "Financials" },
  { ticker: "ORN", name: "Orion Energy", sector: "Energy" },
  { ticker: "HSBC", name: "HSBC", sector: "Banks" },
  { ticker: "CTO", name: "Contoso Trading", sector: "Trading" },
  { ticker: "MDB", name: "Meridian Bank", sector: "Banks" },
  { ticker: "DLT", name: "Delta Retail", sector: "Retail" },
];

const input = document.querySelector("#event-input");
const analyzeButton = document.querySelector("#analyze-button");
const clearButton = document.querySelector("#clear-button");
const simulateButton = document.querySelector("#simulate-button");
const loadSampleButton = document.querySelector("#load-sample");
const sourceSelect = document.querySelector("#source-select");
const counterpartyInput = document.querySelector("#counterparty-input");
const resultList = document.querySelector("#result-list");
const resultCount = document.querySelector("#result-count");
const summaryCards = document.querySelector("#summary-cards");
const trendChart = document.querySelector("#trend-chart");
const topCounterparties = document.querySelector("#top-counterparties");
const riskBreakdown = document.querySelector("#risk-breakdown");
const eventTimeline = document.querySelector("#event-timeline");
const forwardReturnTable = document.querySelector("#forward-return-table");
const strategyMetrics = document.querySelector("#strategy-metrics");
const returnScatter = document.querySelector("#return-scatter");
const topNewsEvents = document.querySelector("#top-news-events");
const pageTrack = document.querySelector("#page-track");
const pageIndicator = document.querySelector("#page-indicator");
const liveNewsList = document.querySelector("#live-news-list");
const newsRadar = document.querySelector("#news-radar");
const stockPickList = document.querySelector("#stock-pick-list");
let simulationTimer = null;
let latestResults = [];
let currentPage = 0;

function normalize(text) {
  const lower = String(text).toLowerCase();
  const latinTokens = lower.match(/[a-z][a-z\- ]*[a-z]|[a-z]/g) || [];
  const cjkTokens = lower.match(/[\u4e00-\u9fa5]+/g) || [];
  return [...latinTokens.map((token) => token.replaceAll("-", " ")), ...cjkTokens].join(" ");
}

function containsTerm(text, term) {
  if (/^[\u4e00-\u9fa5]+$/.test(term)) return text.includes(term);
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
    const window = words.slice(index + 1, index + 6).join(" ");
    if (positiveMatches.some((term) => window.includes(term))) adjustment -= 1;
    if (negativeMatches.some((term) => window.includes(term))) adjustment += 1;
  });

  return adjustment;
}

function intensityMultiplier(text) {
  const matchedIntensifiers = [...intensifiers].filter((term) => containsTerm(text, term)).length;
  return Math.min(1.45, 1 + 0.08 * matchedIntensifiers);
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
  const transformerContextBoost = inferTransformerContext(event.text || "");
  const rawScore =
    ((positiveScore + 0.7 * dimensionResilience) - (negativeScore + 0.8 * dimensionRiskPressure)) *
      intensityMultiplier(normalizedText) +
    negationAdjustment(normalizedText, matchedPositiveTerms, matchedNegativeTerms) +
    transformerContextBoost;
  const score = Math.tanh(rawScore / 4);
  const label = score >= 0.15 ? "positive" : score <= -0.15 ? "negative" : "neutral";
  const riskFlags = buildRiskFlags(normalizedText, dimensionScores);
  const confidence = Math.min(
    1,
    Math.abs(score) + 0.1 * (matchedPositiveTerms.length + matchedNegativeTerms.length) + 0.08 * riskFlags.length + 0.12,
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
    model: "FinTransformer-Sim v2",
    extractedEvents: extractFinancialEvents(event.text || "", riskFlags, severity),
    explanation: buildExplanation(matchedPositiveTerms, matchedNegativeTerms, dimensionScores, riskFlags, transformerContextBoost),
  };
}

function extractFinancialEvents(text, riskFlags, severity) {
  const patterns = [
    ["upgrade", /upgrade|upgraded|评级上调/i],
    ["downgrade", /downgrade|下调评级/i],
    ["default_warning", /default|missed payment|违约/i],
    ["liquidity_stress", /liquidity squeeze|funding pressure|流动性压力/i],
    ["fraud_loss_exposure", /fraud|欺诈/i],
    ["sanctions_exposure", /sanction|制裁/i],
    ["systemic_risk_warning", /systemic financial risks|systemic risk|系统性风险/i],
  ];
  return patterns
    .filter(([, pattern]) => pattern.test(text))
    .map(([eventType]) => ({ event_type: eventType, severity, flags: riskFlags.slice(0, 3) }));
}

function inferTransformerContext(text) {
  const value = String(text).toLowerCase();
  let boost = 0;
  if (/denied|no evidence|resolved|否认|没有证据|解决/.test(value)) boost += 0.75;
  if (/beat|upgrade|strong demand|guidance raise|超预期|上调|订单增长/.test(value)) boost += 0.55;
  if (/warned|missed payment|fraud|liquidity squeeze|违约|欺诈|流动性压力/.test(value)) boost -= 0.55;
  return boost;
}

function buildRiskFlags(text, dimensionScores) {
  const flags = Object.entries(riskTerms)
    .filter(([term]) => containsTerm(text, term))
    .map(([, flag]) => flag);
  Object.entries(dimensionScores).forEach(([dimension, score]) => {
    if (score >= 0.45) flags.push(`${dimension}_risk`);
  });
  return [...new Set(flags)];
}

function severityFromScores(dimensionScores, score) {
  const maxRisk = Math.max(...Object.values(dimensionScores));
  if (score <= -0.55 || maxRisk >= 0.65) return "high";
  if (score <= -0.18 || maxRisk >= 0.35) return "medium";
  return "low";
}

function buildExplanation(positiveMatches, negativeMatches, dimensionScores, riskFlags, contextBoost) {
  const riskDimensions = Object.entries(dimensionScores)
    .filter(([, score]) => Math.abs(score) >= 0.25)
    .map(([dimension, score]) => `${dimension}:${score.toFixed(2)}`);
  const parts = [];
  if (positiveMatches.length) parts.push(`正面信号 ${positiveMatches.join(", ")}`);
  if (negativeMatches.length) parts.push(`负面信号 ${negativeMatches.join(", ")}`);
  if (riskDimensions.length) parts.push(`维度 ${riskDimensions.join(", ")}`);
  if (riskFlags.length) parts.push(`风险旗标 ${riskFlags.join(", ")}`);
  if (contextBoost !== 0) parts.push(`上下文修正 ${contextBoost > 0 ? "+" : ""}${contextBoost.toFixed(2)}`);
  return parts.join(" · ") || "未命中强信号，FinTransformer 语义层将该事件视为中性观察。";
}

function parseInput(value) {
  const trimmed = value.trim();
  if (!trimmed) return [];
  const lines = trimmed.split(/\n+/).filter(Boolean);
  if (lines.every((line) => line.trim().startsWith("{"))) {
    return lines.map((line, index) => normalizeEvent(JSON.parse(line), index));
  }
  return parseNaturalText(trimmed);
}

function parseNaturalText(text) {
  const chunks = text
    .split(/\n\s*\n|(?<=[.!?。！？])\s+(?=[A-Z\u4e00-\u9fa5])/)
    .map((item) => item.trim())
    .filter(Boolean);
  return chunks.map((chunk, index) =>
    normalizeEvent(
      {
        event_id: `nlp-${String(index + 1).padStart(3, "0")}`,
        counterparty: inferCounterparty(chunk),
        source: sourceSelect.value,
        timestamp: new Date(Date.now() + index * 1000).toISOString(),
        text: chunk,
      },
      index,
    ),
  );
}

function normalizeEvent(event, index) {
  const fallbackCounterparty = counterpartyInput.value && counterpartyInput.value !== "自动识别" ? counterpartyInput.value : `Detected Entity ${index + 1}`;
  return {
    event_id: event.event_id || `evt-${String(index + 1).padStart(3, "0")}`,
    counterparty: event.counterparty || inferCounterparty(event.text || "") || fallbackCounterparty,
    source: event.source || sourceSelect.value,
    timestamp: event.timestamp || new Date().toISOString(),
    text: event.text || String(event),
  };
}

function inferCounterparty(text) {
  const known = stockUniverse.find((item) => text.toLowerCase().includes(item.name.toLowerCase()) || text.includes(item.ticker));
  if (known) return known.name;
  const englishOrg = text.match(/\b([A-Z][A-Za-z&.-]+(?:\s+[A-Z][A-Za-z&.-]+){0,3})\b/);
  if (englishOrg) return englishOrg[1].replace(/^(Reuters|MarketWire|Exchange|Global News|Credit desk)\s*-?\s*/i, "") || englishOrg[1];
  const chineseOrg = text.match(/([\u4e00-\u9fa5A-Za-z]{2,12})(?:公司|银行|集团|资本|能源|证券)/);
  if (chineseOrg) return chineseOrg[0];
  return counterpartyInput.value && counterpartyInput.value !== "自动识别" ? counterpartyInput.value : "Auto-detected Counterparty";
}

function renderResults(results) {
  latestResults = results;
  resultCount.textContent = `${results.length} events`;
  renderSummary(results);
  renderDashboard(results);
  renderStockPicks(results);

  if (!results.length) {
    resultList.className = "result-list empty-state";
    resultList.innerHTML = "<p>点击“智能分析”后将在这里显示情绪分数、多维风险、命中词与风险旗标。</p>";
    return;
  }

  resultList.className = "result-list";
  resultList.innerHTML = results.map(renderResultCard).join("");
}

function renderSummary(results) {
  const averageScore = results.length ? results.reduce((total, result) => total + result.score, 0) / results.length : 0;
  const highRisk = results.filter((result) => result.severity === "high").length;
  const positive = results.filter((result) => result.label === "positive").length;
  summaryCards.innerHTML = [
    ["平均情绪", averageScore.toFixed(2)],
    ["高风险", highRisk],
    ["正面事件", positive],
  ]
    .map(([label, value]) => `<article class="summary-card"><span>${label}</span><strong>${value}</strong></article>`)
    .join("");
}

function renderDashboard(results) {
  const researchRows = attachSimulatedReturns(results);
  renderTrendChart(results);
  renderTopCounterparties(results);
  renderRiskBreakdown(results);
  renderEventTimeline(results);
  renderForwardReturnTable(researchRows);
  renderStrategyMetrics(researchRows);
  renderReturnScatter(researchRows);
  renderTopNewsEvents(researchRows);
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

function attachSimulatedReturns(results) {
  return results.map((result, index) => {
    const futureReturn = Number((0.018 * result.score + 0.006 * Math.sin(index + 1) - (result.severity === "high" ? 0.012 : 0)).toFixed(4));
    return {
      ...result,
      returns: {
        forward_return_1d: futureReturn,
        forward_return_3d: Number((futureReturn * 1.45).toFixed(4)),
        forward_return_5d: Number((futureReturn * 1.9).toFixed(4)),
        forward_return_10d: Number((futureReturn * 2.35).toFixed(4)),
        abnormal_return: Number((futureReturn - 0.0015).toFixed(4)),
      },
      signal: result.score > 0.15 ? 1 : result.score < -0.15 ? -1 : 0,
    };
  });
}

function renderForwardReturnTable(rows) {
  const selected = rows.slice(0, 4);
  forwardReturnTable.innerHTML = selected.length
    ? selected.map((row) => `<div class="mini-row"><span>${escapeHtml(row.event.counterparty)}</span><strong>${formatPercent(row.returns.forward_return_5d)}</strong><small>5d fwd</small></div>`).join("")
    : '<p class="placeholder">暂无收益归因</p>';
}

function renderStrategyMetrics(rows) {
  const active = rows.filter((row) => row.signal !== 0);
  const strategyReturns = active.map((row) => row.signal * row.returns.forward_return_1d);
  const cumulative = strategyReturns.reduce((value, item) => value * (1 + item), 1) - 1;
  const wins = strategyReturns.filter((item) => item > 0).length;
  const mean = strategyReturns.length ? strategyReturns.reduce((total, item) => total + item, 0) / strategyReturns.length : 0;
  const variance = strategyReturns.length ? strategyReturns.reduce((total, item) => total + (item - mean) ** 2, 0) / strategyReturns.length : 0;
  const sharpe = variance > 0 ? (mean / Math.sqrt(variance)) * Math.sqrt(252) : 0;
  strategyMetrics.innerHTML = rows.length
    ? `
      <div class="mini-row"><span>累计策略收益</span><strong>${formatPercent(cumulative)}</strong></div>
      <div class="mini-row"><span>Hit Rate</span><strong>${active.length ? formatPercent(wins / active.length) : "0.0%"}</strong></div>
      <div class="mini-row"><span>Sharpe</span><strong>${sharpe.toFixed(2)}</strong></div>
    `
    : '<p class="placeholder">暂无回测指标</p>';
}

function renderReturnScatter(rows) {
  if (!rows.length) {
    returnScatter.innerHTML = '<p class="placeholder">暂无散点数据</p>';
    return;
  }
  const points = rows.map((row) => {
    const x = 50 + row.score * 42;
    const y = 50 - row.returns.forward_return_5d * 900;
    return `<circle cx="${Math.max(5, Math.min(95, x)).toFixed(1)}" cy="${Math.max(5, Math.min(95, y)).toFixed(1)}" r="3" class="${row.label}"></circle>`;
  });
  returnScatter.innerHTML = `<svg viewBox="0 0 100 100" role="img" aria-label="sentiment score versus future return"><line x1="0" y1="50" x2="100" y2="50"></line><line x1="50" y1="0" x2="50" y2="100"></line>${points.join("")}</svg>`;
}

function renderTopNewsEvents(rows) {
  const topPositive = [...rows].sort((a, b) => b.score - a.score)[0];
  const topNegative = [...rows].sort((a, b) => a.score - b.score)[0];
  topNewsEvents.innerHTML = rows.length
    ? [topPositive, topNegative].filter(Boolean).map((row) => `<div class="mini-row"><span>${escapeHtml(row.event.counterparty)}</span><strong>${row.score.toFixed(2)}</strong><small>${row.label}</small></div>`).join("")
    : '<p class="placeholder">暂无新闻排行</p>';
}

function formatPercent(value) {
  return `${(value * 100).toFixed(1)}%`;
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
  const extracted = result.extractedEvents.length
    ? `<div class="event-chip-row">${result.extractedEvents.map((item) => `<span>${escapeHtml(item.event_type)}</span>`).join("")}</div>`
    : "";

  return `
    <article class="result-card severity-${result.severity}">
      <header>
        <div>
          <h4>${escapeHtml(result.event.counterparty)}</h4>
          <small>${escapeHtml(result.event.source || "unknown")} · ${escapeHtml(result.model)} · confidence ${result.confidence.toFixed(4)} · severity ${result.severity}</small>
        </div>
        <span class="score-badge ${result.label}">${result.label} ${result.score.toFixed(4)}</span>
      </header>
      <p class="result-text">${escapeHtml(result.event.text)}</p>
      <p class="explanation">${escapeHtml(result.explanation)}</p>
      ${extracted}
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

function renderLiveNews() {
  const scored = liveNewsItems.map((text, index) => analyzeEvent(normalizeEvent({ text, source: "live-news" }, index)));
  liveNewsList.innerHTML = scored
    .map(
      (result) => `<article class="news-item severity-${result.severity}">
        <div><strong>${escapeHtml(result.event.counterparty)}</strong><p>${escapeHtml(result.event.text)}</p></div>
        <span class="score-badge ${result.label}">${result.score.toFixed(2)}</span>
      </article>`,
    )
    .join("");
  newsRadar.innerHTML = scored
    .map((result) => `<div class="radar-cell ${result.label}"><span>${escapeHtml(result.event.counterparty)}</span><strong>${result.label}</strong><small>${result.confidence.toFixed(2)}</small></div>`)
    .join("");
}

function renderStockPicks(results = latestResults) {
  const baseResults = results.length ? results : liveNewsItems.map((text, index) => analyzeEvent(normalizeEvent({ text, source: "live-news" }, index)));
  const rows = stockUniverse
    .map((stock) => {
      const related = baseResults.filter((result) => result.event.counterparty.toLowerCase().includes(stock.name.toLowerCase()) || stock.name.toLowerCase().includes(result.event.counterparty.toLowerCase()));
      const score = related.length ? related.reduce((total, result) => total + result.score * result.confidence, 0) / related.length : 0;
      const riskPenalty = related.filter((result) => result.severity === "high").length * 0.35;
      return { ...stock, score: score - riskPenalty, related: related.length };
    })
    .sort((a, b) => b.score - a.score);
  stockPickList.innerHTML = rows
    .map((stock, index) => {
      const action = stock.score > 0.18 ? "关注" : stock.score < -0.18 ? "规避" : "观察";
      return `<article class="stock-card">
        <span class="rank">#${index + 1}</span>
        <div><h4>${escapeHtml(stock.ticker)} · ${escapeHtml(stock.name)}</h4><p>${escapeHtml(stock.sector)} · related news ${stock.related}</p></div>
        <strong class="action-${action}">${action}</strong>
        <small>${stock.score.toFixed(2)}</small>
      </article>`;
    })
    .join("");
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
    input.value += `${liveNewsItems[index % liveNewsItems.length]}\n\n`;
    analyzeInput();
    index += 1;
    if (index >= liveNewsItems.length) toggleSimulation();
  }, 700);
}

function goToPage(pageIndex) {
  const max = document.querySelectorAll(".page-panel").length - 1;
  currentPage = Math.max(0, Math.min(max, pageIndex));
  pageTrack.style.transform = `translateX(-${currentPage * 100}vw)`;
  pageIndicator.textContent = `${currentPage + 1} / ${max + 1}`;
  document.querySelectorAll("[data-page]").forEach((item) => {
    item.classList.toggle("active", Number(item.dataset.page) === currentPage);
  });
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
  input.value = sampleText;
}

function analyzeInput() {
  try {
    const events = parseInput(input.value);
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
clearButton.addEventListener("click", () => {
  input.value = "";
  renderResults([]);
});
simulateButton.addEventListener("click", toggleSimulation);
document.querySelector("#refresh-news").addEventListener("click", renderLiveNews);
document.querySelector("#rebalance-button").addEventListener("click", () => renderStockPicks([...latestResults].reverse()));
document.querySelector("#prev-page").addEventListener("click", () => goToPage(currentPage - 1));
document.querySelector("#next-page").addEventListener("click", () => goToPage(currentPage + 1));
document.querySelectorAll("[data-page]").forEach((item) => {
  item.addEventListener("click", (event) => {
    event.preventDefault();
    goToPage(Number(item.dataset.page));
  });
});
document.addEventListener("keydown", (event) => {
  if (event.key === "ArrowLeft") goToPage(currentPage - 1);
  if (event.key === "ArrowRight") goToPage(currentPage + 1);
});

loadSample();
analyzeInput();
renderLiveNews();
goToPage(0);
