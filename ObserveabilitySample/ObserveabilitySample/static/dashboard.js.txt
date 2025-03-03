$(document).ready(function () {
    $("#search").click(handleSearch);
});


let startDateInput = $('#start_date');
    let endDateInput = $('#end_date');

    // ✅ Initialize Date Inputs (sets default values if empty)
    function initializeDateInputs() {
        if (!startDateInput.val() || !endDateInput.val()) {
            let now = new Date();
            let oneHourAgo = new Date(now.getTime() - 6 * 60 * 60 * 1000);

            let formatDateTimeLocal = (date) => {
                let year = date.getFullYear();
                let month = String(date.getMonth() + 1).padStart(2, '0');
                let day = String(date.getDate()).padStart(2, '0');
                let hours = String(date.getHours()).padStart(2, '0');
                let minutes = String(date.getMinutes()).padStart(2, '0');
                return `${year}-${month}-${day}T${hours}:${minutes}`;
            };

            startDateInput.val(formatDateTimeLocal(oneHourAgo));
            endDateInput.val(formatDateTimeLocal(now));
        }
    }
    initializeDateInputs();

    // ✅ Fetch Transactions Based on Selected Test ID
    function fetchTransactions(selectedTestId) {
        let transactionDropdown = $('#transaction_name');
        transactionDropdown.empty().append(new Option("Select Transaction", "")); // Reset dropdown

        if (selectedTestId) {
            $.ajax({
                url: '/get_transactions',
                method: 'POST',
                data: { test_id: selectedTestId },
                success: function(response) {
                    transactionDropdown.empty();
                    response.transactions.forEach(transaction => {
                        transactionDropdown.append(new Option(transaction, transaction));
                    });
                    transactionDropdown.trigger('change'); // Refresh Select2
                }
            });
        }
    }

    // ✅ Event Listener for Test ID Change
    $('#test_id').on('change', function() {
        fetchTransactions($(this).val());
    });


        // ✅ Fetch Available Servers for the Selected Application
        function fetchServers(app) {
            $.getJSON(`/servers?application=${app}`, function(data) {
                let serverDropdown = $('#server_names');
                serverDropdown.empty().trigger("change"); // Clear and refresh
                data.forEach(server => {
                    let newOption = new Option(server.name, server.id, false, false);
                    serverDropdown.append(newOption);
                });
            });
        }
    
        // ✅ Event Listener for Application Change
        $('#application').change(function() {
            let app = $(this).val();
            fetchServers(app);
    
            // Reset Test ID and Transaction Dropdowns
            $('#test_id').empty().append(new Option("Select Test ID", ""));
            $('#transaction_name').empty().append(new Option("Select Transaction", ""));
            let testRunDropdown = document.getElementById("test_id");
    
            testRunDropdown.innerHTML = '<option value="">Select Test Scenario</option>';
            if (app in testScenarios) {
                testScenarios[app].forEach(test => {
                    let option = document.createElement("option");
                    option.value = test.testID;
                    option.textContent = `${test.testScenarioName} (${test.testID})`;
                    testRunDropdown.appendChild(option);
                });
            }
        });

        
// ✅ Function to handle search
function handleSearch() {
    $("#loading-spinner").show();
    let selectedServers = $('#server_names').val() || [];
    let startDate = $('#start_date').val();
    let endDate = $('#end_date').val();
    let granularity = $('#granularity').val();
    let application = $('#application').val();

    fetchSplunkData(application, startDate, endDate, granularity);
    fetchHostHealth(application, selectedServers);
    fetchTransactionData(application, selectedServers, startDate, endDate, granularity);
}

// ✅ Fetch Splunk Data
function fetchSplunkData(application, startDate, endDate, granularity) {
    $.ajax({
        url: "/fetch_splunk_data",
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ application, start_date: startDate, end_date: endDate, granularity }),
        beforeSend: () => $("#tables-container").empty(),
        success: renderSplunkTables,
        error: () => $("#tables-container").append("<p>Error fetching data.</p>"),
        complete: () => $("#loading-spinner").hide()
    });
}

