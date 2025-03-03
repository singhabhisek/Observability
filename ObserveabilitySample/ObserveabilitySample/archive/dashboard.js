    
    
    //PDF export

    document.addEventListener("DOMContentLoaded", function() {
        // alert('hi');
        const pdfButton = document.getElementById("export-pdf");
        const pngButton = document.getElementById("export-png");

        if (pdfButton && pngButton) {
            pdfButton.addEventListener("click", function() {
                const {
                    jsPDF
                } = window.jspdf;
                let pdf = new jsPDF('landscape', 'mm', 'a4');

                html2canvas(document.body, {
                    scrollY: -window.scrollY
                }).then(canvas => {
                    let imgData = canvas.toDataURL("image/png");
                    let imgWidth = 290; // Adjust to fit A4 landscape
                    let imgHeight = (canvas.height * imgWidth) / canvas.width;

                    pdf.addImage(imgData, 'PNG', 10, 10, imgWidth, imgHeight);
                    pdf.save("dashboard.pdf");
                });
            });

            pngButton.addEventListener("click", function() {
                html2canvas(document.body, {
                    scrollY: -window.scrollY
                }).then(canvas => {
                    let link = document.createElement('a');
                    link.href = canvas.toDataURL("image/png");
                    link.download = "dashboard.png";
                    link.click();
                });
            });
        }
    });


    $(document).on("mouseenter", ".hex", function() {
        let tooltipText = $(this).attr("data-tooltip");
        if (tooltipText) {
            let tooltip = $("<div class='custom-tooltip'></div>").text(tooltipText);
            $("body").append(tooltip);
            $(this).on("mousemove", function(e) {
                tooltip.css({ left: e.pageX + 10, top: e.pageY + 10 });
            });
        }
    }).on("mouseleave", ".hex", function() {
        $(".custom-tooltip").remove();
    });

    $(document).ready(function() {

        let startDateInput = $('#start_date');
        let endDateInput = $('#end_date');

        if (!startDateInput.val() || !endDateInput.val()) {
            let now = new Date();
            let oneHourAgo = new Date(now.getTime() - 6 * 60 * 60 * 1000);

            let formatDateTimeLocal = (date) => {
                let year = date.getFullYear();
                let month = String(date.getMonth() + 1).padStart(2, '0');
                let day = String(date.getDate()).padStart(2, '0');
                let hours = String(date.getHours()).padStart(2, '0');
                let minutes = String(date.getMinutes()).padStart(2, '0');
                return `${year}-${month}-${day}T${hours}:${minutes}`; // Local time format
            };

            startDateInput.val(formatDateTimeLocal(oneHourAgo));
            endDateInput.val(formatDateTimeLocal(now));
        }

        // Initialize Select2
        $('#application').select2({
            placeholder: "Select Application",
            allowClear: true
        });

        $('#granularity').select2({
            placeholder: "Select Granularity",
            allowClear: true
        });


        $('#test_id').select2({
            placeholder: "Select Test ID",
            allowClear: true
        });

        $('#server_names').select2({
            placeholder: "Select Server Names",
            multiple: true,
            allowClear: true
        });

        $('#transaction_name').select2({
            placeholder: "Select Transactions",
            multiple: true,
            allowClear: true
        });

        // Fetch transactions based on selected Test ID
        $('#test_id').on('change', function() {
            var selectedTestId = $(this).val();
            var transactionDropdown = $('#transaction_name');
            transactionDropdown.empty().append(new Option("Select Transaction", "")); // Clear previous transactions

            if (selectedTestId) {
                $.ajax({
                    url: '/get_transactions', // This should be a valid endpoint in app.py
                    method: 'POST',
                    data: {
                        test_id: selectedTestId
                    },
                    success: function(response) {
                        var transactionDropdown = $('#transaction_name');
                        transactionDropdown.empty();
                        response.transactions.forEach(function(transaction) {
                            transactionDropdown.append(new Option(transaction, transaction));
                        });
                        transactionDropdown.trigger('change'); // Refresh Select2
                    }
                });
            }
        });


        $('#application').change(function() {
            let app = $(this).val();
            fetchServers(app);

            
            var selectedApp = this.value;
            $('#test_id').empty().append(new Option("Select Test ID", "")); // Reset Test ID dropdown
            $('#transaction_name').empty().append(new Option("Select Transaction", "")); // Reset Transactions
            var testRunDropdown = document.getElementById("test_id");

            // Clear previous options
            testRunDropdown.innerHTML = '<option value="">Select Test Scenario</option>';

            if (selectedApp in testScenarios) {
                testScenarios[selectedApp].forEach(function(test) {
                    var option = document.createElement("option");
                    option.value = test.testID;
                    option.textContent = `${test.testScenarioName} (${test.testID})`;
                    testRunDropdown.appendChild(option);
                });
            }

            
        });

        function fetchServers(app) {
            $.getJSON(`/servers?application=${app}`, function(data) {
                $('#server_names').empty().trigger("change");
                data.forEach(server => {
                    let newOption = new Option(server.name, server.id, false, false); //.id
                    $('#server_names').append(newOption);
                });
                // $('#server_names').trigger("change");
            });
        }

        // $('#application').change(function() {
        //     var app = $(this).val();
        //     $('#server_names').empty();
        //     applications[app].forEach(server => {
        //         $('#server_names').append(`<option value="${server}">${server}</option>`);
        //     });
        // });

        function getYAxisMax(data, overrideMax = null) {
            let maxValue = Math.max(...data) || 0; // Handle empty dataset
            return overrideMax !== null ? overrideMax : Math.ceil((maxValue + 10) / 10) * 10;
        }

        const chartOptions = {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true, // Use small line instead of a box
                        boxWidth: 40,
                        padding: 10
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: "Time (HH:MM)"
                    }
                },
                y: {
                    beginAtZero: true
                }
            }
        };

        function createChart(canvasId, chartType, labels, datasets, yAxisLabel = "", yAxisMax = null, customOptions = {}) {
            let canvas = document.getElementById(canvasId);
            let container = canvas.parentElement;

            // 🔹 If No Data, Show "No Data Found"
            // if (!datasets.length || datasets.every(ds => ds.data.length === 0)) {
            //     container.innerHTML = `<div class="no-data">No Data Found</div>`;
            //     return;
            // }

            if (!datasets.length || datasets.every(ds => ds.data.length === 0)) {
                container.querySelector(".no-data-message").style.display = "flex"; // Show "No Data Found"
                return;
            }

            // Hide "No Data Found" if data exists
            let noDataElement = container.querySelector(".no-data-message");
            if (noDataElement) noDataElement.style.display = "none";



            // container.innerHTML = `<canvas id="${canvasId}"></canvas>`; // Reset canvas
            let existingCanvas = container.querySelector("canvas");

            // If canvas exists, remove only it (not the <h5>)
            if (existingCanvas) existingCanvas.remove();

            // Append a new canvas, preserving the <h5> heading
            let newCanvas = document.createElement("canvas");
            newCanvas.id = canvasId;
            container.appendChild(newCanvas);

            let finalOptions = {
                ...chartOptions,
                ...customOptions
            };
            finalOptions.maintainAspectRatio = false; // Allow dynamic height

            // 🔹 Skip scales for Pie/Donut charts
            if (!["pie", "doughnut"].includes(chartType)) {
                finalOptions.scales = {
                    ...chartOptions.scales,
                    ...customOptions.scales,
                    y: {
                        ...chartOptions.scales.y,
                        ...customOptions.scales?.y,
                        title: {
                            display: true,
                            text: yAxisLabel
                        },
                        max: yAxisMax
                    }
                };
            }

            if (["pie", "doughnut"].includes(chartType)) {
                finalOptions.scales = {}; // Remove X-Y axes for Pie and Donut charts
            }

            new Chart(document.getElementById(canvasId), {
                type: chartType,
                data: {
                    labels: labels,
                    datasets
                },
                options: finalOptions
            });
        }

        function getDynamicColors(count) {
            return Array.from({
                length: count
            }, (_, i) => `hsl(${(i * 360) / count}, 70%, 50%)`);
        }

        $('#search').click(function() {
            $("#loading-spinner").show();  // Show the loading spinner
            let selectedServers = $('#server_names').val() || [];
            let startDate = $('#start_date').val(); // Ensure date format matches backend
            let endDate = $('#end_date').val();
            let granularity = $('#granularity').val(); // Get selected granularity
            let application = $('#application').val()
            

            $.ajax({
                url: "/fetch_splunk_data", // API endpoint to fetch Splunk data
                type: 'POST', // Sending a POST request
                contentType: 'application/json', // Setting request content type as JSON
                data: JSON.stringify({
                    application: application,
                    start_date: startDate, // Start date filter for fetching data
                    end_date: endDate, // End date filter for fetching data
                    granularity: granularity // Granularity level for data aggregation
                }),
                beforeSend: function() {
                    $("#tables-container").empty(); // ✅ Clear previous tables and headings before inserting new data
                },
                success: function(response) {
                    console.log("API Response:", response); // Debugging: Log the response format

                    // Loop through each dataset in the response
                    for (const [queryName, dataset] of Object.entries(response)) {
                        let tableId = `table-${queryName.replace(/\s+/g, '-')}`; // Generate a unique table ID based on the query name
                        $("#tables-container").append(`<h4>${queryName}</h4><table id="${tableId}" class="display"></table>`); // Create table and title

                        if (dataset.error) {
                            dataset = []; // If an error exists, treat it as an empty dataset
                        }

                        let headers = []; // Array to store column headers
                        let timeColumn = null; // Variable to store the identified timestamp column
                        let tableHTML = `<thead><tr>`; // Start building table header HTML

                        if (dataset.length > 0) { // Check if dataset has data
                            let firstRow = dataset[0]; // Get the first row to extract headers
                            headers = Object.keys(firstRow); // Get all column names

                            console.log("Headers before sorting:", headers); // Debugging: Log headers before sorting

                            // Identify the column that represents timestamps (excluding responseTime, etc.)
                            timeColumn = headers.find(h => {
                                let lowerH = h.toLowerCase().replace(/\s+/g, ''); // Normalize column name by removing spaces and converting to lowercase
                                return /^time$|^timestamp$|^eventtime$|^logtime$|^recordedtime$/.test(lowerH); // Check for common timestamp column names
                            });

                            // ✅ Move timestamp column to first position if found
                            if (timeColumn) {
                                headers = [timeColumn, ...headers.filter(h => h !== timeColumn)]; // Reorder columns with timestamp first
                            }

                            console.log("Headers after sorting:", headers); // Debugging: Log headers after sorting

                            // Build table headers
                            headers.forEach(header => {
                                tableHTML += `<th>${header}</th>`; // Add each header as a table column
                            });
                            tableHTML += `</tr></thead><tbody>`; // Close table header and start table body

                            // Loop through dataset and build table rows
                            dataset.forEach(row => {
                                tableHTML += `<tr>`; // Start a new row
                                headers.forEach(header => {
                                    tableHTML += `<td>${row[header] || ''}</td>`; // Populate row data, defaulting to empty string if missing
                                });
                                tableHTML += `</tr>`; // Close row
                            });

                        } else { // ✅ Case where no data is found, still creating a table
                            headers = ["No Data"]; // Set a placeholder header
                            tableHTML += `<th>No Data</th></tr></thead><tbody><tr><td>No data found for the given filter</td></tr>`; // Show "No Data" message
                        }

                        tableHTML += `</tbody>`; // Close table body
                        $(`#${tableId}`).html(tableHTML); // ✅ **Replace existing table content instead of appending**

                        // Initialize DataTables with correct column order and settings
                        $(`#${tableId}`).DataTable({
                            "order": timeColumn ? [
                                [headers.indexOf(timeColumn), "asc"]
                            ] : [], // Sort by timestamp column if available
                            "autoWidth": false, // Disable auto width for better formatting
                            "searching": dataset.length > 0, // Disable search if no data
                            "paging": dataset.length > 0, // Disable pagination if no data
                            "info": dataset.length > 0, // Disable info text if no data
                            "columns": headers.map(h => ({
                                title: h,
                                data: h
                            })), // ✅ Define columns explicitly to prevent 'mData' errors
                            "columnDefs": [{
                                "orderable": true,
                                "targets": "_all"
                            }] // Enable sorting for all columns
                        });
                    }
                },
                error: function() {
                    $("#tables-container").append("<p>Error fetching data.</p>"); // Display error message if the API call fails
                },

                complete: function() {  
                    $("#loading-spinner").hide();  // Hide spinner when request completes  
                }  
            });



            // Get selected application name
            let applicationName = $("#application").val() || "";

            // Get selected server names (multiselect)
            let selectedServers1 = $("#server_names").val(); // Select2 returns an array

            // If no server is selected, consider all available servers in the dropdown
            if (!selectedServers1 || selectedServers1.length === 0) {
                selectedServers1 = $("#server_names option").map(function() {
                    return $(this).val();
                }).get(); // Get all server names
            }



            function fetchMetrics(metricType, chartId, chartType, label, colorKey) {
                fetch('/metrics', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        application: $('#application').val(),
                        servers: selectedServers,
                        start_date: startDate,
                        end_date: endDate,
                        granularity: granularity,
                        metric: metricType // ✅ Dynamic metric selection
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        console.error(`Error fetching ${metricType}:`, data.error);
                        return;
                    }
            
                    let metricData = data[metricType] || []; // Handle missing data safely
                    let timestamps = [...new Set(metricData.map(entry => entry.timestamp))];
                    let servers = [...new Set(metricData.map(entry => entry.server))];
                    console.log("Last few data points:", metricData.slice(-5));

                    let datasets = servers.map((server, index) => ({
                        label: server,
                        data: timestamps.map(ts => {
                            // let entry = metricData.find(e => e.timestamp === ts && e.server === server);
                            // return entry ? entry.value : null; // Handle missing data points
                            let entry = metricData.find(e => e.timestamp === ts && e.server === server);
                            if (entry) return entry.value;
                            
                            // Fill missing values with the last known value
                            return idx > 0 ? timestamps[idx - 1] : null;
                        }),
                        backgroundColor: chartType === "bar" ? `hsl(${index * 40}, 70%, 50%)` : undefined,
                        borderColor: chartType === "line" ? `hsl(${index * 40}, 70%, 50%)` : undefined,
                        fill: false,
                        spanGaps: true
                    }));
            
                    createChart(chartId, chartType, timestamps, datasets, label, getYAxisMax(metricData.map(e => e.value), 100));
                })
                .catch(error => console.error(`Error processing ${metricType}:`, error));
            }
            
        

            // Prepare request payload
            let requestData = {
                applicationName: applicationName,
                serverNames: selectedServers1
            };

            // 🟢 Make a POST request to /get_host_health
            $.ajax({
                url: "/get_host_health",
                type: "POST",
                contentType: "application/json",
                data: JSON.stringify(requestData), // Convert data to JSON
                success: function(data) {
                    console.log("Host Health Data:", data); // Debugging

                    // Extract summary metrics
                    document.getElementById("cpu_avg").textContent = data.summary.cpu_avg + "%";
                    document.getElementById("memory_avg").textContent = data.summary.memory_avg + "%";
                    document.getElementById("error_count").textContent = data.summary.total_errors;

                    const honeycombContainer = document.getElementById("honeycomb");
                    honeycombContainer.innerHTML = ""; // Clear previous content

                    // Loop through each server's health data
                    data.health_data.forEach(server => {
                        const div = document.createElement("div");
                        div.classList.add("hex");

                        // Assign Color Based on Status
                        if (server.status === "Healthy") {
                            div.classList.add("healthy");
                        } else if (server.status === "Warning") {
                            div.classList.add("warning");
                        } else {
                            div.classList.add("critical");
                        }


                        // 🟢 Server status coloring is now handled in `app.py`, so no status check here
                        div.innerHTML = `
                            <strong>${server.server}</strong><br>
                            CPU: ${server.cpu_usage}%<br>
                            Mem: ${server.memory_usage}%<br>
                            Errors: ${server.error_count}
                        `;

                        // Store text inside `data-tooltip` attribute for hidden tooltip
                        div.setAttribute("data-tooltip", `${server.server} | CPU: ${server.cpu_usage}% | Mem: ${server.memory_usage}% | Errors: ${server.error_count}`);

                        honeycombContainer.appendChild(div);

                        console.log(document.querySelectorAll(".hex"));

                    });
                },
                error: function() {
                    console.error("Error fetching host health data");
                }
            });


            // // Call `fetchHostHealth` when needed (e.g., on button click)
            // $("#fetchHealthBtn").on("click", fetchHostHealth);

            $.ajax({
                url: '/get_data',
                type: 'POST',
                contentType: 'application/json',
                // data: JSON.stringify({ application: $('#application').val() }),
                data: JSON.stringify({
                    application: $('#application').val(),
                    servers: selectedServers, // ✅ Send selected servers
                    start_date: startDate,
                    end_date: endDate,
                    granularity: granularity // ✅ Send selected granularity
                }),
                success: function(data) {
                    // console.log(data);
                    // 🟢 Populate Transactions Table
                    if ($.fn.DataTable.isDataTable('#transactionsTable')) {
                        $('#transactionsTable').DataTable().destroy(); // Destroy existing instance
                    }
                    $('#transactionsTable tbody').html(data.transaction_summary.map(t =>
                        `<tr><td>${t.name}</td><td>${t.tps}</td><td>${t.avg_response_time}</td></tr>`
                    ).join(""));

                    $('#transactionsTable').DataTable({
                        "paging": true,
                        "searching": true,
                        "ordering": true,
                        "info": true,
                        "lengthMenu": [5, 10, 25, 50] // Customize rows per page
                    });

                    // 🟢 Populate Logs Table
                    if ($.fn.DataTable.isDataTable('#logTable')) {
                        $('#logTable').DataTable().destroy();
                    }
                    $('#logTable tbody').html(data.logs.map(log =>
                        `<tr><td>${log.timestamp}</td><td>${log.server}</td><td>${log.message}</td></tr>`
                    ).join(""));

                    $('#logTable').DataTable({
                        "paging": true,
                        "searching": true,
                        "ordering": true,
                        "info": true,
                        "lengthMenu": [5, 10, 25, 50]
                    });

                    let timestamps = data.timestamps || []; // ✅ Ensure timestamps is always defined

                    // 🥧 Pie Chart: HTTP Status Codes
                    let statusKeys = Object.keys(data.status_codes);
                    createChart("statusCodesPie", "pie", statusKeys, [{
                        data: Object.values(data.status_codes),
                        backgroundColor: getDynamicColors(statusKeys.length)
                    }], "HTTP Status Codes");

                    // 🍩 Donut Chart: Server Hits
                    let serverKeys = Object.keys(data.server_hits);
                    createChart("serverHitsDonut", "doughnut", serverKeys, [{
                        data: Object.values(data.server_hits),
                        backgroundColor: getDynamicColors(serverKeys.length)
                    }], "Server Hits");

                    let tpsValues = Object.values(data.transactions).flatMap(t => t.tps_values);
                    createChart("tpsLineChart", "line", timestamps, Object.keys(data.transactions).map((transaction, index) => ({
                        label: `${transaction} TPS`,
                        data: data.transactions[transaction].tps_values,
                        borderColor: `hsl(${index * 60}, 70%, 50%)`,
                        fill: false
                    })), "TPS", getYAxisMax(tpsValues));

                    let responseTimeValues = Object.values(data.transactions).flatMap(t => t.response_times);
                    createChart("responseTimesLine", "line", timestamps, Object.keys(data.transactions).map((transaction, index) => ({
                        label: transaction,
                        data: data.transactions[transaction].response_times,
                        borderColor: `hsl(${index * 60}, 70%, 50%)`,
                        fill: false
                    })), "Response Time (s)", getYAxisMax(responseTimeValues));

                    // Fetch CPU and Memory metrics
                    fetchMetrics("builtin:host.cpu.usage", "cpuUsageBar", "bar", "CPU Usage (%)");
                    fetchMetrics("builtin:host.mem.usage", "memoryUsageLine", "line", "Memory Usage (%)");
               
                }
            });
        });
    });