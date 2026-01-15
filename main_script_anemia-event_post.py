# main.py
from concurrent.futures import ThreadPoolExecutor
import requests
import json
from datetime import datetime
from constants import ODK_AUTH,ODK_API_URL,DHIS2_API_URL,DHIS2_AUTH, LOG_FILE_EVENT_ERROR_LOG

from utils import configure_logging, log_info, log_error, get_dhis2_orgunit_uid_by_block_district,data_value_exists_in_dhis2,sendEmail


#DHIS2_API_POST_URL = "http://172.105.253.84:8665/odk_nipi/api"
#DHIS2_API_POST_URL = "http://49.50.97.167:8665/odk_nipi/api"
#DHIS2_AUTH_POST = ("******", "*******")

DHIS2_API_POST_URL =  "http://dss.nipi-cure.org:8665/odk_nipi/api"
DHIS2_AUTH_POST = ("******", "*******")

session_post = requests.Session()
session_post.auth = DHIS2_AUTH_POST

# Get the current date and time
configure_logging()
current_time_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
print( f"pushing Anemia event Program data into DHIS2 start . { current_time_end }" )
log_info(f"pushing Anemia event Program data into DHIS2 start . { current_time_end }")

def fetch_odk_data():
    try:
        today_date = datetime.now().strftime("%Y-%m-%d")
        updated_odk_api_url = f"{ODK_API_URL}?$filter=__system/submissionDate ge {today_date}"
        #updated_odk_api_url = f"{ODK_API_URL}?$filter=__system/submissionDate ge 2025-11-20"
        print("data fetching for: ",updated_odk_api_url)
        response = requests.get(updated_odk_api_url, auth=ODK_AUTH)
        
        if response.status_code == 200:
            log_info(f"ODK data fetched successfully.from url {updated_odk_api_url}")
            print(f"ODK data fetched successfully.")
            return response.json()["value"]
        else:
            log_error("Failed to fetch ODK data.")
            return []
    except Exception as e:
        log_error("An error occurred while fetching ODK data--", e)
        return []


def check_existing_event(session_post,event_id):
    #http://172.105.253.84:8665/odk_nipi/api/events.json?&skipPaging=true&dataElement=zkhndIoBYH7&filter=zkhndIoBYH7:like:d1b782c1-4d8c-4c3f-8faa-6aed9db64045
    #event_search_url = f"{event_push_endpoint}?orgUnit={orgUnitID}&ouMode=SELECTED&program={programID}&status=ACTIVE&skipPaging=true&filter={event_search_dataElement_uid}:eq:{BenCallID}"
    response = session_post.get(f"{DHIS2_API_URL}/events.json?&skipPaging=true", params={"dataElement": "zkhndIoBYH7", "filter": f"zkhndIoBYH7:like:{event_id}"})

    if response.status_code == 200:
        response_data = response.json()
        events = response_data.get('events', [])
        return events 
    else:
        return []

def push_to_dhis2(dhis2_events):
    try:
        for event in dhis2_events:
            response = requests.post(f"{DHIS2_API_URL}/events", json=event, auth=DHIS2_AUTH)
            # print("response--", response)
            if response.status_code != 200:
                log_error("Failed to create event in DHIS2 for: " + str(response.content))

        log_info("Events successfully pushed to DHIS2.")

    except Exception as e:
        log_error("An error occurred while pushing data to DHIS2: " + str(e))

def push_event_in_dhis2(session_post, event_payload, event_id, row, execution_date ):
    #
    try:
        event_post_url = f"{DHIS2_API_POST_URL}/events"
        response = session_post.post(event_post_url, data=json.dumps(event_payload), headers={"Content-Type": "application/json"})
        response.raise_for_status()
       
        imported_event_uid = response.json().get("response", {}).get("importSummaries", [])[0].get("reference")
        event_count = response.json().get("response", {}).get("importSummaries", [])[0].get("importCount",{}).get("imported")
        print(f"Events created successfully. row : {row} . with uuid : {event_id} .  Event Date : {execution_date}. Event count: {event_count}. imported event : {imported_event_uid}")
        log_info(f"Events created successfully.row : {row}. with uuid : {event_id} . Event Date : {execution_date}. Event count: {event_count}. imported event : {imported_event_uid}")
    except requests.RequestException as e:
        resp_msg=response.text
        ind=resp_msg.find('conflict')
        
        with open(LOG_FILE_EVENT_ERROR_LOG, 'a') as fail_record:
            fail_record.write(f'\ncurrent event_id: {event_id}. \n Error Message: {resp_msg[ind-1:]}\n')
            fail_record.write("----------------------------------------------------------------------------------------\n")

        print(f"Failed to create events. . row : {row} . Event Date : {execution_date}. Error: {response.text}")
        log_error(f"Failed to create events . row : {row}. with uuid : {event_id} . Event Date : {execution_date} .Status code: {response.status_code} . error details: {response.json()} .Error: {response.text}")


