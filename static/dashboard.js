async function loadChart() {
  try {
    const res = await fetch("/api/metrics/Squat");
    if (!res.ok) return;

    const data = await res.json();
    const labels = data.points.map(p => p.iso_week);
    const values = data.points.map(p => p.best_e1rm);
    const forecastLabels = data.forecast.map((_, i) => `+${i + 1}w`);

    const ctx = document.getElementById("squatChart").getContext("2d");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: labels.concat(forecastLabels),
        datasets: [
          {
            label: "Best e1RM",
            data: values,
            borderColor: "#2196f3",
            backgroundColor: "rgba(33, 150, 243, 0.1)",
            borderWidth: 2,
            tension: 0.2
          },
          {
            label: "Forecast",
            data: new Array(values.length).fill(null).concat(data.forecast),
            borderColor: "#e91e63",
            borderDash: [6, 4],
            borderWidth: 2,
            tension: 0.2
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            position: "bottom" // 👈 moves the legend under the chart
          }
        },
        layout: {
          padding: 10
        },
        scales: {
          y: {
            beginAtZero: false
          }
        }
      }
    });
  } catch (e) {
    console.error("chart error", e);
  }
}

document.addEventListener("DOMContentLoaded", loadChart);
