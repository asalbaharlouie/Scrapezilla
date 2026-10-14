const startButton = document.getElementById("startButton");
const pagesSelect = document.getElementById("pages");
const categorySelect = document.getElementById("category");
const brandInput = document.getElementById("brand");
const notice = document.getElementById("notice");

let pollTimer = null;

function getSelectedMethod() {
    return document.querySelector(
        'input[name="method"]:checked'
    ).value;
}

function getMethodLabel(method) {
    return method === "async" ? "Async" : "Threading";
}

function setNotice(message, isError = false) {
    notice.textContent = message;
    notice.classList.toggle("error", isError);
}

document.querySelectorAll('input[name="method"]').forEach(input => {
    input.addEventListener("change", () => {
        document.getElementById("selectedMethod").textContent =
            getMethodLabel(getSelectedMethod());
    });
});

function renderResults(products) {
    const body = document.getElementById("resultsBody");
    body.replaceChildren();

    if (!products || products.length === 0) {
        const row = document.createElement("tr");
        const cell = document.createElement("td");

        cell.colSpan = 4;
        cell.className = "empty-state";
        cell.textContent = "No products available yet.";

        row.appendChild(cell);
        body.appendChild(row);
        return;
    }

    products.forEach(product => {
        const row = document.createElement("tr");

        const title = document.createElement("td");
        title.textContent =
            product.title_en || product.title_fa || "Untitled product";

        const price = document.createElement("td");
        price.textContent = product.price_toman == null
            ? "N/A"
            : Number(product.price_toman).toLocaleString("en-US");

        const rating = document.createElement("td");
        rating.textContent =
            product.rating_rate == null ? "N/A" : product.rating_rate;

        const linkCell = document.createElement("td");

        if (product.url) {
            const link = document.createElement("a");
            link.href = product.url;
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.textContent = "View Product ↗";
            linkCell.appendChild(link);
        } else {
            linkCell.textContent = "N/A";
        }

        [title, price, rating, linkCell].forEach(cell => {
            row.appendChild(cell);
        });

        body.appendChild(row);
    });
}

function updateDashboard(data) {
    const progress = Number(data.progress || 0);
    const total = Number(data.total_pages || pagesSelect.value || 1);

    document.getElementById("progressText").textContent = progress;
    document.getElementById("progressTotal").textContent =
        `of ${total} pages`;

    const percentage = total
        ? Math.min(100, (progress / total) * 100)
        : 0;

    document.getElementById("progressBar").style.width =
        `${percentage}%`;

    document.getElementById("statusText").textContent =
        data.status || "Ready to start";

    document.getElementById("productCount").textContent =
        Number(data.products_count || 0).toLocaleString("en-US");

    if (data.method) {
        document.getElementById("selectedMethod").textContent =
            getMethodLabel(data.method);
    }

    const badge = document.getElementById("statusBadge");

    badge.textContent = data.running
        ? "Running"
        : (data.status || "Ready");

    badge.className = "status-badge";

    if (data.running) {
        badge.classList.add("running");
    } else if (data.error) {
        badge.classList.add("error");
    } else if (data.elapsed !== null && data.elapsed !== undefined) {
        badge.classList.add("done");
    }

    if (data.elapsed !== null && data.elapsed !== undefined) {
        document.getElementById("elapsed").textContent = data.elapsed;
        document.getElementById("lastMethod").textContent =
            getMethodLabel(data.method);
    }

    renderResults(data.results || []);

    if (data.error) {
        setNotice(`Error: ${data.error}`, true);
    } else if (!data.running && data.elapsed != null) {
        setNotice("Scraping completed. The CSV file has been saved.");
    }

    startButton.disabled = Boolean(data.running);

    startButton.innerHTML = data.running
        ? "<span>◌</span> Scraping..."
        : "<span>▶</span> Start Scraping";
}

async function pollStatus() {
    try {
        const response = await fetch("/api/status");

        if (!response.ok) {
            throw new Error("Could not read job status.");
        }

        const data = await response.json();
        updateDashboard(data);

        if (!data.running && pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    } catch (error) {
        setNotice(
            "Could not connect to the server. Make sure Flask is running.",
            true
        );
    }
}

startButton.addEventListener("click", async () => {
    const category = categorySelect.value.trim();
    const brand = brandInput.value.trim();

    if (!category) {
        setNotice("Please select a category.", true);
        return;
    }

    if (!brand) {
        setNotice("Please enter a brand.", true);
        return;
    }

    startButton.disabled = true;
    setNotice("Sending request to the server...");

    try {
        const response = await fetch("/api/start", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                method: getSelectedMethod(),
                pages: Number(pagesSelect.value),
                category: category,
                brand: brand
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Could not start scraping.");
        }

        setNotice("Scraping started. Updating job status...");

        if (pollTimer) {
            clearInterval(pollTimer);
        }

        await pollStatus();
        pollTimer = setInterval(pollStatus, 1000);

    } catch (error) {
        startButton.disabled = false;
        setNotice(error.message, true);
    }
});

pollStatus();
