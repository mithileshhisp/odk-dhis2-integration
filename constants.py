# constants.py

from datetime import datetime

#Rajasthan https://odk.nipi-cure.org/v1/projects/1/forms/HBNCC_VISIT_M25.svc


#Odisha https://odk.nipi-cure.org/v1/projects/29/forms/HBNCC_VISIT_M25.svc

#https://odk.nipi-cure.org/v1/projects/1/forms/HBNCC_VISIT_M25.svc/Submissions?$filter=__system/submissionDate ge 2026-06-20

# change url as on 03/11/2025

#https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health_mp.svc/Submissions?$filter=__system/submissionDate ge 2026-07-14 and __system/submissionDate lt 2026-09-01
#https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health_mp.svc/Submissions?$filter=__system/submissionDate ge 2025-11-01
#https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health_mp.svc/Submissions?$filter=__system/submissionDate ge 2025-11-01
ODK_API_URL = "https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health_mp.svc/Submissions"

# before 03/11/2025
#ODK_API_URL = "https://odk.nipi-cure.org/v1/projects/9/forms/dss_child_health.svc/Submissions"
# ODK_API_URL = "https://odk.nipi-cure.org/v1/projects/9/forms/dss_health.svc/Submissions?$filter=__system/submissionDate ge 2024-02-01 and __system/submissionDate le 2024-02-0"
#DHIS2_API_URL = "http://172.105.253.84:8665/odk_nipi/api"
#DHIS2_API_URL =  "http://49.50.97.167:8665/odk_nipi/api"
DHIS2_API_URL =  "http://dss.nipi-cure.org:8665/odk_nipi/api"

#ODK_AUTH = ("sourabh.bhardwaj@hispindia.org", "h!spD@v123")
ODK_AUTH = ("dss.nipi@hispindia.org", "********")
DHIS2_AUTH = ("*******", "******")
#DHIS2_AUTH = ("*****", "******")

#LOG_FILE = datetime.now().strftime("%Y-%m-%d") + "_dss_child_health_integration_missing_patient.log"
LOG_FILE_RAJASTHAN = datetime.now().strftime("%Y-%m-%d") + "_nipi_odk_dhis2_ssbsk_integration_rajasthan.log"
LOG_FILE_ODISHA = datetime.now().strftime("%Y-%m-%d") + "_nipi_odk_dhis2_ssbsk_integration_odisha.log"

LOG_FILE_ANALYTICS = datetime.now().strftime("%Y-%m-%d") + "_analytics_tables.log"