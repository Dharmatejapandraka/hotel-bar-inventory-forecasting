const state = { data: null, trendChart: null, weekdayChart: null };

const $ = (id) => document.getElementById(id);
const fmt = (value, digits = 0) => {
    if (value === null || value === undefined || Number.isNaN(Number(value))) return "—";
    return Number(value).toLocaleString(undefined, { maximumFractionDigits: digits });
};

function showStatus(message, type = "success") {
    const el = $("status");
    el.textContent = message;
    el.className = `status ${type}`;
}

function renderCards(cards) {
    $("rows").textContent = fmt(cards.rows);
    $("totalConsumed").textContent = `${fmt(cards.total_consumed)} ml`;
    $("avgDaily").textContent = `${fmt(cards.avg_daily_consumption)} ml`;
    $("stockouts").textContent = fmt(cards.stockout_rows);
    $("items").textContent = fmt(cards.bar_brand_count);
}

function renderTrend(records, title = "Consumed (ml)") {

    console.log("Rendering trend records:", records);

    const labels = records.map(r =>
        new Date(r.Date).toLocaleDateString()
    );

    const values = records.map(r =>
        Number(r["Consumed (ml)"]) || 0
    );

    const canvas = $("trendChart");
    const ctx = canvas.getContext("2d");

    // Destroy old chart
    if (state.trendChart) {
        state.trendChart.destroy();
        state.trendChart = null;
    }

    state.trendChart = new Chart(ctx, {
        type: "line",

        data: {
            labels: labels,

            datasets: [{
                label: title,
                data: values,
                borderWidth: 2,
                tension: 0.25,
                fill: true
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,

            animation: {
                duration: 300
            },

            plugins: {
                legend: {
                    labels: {
                        color: "#eef3ff"
                    }
                }
            },

            scales: {
                x: {
                    ticks: {
                        color: "#9ca8c7"
                    },
                    grid: {
                        color: "#293655"
                    }
                },

                y: {
                    beginAtZero: true,

                    ticks: {
                        color: "#9ca8c7"
                    },

                    grid: {
                        color: "#293655"
                    }
                }
            }
        }
    });
}

function renderWeekday(values) {
    const labels = Object.keys(values);
    const data = Object.values(values);
    const ctx = $("weekdayChart").getContext("2d");
    if (state.weekdayChart) state.weekdayChart.destroy();
    state.weekdayChart = new Chart(ctx, {
        type: "bar",
        data: { labels, datasets: [{ label: "Average consumption (ml)", data, borderWidth: 1 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#eef3ff" } } }, scales: { x: { ticks: { color: "#9ca8c7" }, grid: { display: false } }, y: { ticks: { color: "#9ca8c7" }, grid: { color: "#293655" } } } }
    });
}

function renderABC(rows) {
    $("abcList").innerHTML = rows.map(row => `
        <div class="abc-row">
            <div><strong>${row["Bar Name"]} / ${row["Brand Name"]}</strong><div class="abc-meta">${fmt(row["Consumed (ml)"])} ml · ${(Number(row.share) * 100).toFixed(1)}% share · ${(Number(row.cumulative_share) * 100).toFixed(1)}% cumulative</div></div>
            <span class="badge ${String(row["ABC Class"]).toLowerCase()}">${row["ABC Class"]}</span>
        </div>`).join("");
}

function renderModels(rows) {
    $("modelTable").innerHTML = rows.map(r => `
        <tr><td>${r["Bar Name"]}</td><td>${r["Brand Name"]}</td><td>${r.model}</td><td>${fmt(r.MAE, 2)}</td><td>${fmt(r.RMSE, 2)}</td><td>${(Number(r.WAPE) * 100).toFixed(2)}%</td></tr>
    `).join("");
}

function renderRecommendations(rows) {
    $("recommendationTable").innerHTML = rows.map(r => `
        <tr><td>${r["Bar Name"]}</td><td>${r["Brand Name"]}</td><td><span class="badge ${String(r["ABC Class"]).toLowerCase()}">${r["ABC Class"]}</span></td><td>${fmt(r["Forecast Daily Demand"])}</td><td>${fmt(r["Safety Stock"])}</td><td><strong>${fmt(r["Par Level"])}</strong></td><td>${fmt(r["Stockout Days"])}</td><td>${fmt(r["Turnover Ratio"], 2)}</td></tr>
    `).join("");
}

function populateFilter(data) {
    const select = $("trendFilter");
    const existing = new Set([...select.options].map(o => o.value));
    data.recommendations.forEach(r => {
        const key = `${r["Bar Name"]}|||${r["Brand Name"]}`;
        if (!existing.has(key)) {
            const option = document.createElement("option");
            option.value = key;
            option.textContent = `${r["Bar Name"]} / ${r["Brand Name"]}`;
            select.appendChild(option);
        }
    });
}

async function loadDashboard() {
    const response = await fetch("/api/dashboard");
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Unable to load dashboard.");
    state.data = data;
    renderCards(data.cards);
    renderTrend(data.trend);
    renderWeekday(data.weekday);
    renderABC(data.abc);
    renderModels(data.models);
    renderRecommendations(data.recommendations);
    populateFilter(data);
}

async function runDemo() {
    showStatus("Generating demo data and running the full analysis…");
    const response = await fetch("/api/run-demo", { method: "POST" });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Demo run failed.");
    await loadDashboard();
    showStatus(data.message, "success");
}

async function uploadCSV(file) {
    const form = new FormData();
    form.append("file", file);
    showStatus("Uploading CSV and running analysis…");
    const response = await fetch("/api/upload", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "Upload failed.");
    await loadDashboard();
    showStatus(data.message, "success");
}

$("demoBtn").addEventListener("click", async () => {
    try { await runDemo(); } catch (error) { showStatus(error.message, "error"); }
});

$("csvInput").addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;
    try { await uploadCSV(file); } catch (error) { showStatus(error.message, "error"); }
    event.target.value = "";
});

$("trendFilter").addEventListener("change", async (event) => {

    const value = event.target.value;

    console.log("Selected filter:", value);

    if (value === "all") {
        renderTrend(
            state.data.trend,
            "All Bars & Brands - Consumed (ml)"
        );
        return;
    }

    const parts = value.split("|||");

    const bar = parts[0];
    const brand = parts[1];

    console.log("Selected Bar:", bar);
    console.log("Selected Brand:", brand);

    try {

        const url =
            `/api/trend?bar=${encodeURIComponent(bar)}&brand=${encodeURIComponent(brand)}`;

        console.log("Request URL:", url);

        const response = await fetch(
            url + `&_=${Date.now()}`,
            {
                cache: "no-store"
            }
        );

        if (!response.ok) {
            throw new Error("Failed to load trend data.");
        }

        const records = await response.json();

        console.log("Filtered records:", records);

        renderTrend(
            records,
            `${bar} / ${brand} - Consumed (ml)`
        );

    } catch (error) {

        console.error(error);

        showStatus(
            "Unable to load the selected trend.",
            "error"
        );
    }
});

window.addEventListener("DOMContentLoaded", async () => {
    try {
        await loadDashboard();
        showStatus("Dashboard loaded successfully.", "success");
    } catch (error) {
        showStatus("No dataset found. Click 'Run Demo Dataset' to create one, or upload your CSV.", "error");
    }
});
