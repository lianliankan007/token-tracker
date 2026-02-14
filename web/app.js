const state = {
  rows: [],
  visible: {
    total: false,
    input: true,
    output: true,
  },
};

const el = {
  pathList: document.getElementById("pathList"),
  candidateList: document.getElementById("candidateList"),
  status: document.getElementById("status"),
  mTotal: document.getElementById("mTotal"),
  mInput: document.getElementById("mInput"),
  mOutput: document.getElementById("mOutput"),
  mFiles: document.getElementById("mFiles"),
  tbody: document.getElementById("tbody"),
  chartSvg: document.getElementById("chartSvg"),
  chartTooltip: document.getElementById("chartTooltip"),
  showTotal: document.getElementById("showTotal"),
  showInput: document.getElementById("showInput"),
  showOutput: document.getElementById("showOutput"),
  sourceSelect: document.getElementById("sourceSelect"),
  btnAutoScan: document.getElementById("btnAutoScan"),
  btnApplyCandidates: document.getElementById("btnApplyCandidates"),
  btnAddDir: document.getElementById("btnAddDir"),
  btnAddFile: document.getElementById("btnAddFile"),
  btnRemove: document.getElementById("btnRemove"),
  btnClear: document.getElementById("btnClear"),
  btnRefresh: document.getElementById("btnRefresh"),
};

const fmt = (n) => Number(n || 0).toLocaleString("en-US");

function renderPaths(paths) {
  el.pathList.innerHTML = "";
  for (const p of paths || []) {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p;
    el.pathList.appendChild(opt);
  }
}

function renderCandidates(candidates) {
  el.candidateList.innerHTML = "";
  for (const p of candidates || []) {
    const opt = document.createElement("option");
    opt.value = p;
    opt.textContent = p;
    el.candidateList.appendChild(opt);
  }
}

function renderSummary(totals = {}) {
  el.mTotal.textContent = totals.total_fmt || fmt(totals.total);
  el.mInput.textContent = totals.input_fmt || fmt(totals.input_tokens);
  el.mOutput.textContent = totals.output_fmt || fmt(totals.output_tokens);
  el.mFiles.textContent = totals.files_fmt || fmt(totals.files_scanned);
}

function renderTable(rows) {
  el.tbody.innerHTML = "";
  for (const r of rows) {
    const tr = document.createElement("tr");
    const cells = [
      r.day,
      fmt(r.total),
      fmt(r.input_tokens),
      fmt(r.output_tokens),
      fmt(r.cached_input_tokens),
      fmt(r.reasoning_output_tokens),
      fmt(r.token_events),
    ];
    for (const c of cells) {
      const td = document.createElement("td");
      td.textContent = c;
      tr.appendChild(td);
    }
    el.tbody.appendChild(tr);
  }
}

function seriesByType(rows, type) {
  if (type === "input") return rows.map((r) => r.input_tokens);
  if (type === "output") return rows.map((r) => r.output_tokens);
  return rows.map((r) => r.total);
}

function lineColor(type) {
  if (type === "input") return "#06b6d4";
  if (type === "output") return "#0ea5e9";
  return "#2563eb";
}

function polylinePoints(series, width, height, pad, maxVal) {
  const minX = pad;
  const minY = pad;
  const maxX = width - pad;
  const maxY = height - pad;
  const n = Math.max(1, series.length - 1);

  return series.map((val, idx) => {
    const x = minX + (idx / n) * (maxX - minX);
    const y = maxY - (val / maxVal) * (maxY - minY);
    return { x, y };
  });
}

function pointsToStr(points) {
  return points.map((p) => `${p.x.toFixed(2)},${p.y.toFixed(2)}`).join(" ");
}

function lineLabel(type) {
  if (type === "input") return "上传";
  if (type === "output") return "下载";
  return "总量";
}

function lineValue(row, type) {
  if (type === "input") return row.input_tokens;
  if (type === "output") return row.output_tokens;
  return row.total;
}

function showTooltip(evt, row, type) {
  const tip = el.chartTooltip;
  tip.innerHTML = [
    `日期: ${row.day}`,
    `总量: ${fmt(row.total)}`,
    `上传: ${fmt(row.input_tokens)}`,
    `下载: ${fmt(row.output_tokens)}`,
    `当前(${lineLabel(type)}): ${fmt(lineValue(row, type))}`,
  ].join("<br>");
  tip.style.display = "block";

  const box = el.chartSvg.getBoundingClientRect();
  const x = evt.clientX - box.left + 12;
  const y = evt.clientY - box.top + 12;
  tip.style.left = `${x}px`;
  tip.style.top = `${y}px`;
}

function hideTooltip() {
  el.chartTooltip.style.display = "none";
}

function drawLine(points, color, rows, type) {
  const pointsStr = pointsToStr(points);
  const poly = document.createElementNS("http://www.w3.org/2000/svg", "polyline");
  poly.setAttribute("fill", "none");
  poly.setAttribute("stroke", color);
  poly.setAttribute("stroke-width", "2.2");
  poly.setAttribute("points", pointsStr);
  el.chartSvg.appendChild(poly);

  for (let idx = 0; idx < points.length; idx += 1) {
    const p = points[idx];
    const c = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    c.setAttribute("cx", String(p.x.toFixed(2)));
    c.setAttribute("cy", String(p.y.toFixed(2)));
    c.setAttribute("r", "3");
    c.setAttribute("fill", color);
    c.style.cursor = "pointer";
    c.addEventListener("mousemove", (evt) => showTooltip(evt, rows[idx], type));
    c.addEventListener("mouseenter", (evt) => showTooltip(evt, rows[idx], type));
    c.addEventListener("mouseleave", hideTooltip);
    el.chartSvg.appendChild(c);
  }
}

