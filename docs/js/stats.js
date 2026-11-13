(function () {
  var COLOR = "#5865f2";
  var metric = "users";
  var days = 0;
  var data = null;
  var chart = null;

  try { metric = localStorage.getItem("statsMetric") || metric; } catch (e) {}

  var errorEl = document.getElementById("stats-error");
  var updatedEl = document.getElementById("stats-updated");

  function showError() {
    errorEl.classList.remove("hidden");
    errorEl.classList.add("flex");
  }

  function points() {
    var idx = data.fields.indexOf(metric);
    var cutoff = days ? Date.now() - days * 86400000 : 0;
    return data.rows
      .map(function (r) { return { x: Date.parse(r[0]), y: r[idx + 1] }; })
      .filter(function (p) { return p.x >= cutoff; });
  }

  function fmtDate(ms) {
    return new Date(ms).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  }

  function render() {
    document.querySelectorAll(".stat-pill").forEach(function (b) {
      b.setAttribute("aria-pressed", String(b.dataset.metric === metric));
    });
    document.querySelectorAll(".range-btn").forEach(function (b) {
      b.setAttribute("aria-pressed", String(Number(b.dataset.days) === days));
    });
    var pts = points();
    var xMin = pts.length ? pts[0].x : undefined;
    var xMax = pts.length ? pts[pts.length - 1].x : undefined;
    if (!chart) {
      chart = new Chart(document.getElementById("stats-chart"), {
        type: "line",
        data: { datasets: [{ data: pts, borderColor: COLOR, backgroundColor: "rgba(88,101,242,0.15)", fill: true, pointRadius: 0, tension: 0.2, borderWidth: 2 }] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          animation: false,
          parsing: false,
          interaction: { mode: "nearest", axis: "x", intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { title: function (items) { return new Date(items[0].parsed.x).toLocaleString(); } } }
          },
          scales: {
            x: { type: "linear", bounds: "data", min: xMin, max: xMax, ticks: { color: "#949ba4", maxTicksLimit: 8, callback: function (v) { return fmtDate(v); } }, grid: { color: "rgba(255,255,255,0.06)" } },
            y: { beginAtZero: true, ticks: { color: "#949ba4", precision: 0 }, grid: { color: "rgba(255,255,255,0.06)" } }
          }
        }
      });
    } else {
      chart.data.datasets[0].data = pts;
      chart.options.scales.x.min = xMin;
      chart.options.scales.x.max = xMax;
      chart.update();
    }
  }

  fetch("stats-history.json", { cache: "no-cache" })
    .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then(function (json) {
      data = json;
      if (!data.rows.length) { showError(); return; }
      var last = data.rows[data.rows.length - 1];
      document.querySelectorAll(".stat-pill").forEach(function (b) {
        var i = data.fields.indexOf(b.dataset.metric);
        b.querySelector("[data-value]").textContent = Number(last[i + 1]).toLocaleString();
      });
      var sum = data.summary || {};
      document.querySelectorAll(".stat-pill").forEach(function (b) {
        var avg = sum.avg_24h && sum.avg_24h[b.dataset.metric];
        b.querySelector("[data-avg]").textContent = avg == null ? "--" : Math.round(avg).toLocaleString();
      });
      document.querySelectorAll("[data-peak]").forEach(function (el) {
        var pk = sum.peak && sum.peak[el.dataset.peak];
        if (!pk) return;
        el.querySelector("[data-peak-value]").textContent = Number(pk.value).toLocaleString();
        el.querySelector("[data-peak-date]").textContent = new Date(pk.at).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" });
      });
      if (data.fields.indexOf(metric) < 0) metric = "users";
      if (updatedEl && data.generatedAt) {
        updatedEl.textContent = "Last updated: " + data.generatedAt.replace("T", " ").slice(0, 16) + " UTC";
      }
      render();
    })
    .catch(showError);

  document.getElementById("stats-metrics").addEventListener("click", function (e) {
    var b = e.target.closest(".stat-pill");
    if (!b || !data) return;
    metric = b.dataset.metric;
    try { localStorage.setItem("statsMetric", metric); } catch (err) {}
    render();
  });
  document.getElementById("stats-ranges").addEventListener("click", function (e) {
    var b = e.target.closest(".range-btn");
    if (!b || !data) return;
    days = Number(b.dataset.days);
    render();
  });
})();
