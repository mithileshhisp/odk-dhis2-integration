import requests
import logging
from datetime import datetime
import time
import sys

from dotenv import load_dotenv
import os
load_dotenv()

from constants import LOG_FILE_ANALYTICS

# ============================================================
# CONFIGURATION
# ============================================================

#DHIS2_BASE_URL = "http://115.124.111.208/mh"
#USERNAME = "YOUR_USERNAME"
#PASSWORD = "YOUR_PASSWORD"

#ANALYTICS_URL = f"{DHIS2_BASE_URL}/api/resourceTables/analytics"

DHIS2_API_URL = os.getenv("DHIS2_API_URL")
DHIS2_USER = os.getenv("DHIS2_USER")
DHIS2_POST_PASSWORD = os.getenv("DHIS2_PASSWORD")

session_dhis2 = requests.Session()
session_dhis2.auth = (DHIS2_USER, DHIS2_POST_PASSWORD)

ANALYTICS_URL = f"{DHIS2_API_URL}/resourceTables/analytics"

# How often to check the job status
POLL_INTERVAL = 10  # seconds

# Maximum time to wait for analytics
#MAX_WAIT_TIME = 1800  # 30 minutes

MAX_WAIT_TIME = 14400  # 4 hours

#CONTINUOUS lastYears=0

#ANNUAL lastYears=1

#FULL Full update
'''

| Requirement            | Parameters         |
| ---------------------- | ------------------ |
| Full/default analytics | `{}`               |
| Last 1 year            | `{"lastYears": 1}` |
| Last 3 years           | `{"lastYears": 3}` |
| Continuous/latest      | `{"lastYears": 0}` |
'''

# ============================================================
# LOGGING
# ============================================================

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

# ============================================================
# START ANALYTICS JOB
# ============================================================

def start_analytics():

    '''
    params = {
        "skipResourceTables": "true",
        "lastYears": 3
    }
    '''
    #Full/default analytics
    params = {}

    try:

        logging.info("Starting DHIS2 Analytics Table generation...")

        print("--------------------------------------------------")
        print("Starting DHIS2 Analytics Table generation...")
        print("--------------------------------------------------")
        print(f"ANALYTICS_URL --  {ANALYTICS_URL}")

        '''
        response = requests.post(
            ANALYTICS_URL,
            params=params,
            auth=(USERNAME, PASSWORD),
            timeout=300
        )
        '''

        response = session_dhis2.post(
            ANALYTICS_URL,
            params=params,
            timeout=300
        )

        logging.info(
            "Analytics API HTTP status: %s",
            response.status_code
        )

        if response.status_code != 200:

            logging.error(
                "Failed to start Analytics. HTTP %s - %s",
                response.status_code,
                response.text
            )

            print(
                f"ERROR: Failed to start Analytics. "
                f"HTTP {response.status_code}"
            )

            print(response.text)

            return None

        data = response.json()

        logging.info(
            "Analytics API response: %s",
            data
        )

        # ----------------------------------------------------
        # Get Job ID
        # ----------------------------------------------------

        job_response = data.get("response", {})

        job_id = job_response.get("id")

        job_status = job_response.get("jobStatus")

        if not job_id:

            logging.error(
                "Analytics started but no job ID was returned."
            )

            print("ERROR: No Analytics job ID returned.")

            return None

        print()
        print("Analytics job started successfully.")
        print(f"Job ID     : {job_id}")
        print(f"Job Status : {job_status}")
        print()

        logging.info(
            "Analytics job started. Job ID: %s, Status: %s",
            job_id,
            job_status
        )

        return job_id

    except requests.exceptions.Timeout:

        logging.error(
            "Timeout while starting Analytics job."
        )

        print("ERROR: Timeout while starting Analytics job.")

        return None

    except requests.exceptions.RequestException as e:

        logging.error(
            "Request error while starting Analytics: %s",
            e
        )

        print(f"ERROR: {e}")

        return None

    except Exception as e:

        logging.exception(
            "Unexpected error while starting Analytics."
        )

        print(f"ERROR: {e}")

        return None


# ============================================================
# CHECK ANALYTICS JOB STATUS
# ============================================================