def main():
    
    try:
        #configure_logging()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            #configure_logging()
            odk_data = fetch_odk_data()
            for index, submission in enumerate(odk_data):

                block_name = submission["location_camp"]["block"]
                district_name = submission["location_camp"]["district"]
                print(f"data fetching for block_name : ", block_name)
                print(f"data fetching for district_name : ", district_name)
                orgunit_uid = get_dhis2_orgunit_uid_by_block_district(session_post, block_name, district_name)
                print(f"data fetching for orgunit_uid : ", orgunit_uid)
                if orgunit_uid:
                    # uuid:6f9d9577-90f6-4668-ae33-4bd0cadc7011
                    event_id = submission["__id"].split(":")[1]
                    print(f"data fetching for event_id : ", event_id)
                    temp_event_date = submission["location_camp"]["date_camp"]
                    print(f"data fetching for temp_event_date : ", temp_event_date)
                    #if not data_value_exists_in_dhis2(session_post,event_id):
                    existing_event = check_existing_event(session_post,event_id)
                    if not existing_event:
                        #print(f"for row { index +1}, Event with ID  {event_id} not exists in DHIS2. Adding. for orgunit_uid {orgunit_uid}, for date {temp_event_date}")
                        #log_info(f"for row { index +1}, Event with ID {event_id} not exists in DHIS2. Adding. for orgunit_uid {orgunit_uid}, for date {temp_event_date}")
                        # log_info("event---")
                        event_payload = {   
                        "eventDate": submission["location_camp"]["date_camp"],
                        "orgUnit": orgunit_uid,
                        "program": "OSZGBa7ap1d",
                        "dataValues": [
                            {"dataElement": "PuO8ZfalloM", "value": submission["location_camp"]["tested_at"]},
                            {"dataElement": "g5lnjsR2mi4", "value": submission["location_camp"]["camp_location"]},
                            {"dataElement": "QnK3KeJVLzN", "value": submission["location_camp"]["address"]},
                            {"dataElement": "qPPuaPj3wy9", "value": submission["Child_adult"]["name_p"]},
                            {"dataElement": "q2FWKpMyRSA", "value": submission["Child_adult"]["gender"]},
                            {"dataElement": "GoTBOz1huaK", "value": submission["Child_adult"]["preorlac"]},
                            {"dataElement": "kPSiW4ngmWO", "value": submission["Child_adult"]["result"]},
                            {"dataElement": "fTsT5tCMQR4", "value": submission["Child_adult"]["classify_all"]},
                            {"dataElement": "ZSsWwLEqGKk", "value": submission["Child_adult"]["weight_kg"]},
                            {"dataElement": "jWTOfbCiGMV", "value": submission["Child_adult"]["agegrp_text"]},
                            {"dataElement": "Bjh3nyIKHi3", "value": submission["Child_adult"]["preglact_text"]},
                            {"dataElement": "zkhndIoBYH7", "value": submission["__id"]}
                        ],
                    }
                        
                        executor.submit( push_event_in_dhis2, session_post, event_payload, event_id,index+1, submission["location_camp"]["date_camp"] )    
                    else:
                        print(f"for row { index +1 },Event with uuid: {event_id}, for date {temp_event_date} already exists in DHIS2 with EventId {existing_event[0]['event']}. Skipping.")
                        log_info(f"for row { index +1 }, Event with uuid: {event_id}, for date {temp_event_date} already exists in DHIS2 with EventId {existing_event[0]['event']}. Skipping.")
                else:
                    log_info(f"row { index +1} DHIS2 organization unit not found for block: {block_name} and parent: {district_name}. Skipping.")
                    print(f"row { index +1} DHIS2 organization unit not found for block:", block_name, "and parent:", district_name, "Skipping.")
    except Exception as e:
        log_error("An error occurred in the main process: " + str(e))


if __name__ == "__main__":
    main()

    current_time_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print( f"pushing Anemia event Program data into DHIS2 finished . { current_time_end }" )
    log_info(f"pushing Anemia event Program data into DHIS2 finished . { current_time_end }")
    sendEmail()