// ✅ Render Splunk Tables
function renderSplunkTables(response) {
    console.log(response);
    Object.entries(response).forEach(([queryName, dataset]) => {
        let tableId = `table-${queryName.replace(/\s+/g, '-')}`;
        $("#tables-container").append(`<h4>${queryName}</h4><table id="${tableId}" class="display"></table>`);

        dataset = dataset.error ? [] : dataset;
        let headers = dataset.length ? Object.keys(dataset[0]) : ["No Data"];
        let timeColumn = headers.find(h => /^time$|^timestamp$|^eventtime$|^logtime$|^recordedtime$/.test(h.toLowerCase().replace(/\s+/g, '')));
        if (timeColumn) headers = [timeColumn, ...headers.filter(h => h !== timeColumn)];

        let tableHTML = `<thead><tr>${headers.map(h => `<th>${h}</th>`).join('')}</tr></thead><tbody>`;
        tableHTML += dataset.length ? dataset.map(row => `<tr>${headers.map(h => `<td>${row[h] || ''}</td>`).join('')}</tr>`).join('') : `<tr><td>No data found</td></tr>`;
        tableHTML += `</tbody>`;

        $(`#${tableId}`).html(tableHTML).DataTable({
            order: timeColumn ? [[headers.indexOf(timeColumn), "asc"]] : [],
            autoWidth: false,
            searching: dataset.length > 0,
            paging: dataset.length > 0,
            info: dataset.length > 0,
            columns: headers.map(h => ({ title: h, data: h })),
            columnDefs: [{ orderable: true, targets: "_all" }]
        });
    });
}

// ✅ Fetch Host Health
function fetchHostHealth(application, selectedServers) {
    $.ajax({
        url: "/get_host_health",
        type: "POST",
        contentType: "application/json",
        data: JSON.stringify({ applicationName: application, serverNames: selectedServers }),
        success: renderHostHealth,
        error: () => console.error("Error fetching host health data")
    });
}

// ✅ Render Host Health
function renderHostHealth(data) {
    $("#cpu_avg").text(`${data.summary.cpu_avg}%`);
    $("#memory_avg").text(`${data.summary.memory_avg}%`);
    $("#error_count").text(data.summary.total_errors);

    const honeycombContainer = $("#honeycomb").empty();
    data.health_data.forEach(server => {
        const statusClass = server.status === "Healthy" ? "healthy" : server.status === "Warning" ? "warning" : "critical";
        honeycombContainer.append(`<div class="hex ${statusClass}" data-tooltip="${server.server} | CPU: ${server.cpu_usage}% | Mem: ${server.memory_usage}% | Errors: ${server.error_count}">
            <strong>${server.server}</strong><br>CPU: ${server.cpu_usage}%<br>Mem: ${server.memory_usage}%<br>Errors: ${server.error_count}
        </div>`);
    });
}

// ✅ Fetch Transaction & Metrics Data
function fetchTransactionData(application, selectedServers, startDate, endDate, granularity) {
    $.ajax({
        url: '/get_data',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ application, servers: selectedServers, start_date: startDate, end_date: endDate, granularity }),
        success: renderTransactionData
    });
}

// ✅ Render Transaction Data & Charts
function renderTransactionData(data) {
    updateTable('#transactionsTable', data.transaction_summary, ["name", "tps", "avg_response_time"]);
    updateTable('#logTable', data.logs, ["timestamp", "server", "message"]);

    let timestamps = data.timestamps || [];

    createChart("statusCodesPie", "pie", Object.keys(data.status_codes), [{ data: Object.values(data.status_codes), backgroundColor: getDynamicColors(Object.keys(data.status_codes).length) }], "HTTP Status Codes");
    createChart("serverHitsDonut", "doughnut", Object.keys(data.server_hits), [{ data: Object.values(data.server_hits), backgroundColor: getDynamicColors(Object.keys(data.server_hits).length) }], "Server Hits");

    createTransactionCharts(data.transactions, timestamps);

    fetchMetrics("builtin:host.cpu.usage", "cpuUsageBar", "bar", "CPU Usage (%)");
    fetchMetrics("builtin:host.mem.usage", "memoryUsageLine", "line", "Memory Usage (%)");
}