def check_analytics_status(job_id):

    status_url = (
        f"{DHIS2_API_URL}/system/tasks/"
        f"ANALYTICS_TABLE/{job_id}"
    )

    try:

        response = session_dhis2.get(
            status_url,
            timeout=60
        )

        print(
            f"HTTP {response.status_code} | "
            f"{status_url}",
            flush=True
        )

        if response.status_code != 200:

            logging.error(
                "Unable to check Analytics status. "
                "HTTP %s - %s",
                response.status_code,
                response.text
            )

            print(
                f"Unable to check job status. "
                f"HTTP {response.status_code}",
                flush=True
            )

            print(
                f"Response: {response.text}",
                flush=True
            )

            return None

        data = response.json()

        logging.info(
            "Analytics job status response: %s",
            data
        )

        # ====================================================
        # DHIS2 returns a LIST
        # ====================================================

        if isinstance(data, list):

            if len(data) == 0:

                return {
                    "completed": False,
                    "failed": False,
                    "message": "No task notification returned",
                    "level": "INFO",
                    "raw": data
                }

            # ------------------------------------------------
            # Check ALL notifications
            # ------------------------------------------------

            for task in data:

                if not isinstance(task, dict):
                    continue

                completed = task.get("completed")

                level = str(
                    task.get("level", "")
                ).upper()

                message = task.get(
                    "message",
                    ""
                )

                # --------------------------------------------
                # COMPLETED
                # --------------------------------------------

                if completed is True:

                    return {
                        "completed": True,
                        "failed": False,
                        "message": message,
                        "level": level,
                        "raw": data
                    }

                # --------------------------------------------
                # FAILED
                # --------------------------------------------

                if level in [
                    "ERROR",
                    "FAILED"
                ]:

                    return {
                        "completed": False,
                        "failed": True,
                        "message": message,
                        "level": level,
                        "raw": data
                    }

            # ------------------------------------------------
            # Still running
            # ------------------------------------------------

            latest = data[-1]

            if isinstance(latest, dict):

                return {
                    "completed": False,
                    "failed": False,
                    "message": latest.get(
                        "message",
                        ""
                    ),
                    "level": latest.get(
                        "level",
                        ""
                    ),
                    "raw": data
                }

        # ====================================================
        # Unexpected response
        # ====================================================

        logging.warning(
            "Unexpected Analytics status response: %s",
            data
        )

        return {
            "completed": False,
            "failed": False,
            "message": "Unexpected response structure",
            "level": "WARNING",
            "raw": data
        }

    except requests.exceptions.RequestException as e:

        logging.error(
            "Error checking Analytics job status: %s",
            e
        )

        print(
            f"Error checking Analytics job status: {e}",
            flush=True
        )

        return None

    except Exception as e:

        logging.exception(
            "Unexpected error checking Analytics status."
        )

        print(
            f"ERROR: {e}",
            flush=True
        )

        return None


# ============================================================
# WAIT FOR ANALYTICS TO COMPLETE
# ============================================================

def wait_for_analytics(job_id):

    print()
    print(
        "Waiting for Analytics job to complete...",
        flush=True
    )
    print()

    logging.info(
        "Waiting for Analytics job %s to complete.",
        job_id
    )

    start_time = time.time()

    while True:

        # ====================================================
        # Maximum wait time
        # ====================================================

        elapsed_time = time.time() - start_time

        if elapsed_time >= MAX_WAIT_TIME:

            logging.error(
                "Analytics job %s exceeded maximum wait time.",
                job_id
            )

            print()
            print(
                f"ERROR: Analytics job exceeded "
                f"{MAX_WAIT_TIME / 60:.0f} minutes.",
                flush=True
            )

            return False

        # ====================================================
        # Check status
        # ====================================================

        result = check_analytics_status(job_id)

        # ----------------------------------------------------
        # Could not get status
        # ----------------------------------------------------

        if result is None:

            print(
                "Could not retrieve job status.",
                flush=True
            )

            print(
                f"Retrying in {POLL_INTERVAL} seconds...",
                flush=True
            )

            time.sleep(POLL_INTERVAL)

            continue

        # ====================================================
        # Get values
        # ====================================================

        completed = result.get(
            "completed",
            False
        )

        failed = result.get(
            "failed",
            False
        )

        message = result.get(
            "message",
            ""
        )

        level = result.get(
            "level",
            ""
        )

        elapsed_minutes = elapsed_time / 60

        # ====================================================
        # PRINT
        # ====================================================

        print(
            f"Analytics | "
            f"Completed: {completed} | "
            f"Failed: {failed} | "
            f"Level: {level} | "
            f"Elapsed: {elapsed_minutes:.1f} min",
            flush=True
        )

        if message:

            print(
                f"Message: {message}",
                flush=True
            )

        logging.info(
            "Analytics job %s | "
            "completed=%s | "
            "failed=%s | "
            "level=%s | "
            "message=%s",
            job_id,
            completed,
            failed,
            level,
            message
        )

        # ====================================================
        # COMPLETED
        # ====================================================

        if completed is True:

            print()
            print(
                "==================================================",
                flush=True
            )
            print(
                "Analytics Table generation COMPLETED successfully.",
                flush=True
            )
            print(
                "==================================================",
                flush=True
            )

            logging.info(
                "Analytics job %s completed successfully.",
                job_id
            )

            return True

        # ====================================================
        # FAILED
        # ====================================================

        if failed is True:

            print()
            print(
                "==================================================",
                flush=True
            )
            print(
                "Analytics Table generation FAILED.",
                flush=True
            )
            print(
                f"Message: {message}",
                flush=True
            )
            print(
                "==================================================",
                flush=True
            )

            logging.error(
                "Analytics job %s failed: %s",
                job_id,
                message
            )

            return False

        # ====================================================
        # WAIT
        # ====================================================

        time.sleep(POLL_INTERVAL)
# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print()
    print("==================================================")
    print("       DHIS2 ANALYTICS TABLE GENERATION")
    print("==================================================")
    print()

    logging.info("---------------------------------------------")
    logging.info("Analytics script started.")
    logging.info("---------------------------------------------")

    # --------------------------------------------------------
    # STEP 1: Start Analytics
    # --------------------------------------------------------

    job_id = start_analytics()

    if not job_id:

        print()
        print("Analytics job could not be started.")

        logging.error(
            "Analytics script stopped because "
            "the job could not be started."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # STEP 2: Wait for completion
    # --------------------------------------------------------

    success = wait_for_analytics(job_id)

    # --------------------------------------------------------
    # STEP 3: Final result
    # --------------------------------------------------------

    if success:

        logging.info(
            "Analytics script completed successfully."
        )

        print()
        print("Analytics process finished successfully.")
        print()

        sys.exit(0)

    else:

        logging.error(
            "Analytics script failed."
        )

        print()
        print("Analytics process failed.")
        print()

        sys.exit(1)    