import requests
import logging
from datetime import datetime
from dotenv import load_dotenv
import os
load_dotenv()

from constants import LOG_FILE_ANALYTICS

DHIS2_API_URL = os.getenv("DHIS2_API_URL")
DHIS2_USER = os.getenv("DHIS2_USER")
DHIS2_POST_PASSWORD = os.getenv("DHIS2_PASSWORD")

session_dhis2 = requests.Session()
session_dhis2.auth = (DHIS2_USER, DHIS2_POST_PASSWORD)

dhis2_analytics_url = f"{DHIS2_API_URL}/resourceTables/analytics"


LOG_DIR = "logs"
#os.makedirs(LOG_DIR, exist_ok=True)

os.makedirs(LOG_DIR, exist_ok=True)
assert LOG_DIR != "/" and LOG_DIR != "" #### Never delete outside log folder.

# Create unique log filename
#log_filename = f"log_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
log_filename = LOG_FILE_ANALYTICS
#log_filename = f"{LOG_FILE}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log"
log_path = os.path.join(LOG_DIR, log_filename)

logging.basicConfig(
    filename=log_path,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#URL = "http://115.124.111.208/mh/api/resourceTables/analytics"
#USERNAME = "USERNAME"
#PASSWORD = "PASSWORD"

params = {
    "skipResourceTables": "true",
    "lastYears": "3"
}

try:
    logging.info("Analytics table generation Starting...")

    #logging.info("Starting resource table analytics generation...")
    print("Analytics table generation Starting...")

    '''
    response = requests.post(
        URL,
        params=params,
        auth=(USERNAME, PASSWORD),
        timeout=1800
    )
    '''
    response = session_dhis2.post(
        dhis2_analytics_url,
        params=params,
        headers={
            "Content-Type": "application/json"
        }
    )


    if response.status_code == 200:

        data = response.json()

        job_id = data.get("response", {}).get("id")
        job_status = data.get("response", {}).get("jobStatus")

        logging.info(
            "Analytics table generation initiated successfully. "
            "HTTP %s, Job ID: %s, Job Status: %s",
            response.status_code,
            job_id,
            job_status
        )

        print(
            f"Analytics table generation initiated successfully. "
            f"HTTP {response.status_code}, Job ID: {job_id}"
        )

    else:

        logging.error(
            "Analytics table generation failed. HTTP %s - Response: %s",
            response.status_code,
            response.text
        )

        print(
            f"Analytics table generation failed. "
            f"HTTP {response.status_code}"
        )

except requests.exceptions.Timeout:
    logging.error("Analytics table generation request timed out.")
    print("Request timed out.")

except requests.exceptions.RequestException as e:
    logging.error("Analytics table generation request failed: %s", e)
    print(f"Request failed: {e}")

except Exception as e:
    logging.exception("Unexpected error: %s", e)
    print(f"Unexpected error: {e}")