// ✅ Determine Y-Axis Max Value
function getYAxisMax(data, overrideMax = null) {
    let maxValue = Math.max(...data) || 0;
    return overrideMax !== null ? overrideMax : Math.ceil((maxValue + 10) / 10) * 10;
}

// ✅ Base Chart Configuration
const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
        legend: {
            position: 'bottom',
            labels: { usePointStyle: true, boxWidth: 40, padding: 10 }
        }
    },
    scales: {
        x: { title: { display: true, text: "Time (HH:MM)" } },
        y: { beginAtZero: true }
    }
};

// ✅ Create a Chart Dynamically
function createChart(canvasId, chartType, labels, datasets, yAxisLabel = "", yAxisMax = null, customOptions = {}) {
    let canvas = document.getElementById(canvasId);
    let container = canvas.parentElement;

    if (!datasets.length || datasets.every(ds => ds.data.length === 0)) {
        container.querySelector(".no-data-message").style.display = "flex"; // Show "No Data Found"
        return;
    }

    let noDataElement = container.querySelector(".no-data-message");
    if (noDataElement) noDataElement.style.display = "none";

    let existingCanvas = container.querySelector("canvas");
    if (existingCanvas) existingCanvas.remove();

    let newCanvas = document.createElement("canvas");
    newCanvas.id = canvasId;
    container.appendChild(newCanvas);

    let finalOptions = { ...chartOptions, ...customOptions };
    finalOptions.maintainAspectRatio = false;

    if (!["pie", "doughnut"].includes(chartType)) {
        finalOptions.scales = {
            ...chartOptions.scales,
            ...customOptions.scales,
            y: {
                ...chartOptions.scales.y,
                ...customOptions.scales?.y,
                title: { display: true, text: yAxisLabel },
                max: yAxisMax
            }
        };
    } else {
        finalOptions.scales = {};
    }

    // new Chart(document.getElementById(canvasId), {
    //     type: chartType,
    //     data: { labels: labels, datasets },
    //     options: finalOptions
    // });
    let chart = new Chart(document.getElementById(canvasId), {
        type: chartType,
        data: { labels: labels, datasets },
        options: finalOptions
    });

    // ✅ Add Zoom Functionality
    addZoomFunctionality(chart, canvasId);
}


// ✅ Zoom Functionality (Handles mouse wheel zoom)
function addZoomFunctionality(chart, canvasId) {
    let canvas = document.getElementById(canvasId);

    canvas.addEventListener("wheel", function (event) {
        event.preventDefault();

        // Zoom only when hovering over the chart
        if (!canvas.matches(":hover")) return;

        let scale = chart.options.scales.y;
        let zoomFactor = event.deltaY > 0 ? 1.1 : 0.9; // Scroll up: Zoom in, Scroll down: Zoom out

        if (!scale.max) scale.max = 100; // Default max value if not set
        let newMax = scale.max * zoomFactor;

        scale.max = Math.max(newMax, 10); // Prevent zooming too much out
        chart.update();
    }, { passive: false });
}


// ✅ Create Transaction Charts
function createTransactionCharts(transactions, timestamps) {
    let tpsValues = Object.values(transactions).flatMap(t => t.tps_values);
    let responseTimeValues = Object.values(transactions).flatMap(t => t.response_times);

    createChart("tpsLineChart", "line", timestamps, Object.keys(transactions).map((transaction, index) => ({
        label: `${transaction} TPS`,
        data: transactions[transaction].tps_values,
        borderColor: `hsl(${index * 60}, 70%, 50%)`,
        fill: false
    })), "TPS", getYAxisMax(tpsValues));

    createChart("responseTimesLine", "line", timestamps, Object.keys(transactions).map((transaction, index) => ({
        label: transaction,
        data: transactions[transaction].response_times,
        borderColor: `hsl(${index * 60}, 70%, 50%)`,
        fill: false
    })), "Response Time (s)", getYAxisMax(responseTimeValues));
}

// ✅ Update DataTable
function updateTable(tableId, data, columns) {
    if ($.fn.DataTable.isDataTable(tableId)) $(tableId).DataTable().destroy();
    $(`${tableId} tbody`).html(data.map(row => `<tr>${columns.map(col => `<td>${row[col]}</td>`).join('')}</tr>`).join(""));
    $(tableId).DataTable({ paging: true, searching: true, ordering: true, info: true, lengthMenu: [5, 10, 25, 50] });
}



