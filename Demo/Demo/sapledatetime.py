import streamlit as st
from streamlit_js_eval import streamlit_js_eval

st.markdown("""
    <link rel="stylesheet" 
          href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" 
          href="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datetimepicker/4.17.47/css/bootstrap-datetimepicker.min.css">
    
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/moment.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/bootstrap-datetimepicker/4.17.47/js/bootstrap-datetimepicker.min.js"></script>

    <div class="container">
        <label for="datetimePicker">📅 Select Date & Time:</label>
        <input type="text" id="datetimePicker" class="form-control"
               placeholder="Pick a date & time" style="text-align: center;"/>
    </div>
    
    <script>
        $(document).ready(function(){
            $('#datetimePicker').datetimepicker({
                format: 'YYYY-MM-DD HH:mm',
                showTodayButton: true
            }).on('dp.change', function(e) {
                var datetime = $('#datetimePicker').val();
                document.getElementById("selectedDateTime").value = datetime;
            });
        });
    </script>

    <input type="hidden" id="selectedDateTime">
""", unsafe_allow_html=True)

# Capture JavaScript-selected datetime
selected_datetime = streamlit_js_eval(js_expressions="document.getElementById('selectedDateTime').value")

st.write("### 📅 You picked:", selected_datetime)
