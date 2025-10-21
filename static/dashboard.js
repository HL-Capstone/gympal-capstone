(function () {
  const selectEl = document.getElementById("exerciseSelect");
  const canvasEl = document.getElementById("e1rmChart");
  const emptyEl  = document.getElementById("emptyState");

  let chart;

  // Read CSS variables from :root so colors match your theme
  function cssVar(name, fallback) {
    const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    return v || fallback;
  }
  const COLOR_PRIMARY = cssVar("--gp-primary", "#2563eb");
  const COLOR_ACCENT  = cssVar("--gp-accent",  "#22c55e");

  async function loadExercise(name) {
    // Show a simple loading state
    if (emptyEl) {
      emptyEl.textContent = `Loading "${name}"…`;
      emptyEl.style.display = "block";
    }

    const url = `/api/metrics/${encodeURIComponent(name)}`;
    let data;
    try {
      const res = await fetch(url, { headers: { "Accept": "application/json" } });
      data = await res.json();
      if (!res.ok || !data.points) {
        showEmpty(`No data for "${name}". Log a workout to see your chart.`);
        render([], []);
        return;
      }
    } catch (e) {
      showEmpty("Could not load data. Please try again.");
      render([], []);
      return;
    }

    // Hide empty-state once we have data
    if (emptyEl) emptyEl.style.display = "none";

    let labels = data.points.map(p => p.iso_week); // use let so we can extend later
    const values = data.points.map(p => p.best_e1rm);
    const forecast = data.forecast || [];

    render(labels, values, forecast);
  }

  function showEmpty(msg) {
    if (!emptyEl) return;
    emptyEl.textContent = msg || emptyEl.textContent;
    emptyEl.style.display = "block";
  }

  function render(labels, values, forecast = []) {
    if (!canvasEl) return;
    const ctx = canvasEl.getContext("2d");

    if (chart) {
      chart.destroy();
    }

    const datasets = [
      {
        label: "Weekly Best e1RM",
        data: values,
        tension: 0.2,
        borderWidth: 2,
        pointRadius: 3,
        borderColor: COLOR_PRIMARY,
        backgroundColor: COLOR_PRIMARY
      }
    ];

    if (forecast.length > 0) {
      const lastIndex = labels.length - 1;
      const forecastLabels = forecast.map((_, i) => `+${i + 1}`);
      datasets.push({
        label: "Forecast (next 4)",
        data: Array(labels.length - 1).fill(null).concat([values[lastIndex], ...forecast]),
        borderDash: [6, 6],
        borderWidth: 2,
        pointRadius: 0,
        borderColor: COLOR_ACCENT,
        backgroundColor: COLOR_ACCENT
      });
      labels = labels.concat(forecastLabels);
    }

    chart = new Chart(ctx, {
      type: "line",
      data: { labels, datasets },
      options: {
        maintainAspectRatio: false,
        responsive: true,
        scales: {
          y: { title: { display: true, text: "e1RM" } },
          x: { title: { display: true, text: "ISO Week" } }
        },
        plugins: {
          legend: { display: true },
          tooltip: { mode: "index", intersect: false }
        }
      }
    });
  }

  // initial load for the default selected exercise
  if (selectEl) {
    loadExercise(selectEl.value);
    selectEl.addEventListener("change", () => loadExercise(selectEl.value));
  }
})();