// Function to dynamically generate different types of charts
function generateChart(chartId, chartType, labels, dataset, label, maxYAxis = null) {
    let ctx = document.getElementById(chartId).getContext("2d");

    // Destroy the previous chart instance to prevent duplication
    // if (window[chartId]) {
    //     window[chartId].destroy();
    // }

    // Check if the chart instance exists before destroying it
    if (window[chartId] instanceof Chart) {
        window[chartId].destroy();
    }

    // Create a new chart
    window[chartId] = new Chart(ctx, {
        type: chartType,  // Chart type (pie, doughnut, line, bar)
        data: {
            labels: labels,  // X-axis labels (timestamps, categories)
            datasets: dataset // Data points for the chart
        },
        options: {
            responsive: true, // Makes the chart responsive
            maintainAspectRatio: false, // Prevents forced aspect ratio
            plugins: {
                legend: { display: true }, // Enables legend display
                tooltip: { enabled: true } // Enables tooltips on hover
            },
            // Different scale settings for Pie/Doughnut vs Line/Bar charts
            scales: chartType === "pie" || chartType === "doughnut" ? {} : {
                y: {
                    beginAtZero: true, // Ensures y-axis starts from 0
                    max: maxYAxis, // Sets max value for y-axis if provided
                    title: { display: true, text: label } // Y-axis title
                },
                x: {
                    title: { display: true, text: "Time" } // X-axis title
                }
            }
        }
    });
}

// Utility function to generate a dynamic array of colors
function getDynamicColors(count) {
    return [...Array(count)].map((_, i) => `hsl(${i * 40}, 70%, 50%)`);
}

// Function to fetch metrics dynamically from an API and generate charts
function fetchMetrics(metricType, chartId, chartType, label) {
    fetch('/metrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            application: $('#application').val(), // Gets selected application
            servers: $('#server_names').val() || [], // Gets selected servers
            start_date: $('#start_date').val(), // Gets start date
            end_date: $('#end_date').val(), // Gets end date
            granularity: $('#granularity').val(), // Gets granularity level
            metric: metricType // Specifies the metric to fetch
        })
    })
    .then(response => response.json()) // Convert response to JSON
    .then(data => {
        if (data.error) {
            console.error(`Error fetching ${metricType}:`, data.error);
            return;
        }

        let metricData = data[metricType] || []; // Get metric data from response
        let timestamps = [...new Set(metricData.map(entry => entry.timestamp))]; // Get unique timestamps
        let servers = [...new Set(metricData.map(entry => entry.server))]; // Get unique servers

        // Create datasets for each server
        let datasets = servers.map((server, index) => ({
            label: server, // Server name
            data: timestamps.map(ts => {
                let entry = metricData.find(e => e.timestamp === ts && e.server === server);
                return entry ? entry.value : null; // Get data or null if missing
            }),
            backgroundColor: chartType === "bar" ? `hsl(${index * 40}, 70%, 50%)` : undefined,
            borderColor: chartType === "line" ? `hsl(${index * 40}, 70%, 50%)` : undefined,
            fill: false, // Do not fill the area under the line
            spanGaps: true // Allows missing data points
        }));

        let maxYAxis = Math.max(...metricData.map(e => e.value), 100); // Get max y-axis value
        generateChart(chartId, chartType, timestamps, datasets, label, maxYAxis); // Generate chart
    })
    .catch(error => console.error(`Error processing ${metricType}:`, error));
}

