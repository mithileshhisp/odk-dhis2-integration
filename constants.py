# constants.py

from datetime import datetime

# change url as on 03/11/2025
#https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health_mp.svc/Submissions?$filter=__system/submissionDate ge 2025-11-01
#https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health_mp.svc/Submissions?$filter=__system/submissionDate ge 2025-11-01
ODK_API_URL = "https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health_mp.svc/Submissions"

# before 03/11/2025
#ODK_API_URL = "https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health.svc/Submissions"
# ODK_API_URL = "https://odk.nipi-cure.org/v1/projects/9/forms/dss_health.svc/Submissions?$filter=__system/submissionDate ge 2024-02-01 and __system/submissionDate le 2024-02-0"
#DHIS2_API_URL = "http://172.105.253.84:8665/odk_nipi/api"
#DHIS2_API_URL =  "http://49.50.97.167:8665/odk_nipi/api"
DHIS2_API_URL =  "http://dss.nipi-cure.org:8665/odk_nipi/api"

#ODK_AUTH = ("*****", "*******")
ODK_AUTH = ("*****", "*******")
DHIS2_AUTH = ("*****", "*******")
#DHIS2_AUTH = ("*****", "*******")

#LOG_FILE = datetime.now().strftime("%Y-%m-%d") + "_dss_child_health_integration_missing_patient.log"
LOG_FILE = datetime.now().strftime("%Y-%m-%d") + "_dss_child_health_integration.log"