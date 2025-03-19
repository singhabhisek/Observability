

$(document).ready(function() {

    let startDateInput = $('#start_date'); // Select start date input field
    let endDateInput = $('#end_date'); // Select end date input field

    // ✅ Function to initialize date inputs with default values if empty
    function initializeDateInputs() {
        if (!startDateInput.val() || !endDateInput.val()) { // Check if inputs are empty
            let now = new Date(); // Get current date and time
            let oneHourAgo = new Date(now.getTime() - 6 * 60 * 60 * 1000); // Calculate time 6 hours ago

            // Function to format date into YYYY-MM-DDTHH:MM format
            let formatDateTimeLocal = (date) => {
                let year = date.getFullYear();
                let month = String(date.getMonth() + 1).padStart(2, '0'); // Ensure two-digit month
                let day = String(date.getDate()).padStart(2, '0'); // Ensure two-digit day
                let hours = String(date.getHours()).padStart(2, '0'); // Ensure two-digit hours
                let minutes = String(date.getMinutes()).padStart(2, '0'); // Ensure two-digit minutes
                return `${year}-${month}-${day}T${hours}:${minutes}`;
            };

            // Set default values for date inputs
            startDateInput.val(formatDateTimeLocal(oneHourAgo));
            endDateInput.val(formatDateTimeLocal(now));
        }
    }
    initializeDateInputs(); // Call function to set default date values

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

    // ✅ Function to fetch transactions based on selected test ID
    function fetchTransactions(selectedTestId) {
        let transactionDropdown = $('#transaction_name'); // Select transaction dropdown
        transactionDropdown.empty().append(new Option("Select Transaction", "")); // Clear and reset dropdown

        if (selectedTestId) { // Proceed only if a test ID is selected
            $.ajax({
                url: '/get_transactions', // API endpoint to fetch transactions
                method: 'POST',
                data: { test_id: selectedTestId }, // Send selected test ID as data
                success: function(response) {
                    transactionDropdown.empty(); // Clear existing options
                    response.transactions.forEach(transaction => {
                        transactionDropdown.append(new Option(transaction, transaction)); // Add new options
                    });
                    transactionDropdown.trigger('change'); // Refresh Select2 dropdown
                }
            });
        }
    }

    // ✅ Event listener for Test ID dropdown change
    $('#test_id').on('change', function() {
        fetchTransactions($(this).val()); // Call function with selected test ID
    });

    // ✅ Function to fetch available servers for the selected application
    function fetchServers(app) {
        $.getJSON(`/servers?application=${app}`, function(data) { // Fetch servers via AJAX
            let serverDropdown = $('#server_names'); // Select server dropdown
            serverDropdown.empty().trigger("change"); // Clear existing options and refresh
            data.forEach(server => {
                let newOption = new Option(server.name, server.id, false, false);
                serverDropdown.append(newOption); // Add new options
            });
        });
    }

    // ✅ Event listener for Application dropdown change
    $('#application').change(function() {
        let app = $(this).val(); // Get selected application
        fetchServers(app); // Fetch corresponding servers

        // Reset Test ID and Transaction dropdowns
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

    // ✅ Function to fetch and update host health metrics
    function fetchHostHealth(applicationName, selectedServers) {
        $.ajax({
            url: "/get_host_health",
            type: "POST",
            contentType: "application/json",
            data: JSON.stringify({ applicationName, serverNames: selectedServers }),
            success: function(data) {
                document.getElementById("cpu_avg").textContent = data.summary.cpu_avg + "%";
                document.getElementById("memory_avg").textContent = data.summary.memory_avg + "%";
                document.getElementById("error_count").textContent = data.summary.total_errors;

                const honeycombContainer = document.getElementById("honeycomb");
                honeycombContainer.innerHTML = ""; // Clear existing server statuses

                data.health_data.forEach(server => {
                    const div = document.createElement("div");
                    div.classList.add("hex", server.status.toLowerCase()); // Add CSS class based on status
                    div.innerHTML = `
                        <strong>${server.server}</strong><br>
                        CPU: ${server.cpu_usage}%<br>
                        Mem: ${server.memory_usage}%<br>
                        Errors: ${server.error_count}
                    `;
                    div.setAttribute("data-tooltip", `${server.server} | CPU: ${server.cpu_usage}% | Mem: ${server.memory_usage}% | Errors: ${server.error_count}`);
                    honeycombContainer.appendChild(div); // Append server status to honeycomb layout
                });
            }
        });
    }

    // ✅ Event listener for Search button click
    $('#search').click(function() {
        $("#loading-spinner").show(); // Show loading spinner

        let application = $('#application').val(); // Get selected application
        let startDate = $('#start_date').val(); // Get start date
        let endDate = $('#end_date').val(); // Get end date
        let granularity = $('#granularity').val(); // Get granularity value
        let selectedServers = $('#server_names').val() || []; // Get selected servers

        if (!selectedServers.length) { // If no servers selected, select all
            selectedServers = $("#server_names option").map(function() { return $(this).val(); }).get();
        }

        fetchHostHealth(application, selectedServers); // Fetch host health data

        // AJAX request to fetch Splunk data
        $.ajax({
            url: "/fetch_splunk_data",
            type: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ application, start_date: startDate, end_date: endDate, granularity }),
            success: function(response) {
                console.log("API Response:", response); // Log API response for debugging
                // Process response data...
            },
            complete: function() {
                $("#loading-spinner").hide(); // Hide loading spinner after request completes
            }
        });
    });
});


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
