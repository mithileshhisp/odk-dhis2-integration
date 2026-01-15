# constants.py

from datetime import datetime

ODK_API_URL = "https://odk.nipi-cure.org/v1/projects/5/forms/Anaemia.svc/Submissions"
#DHIS2_API_URL = "http://172.105.253.84:8665/odk_nipi/api"
#DHIS2_API_URL =  "http://49.50.97.167:8665/odk_nipi/api"
DHIS2_API_URL =  "http://dss.nipi-cure.org:8665/odk_nipi/api"

#ODK_AUTH = ("******", "*******")
ODK_AUTH = ("******", "*******")
DHIS2_AUTH = ("******", "*******")
#DHIS2_AUTH = ("******", "*******")

LOG_FILE = datetime.now().strftime("%Y-%m-%d") + "_integration_anemia.log"
LOG_FILE_EVENT_ERROR_LOG = datetime.now().strftime("%Y-%m-%d") + "_event_integration_anemia_error_log.txt"