async function populateReports() {
    const select = document.getElementById("reportSelect");

    try {
        const res = await fetch("index_data.json");
        const reports = await res.json();

        if (reports.length === 0) {
            document.getElementById("output").textContent = "No reports found.";
            return;
        }

        reports.forEach(file => {
            const option = document.createElement("option");
            option.value = file;
            option.text = file.replace("report-", "").replace(".json", "");
            select.appendChild(option);
        });

        loadReport(reports[0]); // Auto-load latest
    } catch (err) {
        document.getElementById("output").textContent = `Error loading reports: ${err}`;
    }
}

function loadReport(filename) {
    fetch(`${filename}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById("output").textContent = JSON.stringify(data, null, 2);
        })
        .catch(err => {
            document.getElementById("output").textContent = `Error loading report: ${err}`;
        });
}

document.getElementById("reportSelect").addEventListener("change", e => {
    loadReport(e.target.value);
});

window.onload = populateReports;
