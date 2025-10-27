console.log("details_content.js loaded");

function fillTopic(session) {
    const colors = ["green", "yellow", "red", "blue", "purple"];
    const olAnswers = document.getElementById("ol_answers");
    const answerLis = olAnswers.querySelectorAll("li");
    colors.forEach((color, idx) => {
        const span = document.getElementById(color);
        const ans = (session.topic.answers || []).find((a) => a.color === color);
        if (span) {
            span.textContent = ans ? ans.content : "";
        }
        if (answerLis[idx]) {
            const prevImg = answerLis[idx].querySelector("img.answer-icon-img");
            if (prevImg) prevImg.remove();
            if (ans && ans.icon) {
                const img = document.createElement("img");
                img.src = `/web/imgs/answers/${ans.icon}.png`;
                img.alt = ans.icon;
                img.className = "answer-icon-img";
                img.style.height = "32px";
                img.style.width = "32px";
                img.style.objectFit = "contain";
                img.style.aspectRatio = "1 / 1";
                img.style.marginLeft = "8px";
                const colorCircle = answerLis[idx].querySelector(".color-circle");
                if (colorCircle) {
                    colorCircle.insertAdjacentElement("afterend", img);
                }
            }
        }
        if (answerLis[idx]) {
            if (!ans || !ans.content) {
                answerLis[idx].style.display = "none";
            } else {
                answerLis[idx].style.display = "";
            }
        }
    });
}

function getColorHex(color) {
    const map = {
        green: "#00AE42",
        yellow: "#FEC600",
        red: "#DE4343",
        blue: "#00B1B7",
        purple: "#950051",
        none: "#cccccc"
    };
    return map[color] || "#cccccc";
}

function getPlayerTimeStr(player, statementIdx) {
    if (
        player &&
        Array.isArray(player.answer_times) &&
        typeof player.answer_times[statementIdx] === "number"
    ) {
        const t = player.answer_times[statementIdx];
        if (t > 0) {
            return ` <span class="player-answer-time">(${t.toFixed(1)}s)</span>`;
        }
    }
    return "";
}

function renderStatementCharts(session) {
    if (!session.topic || !session.topic.statements) return;
    const statements = session.topic.statements;
    const answers = session.topic.answers || [];
    const players = session.players || [];
    statements.forEach((statement, idx) => {
        const voteCounts = {};
        answers.forEach(a => voteCounts[a.color] = 0);
        voteCounts["none"] = 0;
        players.forEach(player => {
            const vote = (player.answers && player.answers[idx]) || null;
            if (!vote || vote === "None") {
                voteCounts["none"]++;
            } else if (voteCounts.hasOwnProperty(vote)) {
                voteCounts[vote]++;
            }
        });
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
        if (voteCounts["none"] > 0) {
            labels.push("Keine Antwort");
            data.push(voteCounts["none"]);
            bgColors.push(getColorHex("none"));
        }
        const chartId = "chart-statement-" + idx;
        const ctx = document.getElementById(chartId);
        if (ctx) {
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
                            textAlign: 'left',
                            position: 'top',
                            align: 'start'
                        }
                    }
                }
            });
        }
        const ul = document.getElementById("player-votes-" + idx);
        if (ul) {
            ul.innerHTML = "";
            players.forEach(player => {
                const vote = (player.answers && player.answers[idx]) || null;
                const li = document.createElement("li");
                let name = player.name || "";
                let timeStr = "";
                if (vote && vote !== "None") {
                    timeStr = getPlayerTimeStr(player, idx);
                }
                li.innerHTML = name + (timeStr ? timeStr : "");
                if (!vote || vote === "None") {
                    li.style.color = getColorHex("none");
                } else {
                    li.style.color = getColorHex(vote);
                }
                li.style.fontWeight = "bold";
                li.style.marginBottom = "0.25em";
                ul.appendChild(li);
            });
        }
    });
}