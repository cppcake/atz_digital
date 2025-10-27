console.log("stats.js loaded");

function getColorHex(color) {
    // Map color names to hex codes
    const map = {
        green: "#00AE42",
        yellow: "#FEC600",
        red: "#DE4343",
        blue: "#00B1B7",
        purple: "#950051",
        none: "#cccccc" // grey for no vote
    };
    return map[color] || "#cccccc";
}

function aggregateVotes(topic, sessions) {
    // Returns: [{ color: voteCount, ... } for each statement
    const answers = topic.answers || [];
    const statements = topic.statements || [];
    const colorKeys = answers.map(a => a.color);
    const result = [];
    for (let sIdx = 0; sIdx < statements.length; sIdx++) {
        const voteCounts = {};
        colorKeys.forEach(c => voteCounts[c] = 0);
        // Do NOT count "none"
        sessions.forEach(session => {
            (session.players || []).forEach(player => {
                const vote = (player.answers && player.answers[sIdx]) || null;
                // Only count valid votes
                if (vote && vote !== "None" && voteCounts.hasOwnProperty(vote)) {
                    voteCounts[vote]++;
                }
            });
        });
        result.push(voteCounts);
    }
    return result;
}

function renderStatementCharts(topic, sessions) {
    // Ensure answers are sorted in the correct order
    const colorOrder = ["green", "yellow", "red", "blue", "purple"];
    const answers = (topic.answers || []).slice().sort(
        (a, b) => colorOrder.indexOf(a.color) - colorOrder.indexOf(b.color)
    );
    const statements = topic.statements || [];
    const voteAggregates = aggregateVotes(topic, sessions);

    statements.forEach((statement, idx) => {
        const voteCounts = voteAggregates[idx];
        const labels = [];
        const data = [];
        const bgColors = [];
        answers.forEach(a => {
            if (a.content && voteCounts[a.color] !== undefined && voteCounts[a.color] > 0) {
                labels.push(a.content);
                data.push(voteCounts[a.color]);
                bgColors.push(getColorHex(a.color));
            }
        });

        const chartId = "chart-statement-" + idx;
        const msgId = "no-data-msg-" + idx;
        const chartContainer = document.getElementById("chart-container-" + idx);
        const ctx = document.getElementById(chartId);
        const msg = document.getElementById(msgId);

        if (data.length === 0) {
            // No data for this statement
            if (ctx) ctx.style.display = "none";
            if (msg) msg.style.display = "inline";
        } else {
            // Data available, show chart
            if (msg) msg.style.display = "none";
            if (ctx) {
                ctx.style.display = "block";
                if (ctx.chartInstance) {
                    ctx.chartInstance.destroy();
                }
                ctx.chartInstance = new Chart(ctx, {
                    type: "pie",
                    data: {
                        labels: labels,
                        datasets: [{
                            data: data,
                            backgroundColor: bgColors,
                        }]
                    },
                    options: {
                        responsive: false,
                        plugins: {
                            legend: {
                                display: false,
                                position: 'top',
                                align: 'start',
                            }
                        }
                    }
                });
            }
        }
    });
}

window.addEventListener("DOMContentLoaded", function () {
    // topic and sessions are provided by stats.html
    renderStatementCharts(window.topic, window.sessions);
});

window.addEventListener("DOMContentLoaded", function () {
    // topic and sessions are provided by stats.html
    renderStatementCharts(window.topic, window.sessions);
});

