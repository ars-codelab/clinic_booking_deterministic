import streamlit as st
import json
import requests
import base64
from datetime import datetime, timedelta
import pytz

# --- Page Configuration ---
st.set_page_config(
    page_title="ABC Clinic Reservation",
    page_icon="🏥",
    layout="centered",
)

# --- GitHub API Functions ---
def update_github_file(repo_name, token, file_path, content_dict):
    """Updates or creates a file in a GitHub repository."""
    try:
        api_url = f"https://api.github.com/repos/{repo_name}/contents/{file_path}"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}

        # Try to get the file first to get its SHA.
        # If it doesn't exist, we'll create it.
        try:
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            current_sha = response.json()['sha']
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                current_sha = None # File doesn't exist, we will create it.
            else:
                raise # Re-raise other HTTP errors.

        json_string = json.dumps(content_dict, indent=4, ensure_ascii=False)
        content_base64 = base64.b64encode(json_string.encode('utf-8')).decode('utf-8')

        payload = {
            "message": f"Update config for {content_dict['patient_name']} on {content_dict['request_date']}",
            "content": content_base64,
        }
        # Add SHA only if we are updating an existing file.
        if current_sha:
            payload['sha'] = current_sha

        update_response = requests.put(api_url, headers=headers, json=payload)
        update_response.raise_for_status()
        return True, "Successfully saved configuration."
    except Exception as e:
        return False, f"An error occurred: {e}"

def trigger_github_action(repo_name, token, workflow_id):
    """Triggers a GitHub Actions workflow dispatch."""
    try:
        api_url = f"https://api.github.com/repos/{repo_name}/actions/workflows/{workflow_id}/dispatches"
        headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
        payload = {"ref": "main"}
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        return True, "Successfully triggered the reservation bot!"
    except Exception as e:
        return False, f"Error triggering bot: {e}"


# --- Main App ---
st.title("🏥 XXX Clinic Reservation")
st.markdown("Use this form to set up the patient and time preferences for the automatic booking.")


with st.form("reservation_form"):
    st.header("1. Select Patient and Symptoms")
    # Since I have 2 kids, I prefer to preconfigure their details so it's easier for us to schedule the bookings
    patient_name = st.selectbox("Select Patient", ('Patient 1','Patient 2'))
    symptoms = st.text_area("Symptoms (症状)")

    st.header("2. Choose Appointment Time")
    time_options = [
        "9:00 - 9:30", "9:30 - 10:00", "10:00 - 10:30", "10:30 - 11:00",
        "11:00 - 11:30", "11:30 - 12:00", "13:10 - 13:30", "13:30 - 14:00",
        "14:00 - 14:30", "14:30 - 15:00", "15:00 - 15:30", "15:30 - 16:00",
        "16:00 - 16:30", "16:30 - 17:00",
    ]
    preferred_time_ranges = st.multiselect("Select Preferred Time Slot(s)", options=time_options)

    st.header("3. Select When to Run")
    run_option = st.radio(
        "When should the bot run?",
        ("Schedule for 5:58 AM Tomorrow", "Run Now"),
        horizontal=True,
    )

    submitted = st.form_submit_button("Submit Request")

    if submitted:
        if not symptoms or not preferred_time_ranges:
            st.error("Symptoms and at least one Preferred Time Slot are required.")
        else:
            github_repo = st.secrets.get("GITHUB_REPO")
            github_token = st.secrets.get("GITHUB_TOKEN")
            patient_prefix = 'Patient1' if patient_name == 'Patient 1' else 'Patient2'
            clinic_username = st.secrets.get(f"{patient_prefix}_USERNAME")
            clinic_password = st.secrets.get(f"{patient_prefix}_PASSWORD")

            if not all([github_repo, github_token, clinic_username, clinic_password]):
                st.error(f"Required secrets for {patient_name} or GitHub are missing.")
            else:
                # Determine the request date based on the user's choice
                jst_tz = pytz.timezone('Asia/Tokyo')
                if run_option == "Schedule for 5:58 AM Tomorrow":
                    request_date = datetime.now(jst_tz) + timedelta(days=1)
                else: # "Run Now"
                    request_date = datetime.now(jst_tz)

                config_data = {
                    "request_date": request_date.strftime('%Y-%m-%d'),
                    "patient_name": patient_name,
                    "symptoms": symptoms,
                    "preferred_time_ranges": preferred_time_ranges,
                    "credentials": {"username": clinic_username, "password": clinic_password}
                }

                with st.spinner("Saving configuration and processing request..."):
                    # Step 1: Always update the config file
                    update_ok, update_msg = update_github_file(github_repo, github_token, "config.json", config_data)

                    if not update_ok:
                        st.error(update_msg)
                    else:
                        st.info(update_msg)
                        # Step 2: If "Run Now" was selected, trigger the workflow
                        if run_option == "Run Now":
                            trigger_ok, trigger_msg = trigger_github_action(github_repo, github_token, "main.yml")
                            if trigger_ok:
                                st.success(trigger_msg + " Check the 'Actions' tab in your GitHub repo for progress.")
                            else:
                                st.error(trigger_msg)
                        else:
                            st.success("Configuration saved. The bot is scheduled to run tomorrow morning.")
