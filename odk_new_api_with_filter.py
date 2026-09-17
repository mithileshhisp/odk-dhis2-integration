import requests


'''
GET /v1/projects/{projectId}/forms/{xmlFormId}.svc/Submissions?$filter=__system/submissionDate ge 2024-01-15T00:00:00.000Z and __system/submissionDate lt 2024-01-16T00:00:00.000Z
'''

'''
from pyodk.client import Client

client = Client().open()

day = "2024-01-15T00:00:00.000Z"
next_day = "2024-01-16T00:00:00.000Z"

f = f"(__system/submissionDate ge {day} and __system/submissionDate lt {next_day})"

subs = client.submissions.get_table(
    form_id="your_form_id",
    project_id=1,
    filter=f,
)
rows = subs["value"]

'''
# ============================================================
# CONFIGURATION
# ============================================================

ODK_BASE_URL = "https://odk.nipi-cure.org"
PROJECT_ID = 29
FORM_ID = "HBNCC_VISIT_M25"

USERNAME = "your_odk_username"
PASSWORD = "your_odk_password"


# ============================================================
# DATE RANGE
# ============================================================

day = "2024-01-15T00:00:00.000Z"
next_day = "2024-01-16T00:00:00.000Z"


# ============================================================
# ODATA FILTER
# ============================================================

odata_filter = (
    f"(__system/submissionDate ge {day} "
    f"and __system/submissionDate lt {next_day})"
)


# ============================================================
# API URL
# ============================================================

url = (
    f"{ODK_BASE_URL}/v1/projects/{PROJECT_ID}/forms/"
    f"{FORM_ID}.svc/Submissions"
)

params = {
    "$filter": odata_filter
}


# ============================================================
# GET SUBMISSIONS
# ============================================================

response = requests.get(
    url,
    params=params,
    auth=(USERNAME, PASSWORD),
    timeout=60
)

response.raise_for_status()

data = response.json()

rows = data.get("value", [])


# ============================================================
# RESULT
# ============================================================

print(f"Total submissions: {len(rows)}")

for row in rows:
    print(row)



## 2nd
import requests

url = (
    "https://odk.nipi-cure.org/v1/projects/29/forms/"
    "HBNCC_VISIT_M25.svc/Submissions"
)

day = "2026-08-17T00:00:00.000Z"
next_day = "2026-08-18T00:00:00.000Z"

params = {
    "$filter": (
        f"(__system/submissionDate ge {day} "
        f"and __system/submissionDate lt {next_day})"
    )
}

response = requests.get(
    url,
    params=params,
    auth=("YOUR_USERNAME", "YOUR_PASSWORD"),
    timeout=60
)

response.raise_for_status()

rows = response.json()["value"]

print("Total rows:", len(rows))

for row in rows:
    print(row)

## 3rd make the date dynamic
# 
#         
import requests
from datetime import datetime, timedelta, timezone


def get_odk_submissions_for_date(
    project_id,
    form_id,
    date_str,
    username,
    password
):
    """
    date_str format: YYYY-MM-DD
    """

    date = datetime.strptime(
        date_str,
        "%Y-%m-%d"
    ).replace(tzinfo=timezone.utc)

    next_date = date + timedelta(days=1)

    day = date.strftime("%Y-%m-%dT00:00:00.000Z")
    next_day = next_date.strftime("%Y-%m-%dT00:00:00.000Z")

    url = (
        f"https://odk.nipi-cure.org/v1/projects/"
        f"{project_id}/forms/{form_id}.svc/Submissions"
    )

    odata_filter = (
        f"(__system/submissionDate ge {day} "
        f"and __system/submissionDate lt {next_day})"
    )

    params = {
        "$filter": odata_filter
    }

    response = requests.get(
        url,
        params=params,
        auth=(username, password),
        timeout=60
    )

    response.raise_for_status()

    return response.json().get("value", [])


# Example
rows = get_odk_submissions_for_date(
    project_id=29,
    form_id="HBNCC_VISIT_M25",
    date_str="2026-08-17",
    username="YOUR_USERNAME",
    password="YOUR_PASSWORD"
)

print("Total submissions:", len(rows))

for row in rows:
    print(row)

##
#subs = client.submissions.get_table(...)
#rows = subs["value"]    