// Function to process fetched data and generate different charts
function processChartData(data) {
    let timestamps = data.timestamps || []; // Extract timestamps from data

    // HTTP Status Codes Pie Chart
    generateChart("statusCodesPie", "pie", Object.keys(data.status_codes), [{
        data: Object.values(data.status_codes), // Count of each status code
        backgroundColor: getDynamicColors(Object.keys(data.status_codes).length)
    }], "HTTP Status Codes");

    // Server Hits Donut Chart
    generateChart("serverHitsDonut", "doughnut", Object.keys(data.server_hits), [{
        data: Object.values(data.server_hits), // Number of hits per server
        backgroundColor: getDynamicColors(Object.keys(data.server_hits).length)
    }], "Server Hits");

    // Transaction TPS Line Chart
    let tpsValues = Object.values(data.transactions).flatMap(t => t.tps_values); // Get all TPS values
    generateChart("tpsLineChart", "line", timestamps, Object.keys(data.transactions).map((transaction, index) => ({
        label: `${transaction} TPS`,
        data: data.transactions[transaction].tps_values,
        borderColor: `hsl(${index * 60}, 70%, 50%)`,
        fill: false
    })), "TPS", Math.max(...tpsValues, 10));

    // Response Time Line Chart
    let responseTimeValues = Object.values(data.transactions).flatMap(t => t.response_times);
    generateChart("responseTimesLine", "line", timestamps, Object.keys(data.transactions).map((transaction, index) => ({
        label: transaction,
        data: data.transactions[transaction].response_times,
        borderColor: `hsl(${index * 60}, 70%, 50%)`,
        fill: false
    })), "Response Time (s)", Math.max(...responseTimeValues, 10));

    // Fetch and generate CPU & Memory metrics
    fetchMetrics("builtin:host.cpu.usage", "cpuUsageBar", "bar", "CPU Usage (%)");
    fetchMetrics("builtin:host.mem.usage", "memoryUsageLine", "line", "Memory Usage (%)");
}

// // Event listener for button click to fetch data and generate charts
// document.getElementById("fetchDataButton").addEventListener("click", function () {
//     fetch('/metrics/summary')
//         .then(response => response.json())
//         .then(data => processChartData(data)) // Process the fetched data
//         .catch(error => console.error("Error fetching summary data:", error));
// });



// PDF export functionality
document.addEventListener("DOMContentLoaded", function() { 
    // Ensures the script runs only after the HTML document has fully loaded

    // Get references to the export buttons
    const pdfButton = document.getElementById("export-pdf"); 
    const pngButton = document.getElementById("export-png");

    // Check if both buttons exist before proceeding
    if (pdfButton && pngButton) {

        // Add event listener for PDF export button
        pdfButton.addEventListener("click", function() {
            const { jsPDF } = window.jspdf; // Get the jsPDF library
            let pdf = new jsPDF('landscape', 'mm', 'a4'); // Create a new PDF in landscape A4 format

            // Capture the entire webpage as a canvas
            html2canvas(document.body, {
                scrollY: -window.scrollY // Adjust to remove scrolling issues
            }).then(canvas => {
                let imgData = canvas.toDataURL("image/png"); // Convert canvas to a PNG image
                let imgWidth = 290; // Define image width to fit A4 landscape
                let imgHeight = (canvas.height * imgWidth) / canvas.width; // Maintain aspect ratio

                // Add the image to the PDF document
                pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
                pdf.save("dashboard.pdf"); // Save the generated PDF
            });
        });

        // Add event listener for PNG export button
        pngButton.addEventListener("click", function() {
            html2canvas(document.body, {
                scrollY: -window.scrollY // Adjust for proper capture
            }).then(canvas => {
                let link = document.createElement('a'); // Create a new anchor element
                link.href = canvas.toDataURL("image/png"); // Convert canvas to PNG format
                link.download = "dashboard.png"; // Set the file name for download
                link.click(); // Trigger the download
            });
        });
    }
});

// Tooltip functionality for elements with the class "hex"
$(document).on("mouseenter", ".hex", function() {
    let tooltipText = $(this).attr("data-tooltip"); // Get the tooltip text from the "data-tooltip" attribute
    if (tooltipText) {
        let tooltip = $("<div class='custom-tooltip'></div>").text(tooltipText); // Create a new tooltip div
        $("body").append(tooltip); // Append tooltip to the body

        // Update tooltip position on mouse movement
        $(this).on("mousemove", function(e) {
            tooltip.css({ left: e.pageX + 10, top: e.pageY + 10 }); // Position the tooltip near the cursor
        });
    }
}).on("mouseleave", ".hex", function() {
    $(".custom-tooltip").remove(); // Remove the tooltip when the mouse leaves the element
});