function renderChart(rows) {
  const width = 920;
  const height = 320;
  const pad = 28;

  el.chartSvg.innerHTML = "";
  hideTooltip();

  if (!rows.length) {
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.setAttribute("x", "50%");
    t.setAttribute("y", "50%");
    t.setAttribute("text-anchor", "middle");
    t.setAttribute("fill", "#64748b");
    t.textContent = "没有可显示的数据";
    el.chartSvg.appendChild(t);
    return;
  }

  const enabledTypes = ["total", "input", "output"].filter((t) => state.visible[t]);
  if (!enabledTypes.length) {
    const t = document.createElementNS("http://www.w3.org/2000/svg", "text");
    t.setAttribute("x", "50%");
    t.setAttribute("y", "50%");
    t.setAttribute("text-anchor", "middle");
    t.setAttribute("fill", "#64748b");
    t.textContent = "请至少选择一条线";
    el.chartSvg.appendChild(t);
    return;
  }

  const axis = document.createElementNS("http://www.w3.org/2000/svg", "line");
  axis.setAttribute("x1", String(pad));
  axis.setAttribute("y1", String(height - pad));
  axis.setAttribute("x2", String(width - pad));
  axis.setAttribute("y2", String(height - pad));
  axis.setAttribute("stroke", "#94a3b8");
  axis.setAttribute("stroke-width", "1");
  el.chartSvg.appendChild(axis);

  const allVisibleValues = enabledTypes.flatMap((t) => seriesByType(rows, t));
  const maxVal = Math.max(1, ...allVisibleValues);

  for (const type of enabledTypes) {
    const points = polylinePoints(seriesByType(rows, type), width, height, pad, maxVal);
    drawLine(points, lineColor(type), rows, type);
  }
}

function renderPayload(payload) {
  if (!payload) return;
  if (payload.error) {
    el.status.textContent = `错误: ${payload.error}`;
    return;
  }

  state.rows = payload.rows || [];
  if (payload.source) {
    el.sourceSelect.value = payload.source;
  }
  renderCandidates(payload.candidates || []);
  renderPaths(payload.paths || []);
  renderSummary(payload.totals || {});
  renderTable(state.rows);
  renderChart(state.rows);
  el.status.textContent = payload.status || "完成";
}

async function callApi(fn, ...args) {
  if (!window.pywebview || !window.pywebview.api || !window.pywebview.api[fn]) {
    throw new Error("pywebview API 未就绪");
  }
  return window.pywebview.api[fn](...args);
}

function syncVisibleFromUI() {
  state.visible.total = el.showTotal.checked;
  state.visible.input = el.showInput.checked;
  state.visible.output = el.showOutput.checked;
}

async function onReady() {
  syncVisibleFromUI();
  const init = await callApi("initialize");
  renderPayload(init);

  el.btnAddDir.addEventListener("click", async () => {
    const res = await callApi("add_directory");
    if (res.ok) renderPaths(res.paths);
  });

  el.btnAddFile.addEventListener("click", async () => {
    const res = await callApi("add_files");
    if (res.ok) renderPaths(res.paths);
  });

  el.btnRemove.addEventListener("click", async () => {
    const selected = [...el.pathList.selectedOptions].map((o) => o.value);
    if (!selected.length) return;
    const res = await callApi("remove_paths", selected);
    if (res.ok) renderPaths(res.paths);
  });

  el.btnClear.addEventListener("click", async () => {
    const res = await callApi("clear_paths");
    if (res.ok) renderPaths(res.paths);
  });

  el.btnRefresh.addEventListener("click", async () => {
    el.status.textContent = "正在解析日志...";
    const res = await callApi("refresh_data");
    renderPayload(res);
  });

  el.sourceSelect.addEventListener("change", async () => {
    const res = await callApi("set_source", el.sourceSelect.value);
    if (!res.ok) {
      el.status.textContent = res.message || "来源设置失败";
      return;
    }
    el.status.textContent = "已切换来源";
  });

  el.btnAutoScan.addEventListener("click", async () => {
    el.status.textContent = "正在自动扫描日志路径...";
    const res = await callApi("auto_scan_candidates", el.sourceSelect.value);
    if (!res.ok) {
      el.status.textContent = res.message || "自动扫描失败";
      return;
    }
    if (res.source) {
      el.sourceSelect.value = res.source;
    }
    renderCandidates(res.candidates || []);
    el.status.textContent = res.message || "自动扫描完成";
  });

  el.btnApplyCandidates.addEventListener("click", async () => {
    const selected = [...el.candidateList.selectedOptions].map((o) => o.value);
    const res = await callApi("apply_auto_scan_selection", selected);
    if (!res.ok) {
      el.status.textContent = res.message || "加入目录失败";
      return;
    }
    renderPaths(res.paths || []);
    el.status.textContent = res.message || "已加入目录";
  });

  for (const id of ["showTotal", "showInput", "showOutput"]) {
    el[id].addEventListener("change", () => {
      syncVisibleFromUI();
      renderChart(state.rows);
    });
  }

  el.chartSvg.addEventListener("mouseleave", hideTooltip);
}

window.addEventListener("pywebviewready", onReady);
