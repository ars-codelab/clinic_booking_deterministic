# ABC Clinic Booking Bot 🤖🏥

This project demonstrates a simple Python webrawler (running via github actions) and a streamlit app to automate booking for a specific clinic. 
While the Streamlit app can be used as-is, the crawler.py is custom coded for a specific clinic and will need to be changed based on your desired clinic's webpage. Since Github Actions (free tier) is highly unreliable for executing the script at a pre-defined time (e.g. 5:58 AM), we also use cron-job.org, a free service to trigger the Github action.

---


## ✨ Features

* **Automated Booking:** Logs in and navigates the clinic's website to book an appointment.
* **Web-Based UI:** A simple Streamlit app allows for easy configuration of patient details and preferred time slots.
* **Secure Credential Management:** Uses Streamlit and GitHub secrets to securely store all sensitive login information.
* **High-Precision Scheduling:** Leverages an external cron job service to trigger the booking bot at an exact time, bypassing the limitations of the standard GitHub Actions scheduler.
* **Conditional Execution:** The bot only runs the full booking process if a request has been made via the Streamlit app for that specific day, making the daily job efficient.

---

## ⚙️ Setup and Installation

Follow these three main steps to set up the entire system.

### 1. GitHub Repository Setup

First, you need to set up your GitHub repository with the correct files and secrets.

**A. Create a Private Repository**

1.  Create a new **private** GitHub repository for this project.
2.  Clone the repository to your local machine and add the following files:
    * `streamlit_app.py`
    * `crawler.py`
    * `.github/workflows/main.yml`
    * `requirements.txt`
    * `.gitignore` (optional, but recommended)

**B. Create the `config.json` File**

You need to create an initial `config.json` file in the root of your repository so the Streamlit app can update it later. This can be blank to start.

1.  In your project folder, create a new file named `config.json`.
2.  Add empty JSON brackets `{}` to the file and save it.
3.  Commit and push this file to your GitHub repository.

**C. Set Up GitHub Secrets**

The system requires one secret to be set in your GitHub repository settings.

1.  Generate a **Personal Access Token (PAT)** on GitHub.
    * Go to **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**.
    * Click **"Generate new token"**.
    * Give it a name (e.g., `clinic-bot-token`) and in the **"Select scopes"** section, check the box for **`repo`**.
    * Generate the token and **copy it immediately**.
2.  In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**.
3.  Click **"New repository secret"** and create the following secret:
    * **Name:** `GITHUB_TOKEN`
    * **Value:** Paste the Personal Access Token you just copied.

---

### 2. Streamlit Cloud Deployment

Next, deploy the user interface on Streamlit's free hosting platform.

1.  Sign up or log in to [Streamlit Community Cloud](https://share.streamlit.io/).
2.  Click **"New app"** and choose to deploy from an existing repository.
3.  Select your repository and the `main` branch.
4.  The main application file is `streamlit_app.py`.
5.  Before deploying, go to the **"Advanced settings"** and add the following secrets. These are crucial for the app to function.

    * `GITHUB_REPO`: Your repository name in `owner/repo-name` format (e.g., `ars-codelab/clinic_booking_deterministic`).
    * `GITHUB_TOKEN`: The same Personal Access Token you created in the previous step.
    * `PATIENT1_USERNAME`: The clinic login ID for Patient1.
    * `PATIENT1_PASSWORD`: The clinic password for Patient1.
    * `PATIENT2_USERNAME`: The clinic login ID for Patient2.
    * `PATIENT2_PASSWORD`: The clinic password for Patient2.

6.  Click **"Deploy!"**.

---

### 3. External Cron Job Setup (cron-job.org)

This is the final one-time setup step to ensure the bot runs precisely at 5:58 AM JST every day.

1.  Go to [https://cron-job.org/en/](https://cron-job.org/en/) and click **"CREATE CRONJOB"**.
2.  Fill out the form with the following details:
    * **Title:** `ABC Clinic Bot`
    * **URL:** `https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/actions/workflows/main.yml/dispatches` (replace with your own details).
    * **Request Method:** Change to `POST`.
    * Click the **"Advanced"** toggle to show more options.
    * **Custom POST-values (body):** `{"ref": "main"}`
    * **Custom Headers:** Add the following three headers:
        * `Accept`: `application/vnd.github.v3+json`
        * `Authorization`: `token YOUR_GITHUB_TOKEN` (use your PAT).
        * `User-Agent`: `Clinic-Cronjob`
    * **Schedule:**
        * Select **"User-defined"**.
        * Set the schedule to run every day at `05:58` (5th hour, 58th minute).
3.  Complete the CAPTCHA and click **"CREATE CRONJOB"**.

---

## 🚀 How to Use

Your setup is now complete. To book an appointment for tomorrow, follow these simple steps:

1.  The day before you want an appointment, open your deployed Streamlit web application.
2.  Select the patient's name from the dropdown.
3.  Enter their symptoms.
4.  Choose one or more preferred 30-minute time slots.
5.  Click **"Save Configuration for Tomorrow"**.

The system is now armed. The external cron job will trigger the booking bot at 5:58 AM JST the next morning, and the bot will attempt to book an appointment based on the configuration you saved.

---

