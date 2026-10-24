# -*- coding: utf-8 -*-
import io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def patch(path, replacements):
    s = open(path, encoding='utf-8').read()
    for old, new, tag in replacements:
        if old not in s:
            raise SystemExit(f"ANCHOR FAILED [{tag}] in {path}")
        if s.count(old) != 1:
            raise SystemExit(f"ANCHOR NOT UNIQUE [{tag}] x{s.count(old)} in {path}")
        s = s.replace(old, new)
    open(path, 'w', encoding='utf-8', newline='\n').write(s)
    print(f"patched {path}: {len(replacements)} edits")

# ============ index.html ============
patch('web/index.html', [
    ("""              <div class="toolbar-field">
                <label for="end">结束</label>
                <input id="end" type="datetime-local" />
              </div>""",
     """              <div class="toolbar-field">
                <label for="end">结束</label>
                <input id="end" type="datetime-local" />
              </div>
              <div class="toolbar-field">
                <label for="granularity">粒度</label>
                <select id="granularity">
                  <option value="auto">自动</option>
                  <option value="60000">1 分钟</option>
                  <option value="300000">5 分钟</option>
                  <option value="3600000">1 小时</option>
                  <option value="86400000">1 天</option>
                </select>
              </div>""", "granularity-field"),
])

# ============ app.js ============
patch('web/app.js', [
    ('const MODE_STORAGE_KEY = "traffic-monitor:display-mode"',
     'const MODE_STORAGE_KEY = "traffic-monitor:display-mode"\nconst GRANULARITY_STORAGE_KEY = "traffic-monitor:granularity"', "const"),
    ('  trendAxis: document.getElementById("trendAxis"),',
     '  trendAxis: document.getElementById("trendAxis"),\n  granularity: document.getElementById("granularity"),', "elements"),
    ('  trendHoverIndex: -1,',
     '  trendHoverIndex: -1,\n  trendSelectedIndex: -1,\n  trendFilter: null,\n  trendBucketMs: 3600000,', "state"),
    ("""function bucketSize(start, end) {
  const range = end - start
  let size = 60000
  if (range <= 3600000) size = 60000
  else if (range <= 86400000) size = 300000
  else if (range <= 604800000) size = 3600000
  else size = 86400000
  return state.mode === "summary" ? Math.max(86400000, size) : size
}""",
     """function bucketSize(start, end) {
  const range = end - start
  let size = 60000
  const manual = elements.granularity && elements.granularity.value !== "auto"
    ? Number(elements.granularity.value)
    : 0
  if (Number.isFinite(manual) && manual > 0) {
    size = manual
  } else {
    if (range <= 3600000) size = 60000
    else if (range <= 86400000) size = 3600000
    else size = 86400000
  }
  return state.mode === "summary" ? Math.max(86400000, size) : size
}""", "bucketSize"),
    ("function nowLocalInputValue(offsetMs) {",
     """function loadStoredGranularity() {
  try {
    return window.localStorage.getItem(GRANULARITY_STORAGE_KEY)
  } catch (error) {
    console.warn("Failed to load stored granularity", error)
    return null
  }
}

function persistSelectedGranularity(value) {
  try {
    window.localStorage.setItem(GRANULARITY_STORAGE_KEY, value)
  } catch (error) {
    console.warn("Failed to persist selected granularity", error)
  }
}

function effectiveRange() {
  if (state.trendFilter) {
    const { start, end } = getTimeRange()
    return {
      start: Math.max(state.trendFilter.start, start),
      end: Math.min(state.trendFilter.end, end),
    }
  }
  return getTimeRange()
}

function resetTrendFilter() {
  state.trendFilter = null
  state.trendSelectedIndex = -1
  syncTrendFilterBadge()
}

function clearTrendFilterAndReload() {
  if (!state.trendFilter) return
  resetTrendFilter()
  renderTrend(state.lastTrendPoints)
  loadTablesOnly()
}

function syncTrendFilterBadge() {
  const existing = document.getElementById("trendFilterBadge")
  if (!state.trendFilter) {
    if (existing) existing.remove()
    return
  }
  let badge = existing
  if (!badge) {
    badge = document.createElement("button")
    badge.id = "trendFilterBadge"
    badge.type = "button"
    badge.className = "toolbar-action trend-filter-badge"
    badge.title = "点击取消走势图时间筛选"
    badge.addEventListener("click", clearTrendFilterAndReload)
    elements.refreshBtn.parentElement.insertBefore(badge, elements.refreshBtn)
  }
  badge.textContent = `已筛选 ${formatDateTime(state.trendFilter.start)} ~ ${formatDateTime(state.trendFilter.end)} ✕`
}

function nowLocalInputValue(offsetMs) {""", "helpers"),
    ("""async function loadSecondaryRows(primaryLabel) {
  const { start, end } = getTimeRange()
  const dimension = elements.dimension.value""",
     """async function loadSecondaryRows(primaryLabel) {
  const { start, end } = effectiveRange()
  const dimension = elements.dimension.value""", "secondary-range"),
    ("""async function loadDetails(primaryLabel, secondaryLabel) {
  const { start, end } = getTimeRange()
  const seq = ++state.detailSeq""",
     """async function loadDetails(primaryLabel, secondaryLabel) {
  const { start, end } = effectiveRange()
  const seq = ++state.detailSeq""", "details-range"),
    ("""  try {
    resetDetailPanels()

    const [rows, trend] = await Promise.all([
      fetchJSON("/api/traffic/aggregate", {
        dimension: elements.dimension.value,
        start,
        end,
        summary,
      }),
      fetchJSON("/api/traffic/trend", {
        start,
        end,
        bucket: bucketSize(start, end),
        summary,
      }),
    ])

    if (seq !== state.loadSeq) return

    state.primaryRows = rows
    state.selectedPrimary = rows[0]?.label || null

    renderCards(rows)
    renderPrimaryTable(rows)
    renderTrend(trend)
    updateViewHints()

    if (state.selectedPrimary) {
      await loadSecondaryRows(state.selectedPrimary)
      renderPrimaryTable(state.primaryRows)
    }

    setStatus("")
  } catch (error) {""",
     """  try {
    resetDetailPanels()
    syncTrendFilterBadge()

    const trend = await fetchJSON("/api/traffic/trend", {
      start,
      end,
      bucket: bucketSize(start, end),
      summary,
    })

    if (seq !== state.loadSeq) return

    state.trendBucketMs = bucketSize(start, end)
    renderTrend(trend)
    await loadTablesOnly()

    setStatus("")
  } catch (error) {""", "loadData-refactor"),
    ("async function loadData() {",
     """async function loadTablesOnly() {
  const seq = ++state.loadSeq
  const summary = state.mode === "summary" ? "1" : ""
  const { start, end } = effectiveRange()

  const rows = await fetchJSON("/api/traffic/aggregate", {
    dimension: elements.dimension.value,
    start,
    end,
    summary,
  })

  if (seq !== state.loadSeq) return

  state.primaryRows = rows
  state.selectedPrimary = rows[0]?.label || null

  renderCards(rows)
  renderPrimaryTable(rows)
  updateViewHints()

  if (state.selectedPrimary) {
    await loadSecondaryRows(state.selectedPrimary)
    renderPrimaryTable(state.primaryRows)
  }
}

async function loadData() {""", "loadTablesOnly"),
    ("""elements.range.addEventListener("change", () => {
  if (Number(elements.range.value) !== -1) updateCustomInputs()
  persistSelectedRange(elements.range.value)
  syncContextSummary()
  loadData()
})""",
     """elements.range.addEventListener("change", () => {
  if (Number(elements.range.value) !== -1) updateCustomInputs()
  persistSelectedRange(elements.range.value)
  resetTrendFilter()
  syncContextSummary()
  loadData()
})

elements.granularity.addEventListener("change", () => {
  persistSelectedGranularity(elements.granularity.value)
  resetTrendFilter()
  loadData()
})""", "range-granularity-listeners"),
    ("""elements.start.addEventListener("change", () => {
  elements.range.value = "-1"
  syncContextSummary()
  loadData()
})""",
     """elements.start.addEventListener("change", () => {
  elements.range.value = "-1"
  resetTrendFilter()
  syncContextSummary()
  loadData()
})""", "start-listener"),
    ("""elements.end.addEventListener("change", () => {
  elements.range.value = "-1"
  syncContextSummary()
  loadData()
})""",
     """elements.end.addEventListener("change", () => {
  elements.range.value = "-1"
  resetTrendFilter()
  syncContextSummary()
  loadData()
})""", "end-listener"),
    ("""    elements.dimension.value = nextDimension
    persistSelectedDimension(nextDimension)
    updateViewHints()
    loadData()""",
     """    elements.dimension.value = nextDimension
    persistSelectedDimension(nextDimension)
    resetTrendFilter()
    updateViewHints()
    loadData()""", "dimension-listener"),
    ("""elements.trendCanvas.addEventListener("mousemove", showTrendTooltip)
elements.trendCanvas.addEventListener("mouseleave", hideTrendTooltip)""",
     """elements.trendCanvas.addEventListener("mousemove", showTrendTooltip)
elements.trendCanvas.addEventListener("mouseleave", hideTrendTooltip)

elements.trendCanvas.addEventListener("click", (event) => {
  if (!state.trendPlotPoints.length) return

  const rect = elements.trendCanvas.getBoundingClientRect()
  const pointerX = event.clientX - rect.left
  let nearestIndex = 0
  let nearestDistance = Number.POSITIVE_INFINITY
  state.trendPlotPoints.forEach((plotPoint, index) => {
    const distance = Math.abs(plotPoint.x - pointerX)
    if (distance < nearestDistance) {
      nearestDistance = distance
      nearestIndex = index
    }
  })

  const spacing = state.trendPlotPoints.length > 1
    ? Math.abs(state.trendPlotPoints[1].x - state.trendPlotPoints[0].x)
    : 40
  const threshold = Math.max(14, Math.min(spacing / 2, 48))

  if (nearestDistance <= threshold) {
    const point = state.trendPlotPoints[nearestIndex].point
    const bucket = state.trendBucketMs || 3600000
    const { end } = getTimeRange()
    const fStart = point.timestamp
    const fEnd = Math.min(fStart + bucket, end)
    if (state.trendFilter && state.trendFilter.start === fStart && state.trendFilter.end === fEnd) {
      clearTrendFilterAndReload()
      return
    }
    state.trendFilter = { start: fStart, end: fEnd }
    state.trendSelectedIndex = nearestIndex
  } else {
    if (!state.trendFilter) return
    clearTrendFilterAndReload()
    return
  }

  renderTrend(state.lastTrendPoints)
  syncTrendFilterBadge()
  loadTablesOnly()
})""", "canvas-click"),
    ("""  if (state.trendHoverIndex >= 0 && state.trendHoverIndex < state.trendPlotPoints.length) {""",
     """  if (state.trendSelectedIndex >= 0 && state.trendSelectedIndex < state.trendPlotPoints.length) {
    const sel = state.trendPlotPoints[state.trendSelectedIndex]
    const halfBand = Math.max(6, Math.min(16, (right - left) / Math.max(state.trendPlotPoints.length, 1) / 2))
    ctx.fillStyle = "rgba(95, 70, 255, 0.10)"
    ctx.fillRect(sel.x - halfBand, top, halfBand * 2, bottom - top)
    ctx.strokeStyle = "rgba(95, 70, 255, 0.9)"
    ctx.lineWidth = 1.5
    ctx.beginPath()
    ctx.moveTo(sel.x, top)
    ctx.lineTo(sel.x, bottom)
    ctx.stroke()
  }

  if (state.trendHoverIndex >= 0 && state.trendHoverIndex < state.trendPlotPoints.length) {""", "selected-highlight"),
    ("""  syncModeUI()
  updateCustomInputs()""",
     """  const storedGranularity = loadStoredGranularity()
  if (storedGranularity && elements.granularity) {
    const option = Array.from(elements.granularity.options).find((item) => item.value === storedGranularity)
    if (option) elements.granularity.value = storedGranularity
  }
  syncModeUI()
  updateCustomInputs()""", "init-granularity"),
])

with open('web/styles.css', 'a', encoding='utf-8', newline='\n') as f:
    f.write("""
/* ===== 走势图点击联动筛选（本地增强） ===== */
#trendCanvas { cursor: pointer; }
.toolbar-action.trend-filter-badge {
  background: #5f46ff;
  border: 1px solid #5f46ff;
  color: #fff;
  font-weight: 600;
}
.toolbar-action.trend-filter-badge:hover { opacity: 0.85; }
""")
print("patched web/styles.css (appended)")
print("ALL PATCHES OK")
