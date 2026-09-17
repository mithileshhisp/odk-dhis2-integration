# main.py
from concurrent.futures import ThreadPoolExecutor
import requests
import json
from datetime import datetime ,timedelta
from dotenv import load_dotenv
import os
#import certifi  ## for post data in hmis production certificate issue
#import urllib3
#urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

load_dotenv()

from constants import ODK_AUTH, ODK_API_URL, DHIS2_API_URL, DHIS2_AUTH
from utils import (
    configure_logging,
    log_info,
    log_error,
    get_dhis2_orgunit_uid_by_block_district,
    get_dhis2_orgunit_uid_by_nin,
    data_value_exists_in_dhis2, sendEmail, get_orgUnit_code_uid_dict
)

ODK_API_URL = os.getenv("ODK_API_URL")
ODK_USER = os.getenv("ODK_USER")
ODK_PASSWORD = os.getenv("ODK_PASSWORD")
ODK_FILTER_DATE = os.getenv("ODK_FILTER_DATE")

DHIS2_API_URL = os.getenv("DHIS2_API_URL")
DHIS2_USER = os.getenv("DHIS2_USER")
DHIS2_POST_PASSWORD = os.getenv("DHIS2_PASSWORD")

META_ATTRIBUTE_SSBSK_ORG_UNIT_CODE = os.getenv("META_ATTRIBUTE_SSBSK_ORG_UNIT_CODE")

org_unit_api_url = f"{DHIS2_API_URL}/organisationUnits"

session_dhis2 = requests.Session()
session_dhis2.auth = (DHIS2_USER, DHIS2_POST_PASSWORD)

session_odk = requests.Session()
#session_get.auth = (user, pwd)
session_odk.auth = (ODK_USER, ODK_PASSWORD)


def fetch_odk_data():
    try:
        
        #from datetime import datetime, timedelta

        today = datetime.now()
        one_day_before = today - timedelta(days=1)

        today_date = today.strftime("%Y-%m-%d")
        previous_date = one_day_before.strftime("%Y-%m-%d")
        
        #today_date = datetime.now().strftime("%Y-%m-%d")

        print(f"today_date:", today_date)
        print(f"previous_date:", previous_date)

        updated_odk_ssbsk_api_url = f"{ODK_API_URL}?$filter=__system/submissionDate ge {ODK_FILTER_DATE}"
       

        log_info(f"Data fetched from odk for date ge {today_date}, with url {updated_odk_ssbsk_api_url}")

        print(f"Data fetched for:", updated_odk_ssbsk_api_url)

        response = requests.get(updated_odk_ssbsk_api_url, auth=ODK_AUTH)
        response.raise_for_status()
        if response.status_code == 200:
            if response.json() and "value" in response.json():
                log_info(f"ODK data fetched successfully.")
                return response.json()["value"]
            else:
                print(f"Invalid or missing JSON content in the ODK response. { str(e)}")
                log_error(f"Invalid or missing JSON content in the ODK response. { str(e)}")
                return []
        else:
            print(f"Failed to fetch ODK data. Status code: {response.status_code} ")
            log_error(f"Failed to fetch ODK data. Status code: {response.status_code}")
            return []
    except Exception as e:
        print(f"An error occurred while fetching ODK data 1 . { str(e)}")
        log_error(f"An error occurred while fetching ODK data: { str(e)} ")
        return []

def remove_null_values(obj):
    if isinstance(obj, dict):
        return {key: remove_null_values(value) for key, value in obj.items() if value is not None and value != "null"}
    elif isinstance(obj, list):
        return [remove_null_values(item) for item in obj if item is not None and item != "null"]
    else:
        return obj


def assign_value_if_not_null(value):
    if value is not None and value != "null":
        return value
    else:
        return None


# ============================================================
# DATE convert this date 17-Aug-2026 to YYYY-MM-DD
# ============================================================
#formatted_date = datetime.strptime(date_str, "%d-%b-%Y").strftime("%Y-%m-%d")
def convert_date(value):

    if not value:
        return None

    value = value.strip()

    formats = [
        "%Y-%m-%d",
        "%d-%b-%Y",
        "%d-%m-%Y"
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                value,
                fmt
            ).strftime("%Y-%m-%d")

        except ValueError:
            continue

    raise ValueError(
        f"Unable to parse date: {value}"
    )


#dt_str = "2026-01-14T00:00:00.000+05:30"
#dt = datetime.fromisoformat(dt_str)
#date_str = dt.strftime("%Y-%m-%d")
#print(date_str)


def format_date_event_enrollment(date_str):
    try:
        #date_str = "14-01-26"
        #dt = datetime.strptime(date_str, "%d-%m-%y")
        #iso_date = dt.strftime("%Y-%m-%d")
        
        date_obj = datetime.fromisoformat(date_str)
        formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        return None

def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%y-%m-%d")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        return None

def format_date_yyyy_mm_dd(date_str):
    try:
        #date_str = "14-01-26"
        #dt = datetime.strptime(date_str, "%d-%m-%y")
        #iso_date = dt.strftime("%Y-%m-%d")
        
        date_obj = datetime.strptime(date_str, "%d-%m-%y")
        formatted_date = date_obj.strftime("%Y-%m-%d")
        return formatted_date
    except ValueError:
        return None

def convert_to_boolean(value):
    if value == "1":
        return "true"
    elif value == "0":
        return "false"
    else:
        return None


def transform_to_dhis2_events(odk_data, orgUnit_code_uid_dict):
    #tracker_payloads = []

        # Mapping of dg_sign values to DHIS2 data elements
    dg_sign_mapping = {
        1: "V424NzPgm8D",
        2: "OLLbXaLlWMw",
        3: "ZXC20iovUyp",
        4: "nsnmtedOgKZ",
        5: "EzV0hDPfQTx",
        6: "Y3rdOlr59B4",
        7: "kAUvsi9SlfQ",
        8: "G6N5q6UzUWC",
        9: "ohM686RSDjv",
        10: "ub63lErLLAN"
    }

    ecd_warning_mapping = {
    1: "nTLMtvM7bMy",
    2: "OzvNIJ6VUUy",
    3: "w9bSH9FUw2z",
    4: "VgErvzPrj2J",
    5: "kz47L5uIrZb",
    6: "eQaPR3Fwwrq",
    7: "I74dAY4BJwq",
    8: "Rk6RMYUEHwu",
    9: "KC3BYqgoGj4",
    10: "kGjSFNBM1Kl",
    11: "ggCZtTXgPvD",
    12: "rO4G67c4fQ2",
    13: "r2sSyin8hyT",
    14: "d3hwgAcTfzG",
    15: "uGb8FxbmT64",
    16: "LwZHgZO5hSK",
    17: "yi6fOSYWK8j",
    18: "FswaOwO5Z9l",
    19: "wtXP8I9OhTD",
    20: "uBzoNOzcy0C",
    21: "GYVIQSYshkh",
    22: "uBYNCdOTSBr",
    23: "u2nUZ3BRIlV",
    24: "EOE57y8bEaB",
    25: "PlBDb8udKzj",
    26: "zLaAWMhzwXN",
    27: "v955iHiiLjZ",
    28: "sPjyFAvHw4n",
    29: "CygMJg5JEsV",
    30: "hm5vKuOHasK",
    31: "ksufm81OroI",
    32: "ZmdBXsiqPZV",
    33: "gHr2obtk6SZ",
    34: "nHZp3Rgkjd4",
    35: "uIY9K58R0UK",
    36: "zuEJetG8g1k",
    37: "moDISYRwVUt",
    38: "iKLKGsW4q4a",
    39: "dSBthHyRktA",
    40: "maN0TXiKnXv"
    }


    feeding_mapping = {
        1: "wGRuhVlSBRR",
        2: "oETaln5QVJZ",
        3: "UaRvsomQLUU",
        4: "E5XV8idvaYf",
        5: "K6KBH2P8ov3"
    }
    
    for index, submission in enumerate(odk_data):
        # Ensure 'login_check1' and 'g_info' keys exist
        if 'grp_provider' not in submission:
            print(f"Missing 'grp_provider' in submission: {submission}")
            log_error(f"Missing 'grp_provider' in submission: {submission}")
            continue
        #print(f"ODK data --  {odk_data}")
        global total_child_count
        total_child_count =  index + 1
        #execution_date = submission["assessment_date"] ## 17-Aug-2026
        execution_date = datetime.strptime(submission["assessment_date"], "%d-%b-%Y").strftime("%Y-%m-%d")

        block_code = submission["grp_provider"]["block_code"]
        district_code  = submission["grp_provider"]["district_code"]
        facility_code = submission["grp_provider"]["facility_code"]

        print("block_code --", block_code, "--", district_code, "--", facility_code )

        facility_nin = submission["grp_provider"]["facility_code"]
        # orgunit_uid = get_dhis2_orgunit_uid_by_block_district(block_name, district_name,facility_name)
        temp_class_child_uid = str(submission["class_child_uid"])

        print(f"ODK data Sl.No. {index+1}. class_child_uid {temp_class_child_uid}")
        log_info(f"ODK data Sl.No. {index+1}. class_child_uid {temp_class_child_uid}")

        #odk_cdate = format_date_event_enrollment(submission["g_info"]["cdate"])
        #odk_f_cdate = format_date_yyyy_mm_dd(submission["f_cdate"])
        #print(f"ODK cdate {index+1}. cdate {odk_cdate}, ODK f_cdate . {odk_f_cdate}")
        
        district_org_unit = orgUnit_code_uid_dict.get(block_code)
        if district_org_unit:
            district_uid = district_org_unit["uid"]
            district_name = district_org_unit["name"]   

        block_org_unit = orgUnit_code_uid_dict.get(block_code)
        if block_org_unit:
            block_uid = block_org_unit["uid"]
            block_name = block_org_unit["name"]   


        #orgunit_uid = get_dhis2_orgunit_uid_by_nin(session_post,DHIS2_API_POST_URL,facility_nin)

        facility_nin_org_unit = orgUnit_code_uid_dict.get(facility_nin)
        if facility_nin_org_unit:
            orgunit_uid = facility_nin_org_unit["uid"]
            facility_nin_org_unit_name = facility_nin_org_unit["name"]   

        #orgunit_uid, orgunit_name = orgUnit_code_uid_dict[facility_nin]

        print("orgunit_uid --", orgunit_uid, "orgunit_name -- ", facility_nin_org_unit_name, "execution_date --", execution_date)
        print("name--", block_name, "--", district_name, "--", facility_nin_org_unit_name )

        if temp_class_child_uid == 'None' or temp_class_child_uid == 'null':
            global null_temp_class_child_uid_count
            null_temp_class_child_uid_count = null_temp_class_child_uid_count + 1
        '''
        instanceName = str(submission["meta"]["instanceName"])
        temp_index = instanceName.find("CREATE")
        if "CREATE" in instanceName:
            instanceName = str((submission["meta"]["instanceName"]).split(":")[1]).strip()
            print("instanceName--", instanceName )
        '''
        if orgunit_uid:

            # uuid:6f9d9577-90f6-4668-ae33-4bd0cadc7011
            #event_id = submission["__id"].split(":")[1]

            child_unique_id = str(submission["class_child_uid"])
        
            #print("event_id/patient_id -- ", event_id )
            if not data_value_exists_in_dhis2( session_dhis2, DHIS2_API_URL, child_unique_id, orgunit_uid ) and (child_unique_id != 'None' and child_unique_id != 'null'):
                print(f"Child with ID  {child_unique_id} not exists in DHIS2. Adding.")
                log_info(f"Child with ID 1 {child_unique_id} not exists in DHIS2. Adding.")
                #print("---nexist orgunit--",
                      #assign_value_if_not_null(submission["login_check1"]["y_mobile"]))
                #print("---nexist orgunit facility_nin --", facility_nin , " -- orgunit_uid " , orgunit_uid)
                tracker_payloads = []
                #print(" gender --- ", submission["g_info"]["gender"])
                tracker = {
                    "trackedEntityType": "PFucIE1oPls",
                    "orgUnit": orgunit_uid,
                    "attributes": remove_null_values([
                        # abha_id    
                        {"attribute": "tJJg6LIBnCR", "value": assign_value_if_not_null(
                            submission["grp_new_register1"]["abha_id"])},
                        # urban_rural
                        {"attribute": "R9e8uhdYSzg", "value": assign_value_if_not_null(
                            submission["grp_address"]["urban_rural"])},
                        # class_child_dob    
                        {"attribute": "gRaVv2UsZ2F", "value": assign_value_if_not_null(submission["class_child_dob"])},
                        # class_child_gender
                        {"attribute": "laQwWtxL66d", "value": str(submission["class_child_gender"])},
                        # class_child_in_danger    
                        {"attribute": "Xf2LOdEbwrO", "value": assign_value_if_not_null(submission["class_child_in_danger"])},
                        # class_child_name
                        {"attribute": "b4GGVt3L6du", "value": assign_value_if_not_null(submission["class_child_name"])},
                        # bal_abha_id     
                        {"attribute": "oQVfclOIH0M", "value": assign_value_if_not_null(
                            submission["grp_new_register1"]["bal_abha_id"])},
                        # class_child_uid
                        {"attribute": "aAMjO9TQK0I", "value": assign_value_if_not_null(submission["class_child_uid"])},
                        # class_father_name
                        {"attribute": "CkPNUpOBflz", "value": assign_value_if_not_null(submission["class_father_name"])},

                        # class_mother_name
                        {"attribute": "gtgfofPb13o", "value": assign_value_if_not_null(submission["class_father_name"])},

                        # provider_designation_reg
                         {"attribute": "Z2YCvGEBKtr", "value": assign_value_if_not_null(submission["grp_confirm_child"]["provider_designation_reg"])},

                        # village_ward_code
                         {"attribute": "DVJKfvSmo3F", "value": assign_value_if_not_null(submission["grp_address"]["village_ward_code"])},                            
                    ]),
                    
                    "enrollments": [
                        {
                            "orgUnit": orgunit_uid,
                            "program": "pUOYd7YC9GN",
                            "enrolledAt": execution_date,
                            "occurredAt": execution_date,
                            "dueDate": execution_date,
                            "events": [
                                {
                                    "program": "pUOYd7YC9GN",
                                    "orgUnit": orgunit_uid,
                                    "occurredAt": execution_date,
                                    #"status": "COMPLETED",
                                    "status": "ACTIVE",
                                    #"storedBy": "admin",
                                    "programStage": "dlQpctFsGBU",
                                    "dataValues": remove_null_values([
                                        # provider_mobile    
                                        {"dataElement": "nBGWUCCFoiu", "value": assign_value_if_not_null(submission["grp_provider"]["provider_mobile"])},
                                        # provider_name
                                        {"dataElement": "EffdMV85KUy", "value": assign_value_if_not_null(submission["grp_provider"]["provider_name"])},
                                        # provider_designation
                                        {"dataElement": "dFOPmrI4YJ2", "value": assign_value_if_not_null(submission["grp_provider"]["provider_designation"])},
                                        # class_visit_count_asha    
                                        {"dataElement": "hEDfjtWDHgl", "value": assign_value_if_not_null(submission["class_visit_count_asha"])},
                                        # mcp_card
                                        {"dataElement": "xYiKk1S3mgg", "value": assign_value_if_not_null(submission["grp_new_register1"]["mcp_card"])},
                                        # discharge_slip
                                        {"dataElement": "d1sTo8ed7Y2", "value": assign_value_if_not_null(submission["grp_new_register1"]["discharge_slip"])},
                                        # live_birth
                                        {"dataElement": "kfXbnLthM51", "value": assign_value_if_not_null(submission["grp_new_register1"]["live_birth"])},
                                        # place_of_delivery
                                        {"dataElement": "Y7ynMzOes0g", "value": assign_value_if_not_null(submission["grp_new_register2"]["place_of_delivery"])},
                                        # type_of_delivery
                                        {"dataElement": "gLFVEgpXb4k", "value": assign_value_if_not_null(submission["grp_new_register2"]["type_of_delivery"])},    
                                        # nb_stay_days
                                        {"dataElement": "no51QCxxXnD", "value": assign_value_if_not_null(submission["grp_new_register2"]["nb_stay_days"])},
                                        # newborn_cry
                                        {"dataElement": "oN1US5LBkKu", "value": assign_value_if_not_null(submission["grp_new_register2"]["newborn_cry"])},
                                        #first_feed
                                        {"dataElement": "S4YXY9a58kl", "value": assign_value_if_not_null(submission["grp_new_register2"]["first_feed"])},
                                        # breastfeed_started
                                        {"dataElement": "Uji3lfiKLG1", "value": assign_value_if_not_null(submission["grp_new_register2"]["breastfeed_started"])},
                                        # class_birth_weight
                                        {"dataElement": "OFb2q78oRSo", "value": assign_value_if_not_null(submission["class_birth_weight"])},
                                        # ageindays
                                        {"dataElement": "fI4XUkOJ9oD", "value": assign_value_if_not_null(submission["ageindays"])},
                                        # visit_type
                                        {"dataElement": "ddcBwpTcoTQ", "value": assign_value_if_not_null(submission["visit_type"])},
                                        #child_available
                                        {"dataElement": "vP3am2Aw7VX", "value": assign_value_if_not_null(submission["grp_status"]["child_available"])},
                                        # cause_nonavailable
                                        {"dataElement": "VDqKs8Z0VEy", "value": assign_value_if_not_null(submission["grp_status"]["cause_nonavailable"])},
                                        # admitted_nrc_paediatric_unit
                                        {"dataElement": "FVN7fQlUu3e", "value": assign_value_if_not_null(submission["grp_status"]["admitted_nrc_paediatric_unit"])},
                                        # joint_visit_newborn_conducted
                                        {"dataElement": "bbgHQh4VFnQ", "value": assign_value_if_not_null(submission["grp_status"]["joint_visit_newborn_conducted"])},
                                        # joint_visit_child_conducted
                                        {"dataElement": "yOj4QkPi4CN", "value": assign_value_if_not_null(submission["grp_status"]["joint_visit_child_conducted"])},
                                        # sncu_followup_vistit_due
                                        {"dataElement": "YHskQDkJ6pO", "value": assign_value_if_not_null(submission["grp_status"]["sncu_followup_vistit_due"])},
                                        # birth_defect_link_rbsk
                                        {"dataElement": "BC6VB5voUte", "value": assign_value_if_not_null(submission["grp_status"]["birth_defect_link_rbsk"])},
                                        # birth_defect_treat_followup
                                        {"dataElement": "NQYMirAMiV1", "value": assign_value_if_not_null(submission["grp_status"]["birth_defect_treat_followup"])},
                                        # refer_danger_sign
                                        {"dataElement": "iw8IP0mqr5n", "value": assign_value_if_not_null(submission["grp_status"]["refer_danger_sign"])},
                                        # class_child_alive
                                        #{"dataElement": "QjY0NmbU9DI", "value": assign_value_if_not_null(submission["g_symptom4"]["class_child_alive"])},
                                        # class_underweight
                                        {"dataElement": "RRy9aLYSLfT", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_underweight"])},
                                        # class_malnutrition
                                        {"dataElement": "eDpx1UsRX8g", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_malnutrition"])},
                                        # class_microcephaly
                                        {"dataElement": "GnRhOOl6e7z", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_microcephaly"])},   
                                        # class_low_birth_weight
                                        {"dataElement": "C1KSTWNPPu7", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_low_birth_weight"])},
                                        # class_preterm_birth
                                        {"dataElement": "Nuuxdmr55lz", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_preterm_birth"])},
                                        # class_not_initiated_breastmilk
                                        {"dataElement": "ewSKDbbqZP7", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_not_initiated_breastmilk"])},
                                        # class_discharge_sncu
                                        {"dataElement": "TiUjD3JIqdJ", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_discharge_sncu"])},
                                        # class_birth_defect
                                        {"dataElement": "BAA3vVcxWfA", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_birth_defect"])},
                                        # class_not_regained_birth_weight
                                        {"dataElement": "IsXLWD2t3Wr", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_not_regained_birth_weight"])},
                                        # class_not_gaining_weight
                                        {"dataElement": "a1FYr7ovFDT", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_not_gaining_weight"])},
                                        # class_atrisk_birth
                                        {"dataElement": "E1kLxy7sZZU", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_atrisk_birth"])},
                                        # class_atrisk_newborn
                                        {"dataElement": "R2CpgcaImvC", "value": assign_value_if_not_null(submission["grp_atrisk1"]["class_atrisk_newborn"])},
                                        # class_bacterial_infection
                                        {"dataElement": "D1jr2fJI6OJ", "value": assign_value_if_not_null(submission["grp_danger"]["class_bacterial_infection"])},
                                        # class_very_severe_disease
                                        {"dataElement": "WRXDVb0f3L0", "value": assign_value_if_not_null(submission["grp_danger"]["class_very_severe_disease"])},
                                        # class_jaundice
                                        {"dataElement": "Un71fHjsKFp", "value": assign_value_if_not_null(submission["grp_jaundice"]["class_jaundice"])},
                                        # class_pneumonia
                                        {"dataElement": "WLZYDSX2oCg", "value": assign_value_if_not_null(submission["grp_cough"]["class_pneumonia"])},
                                        # class_cough
                                        {"dataElement": "d3lnzwAjMte", "value": assign_value_if_not_null(submission["grp_cough"]["class_cough"])},                               
                                        # class_cough_14days
                                        {"dataElement": "o3h6tqYghLG", "value": assign_value_if_not_null(submission["grp_cough"]["class_cough_14days"])},
                                        # class_dehydration
                                        {"dataElement": "XE1rTCa99lu", "value": assign_value_if_not_null(submission["grp_diaarrhoea"]["class_dehydration"])},
                                        # class_dysentery
                                        {"dataElement": "wivlqktQI0N", "value": assign_value_if_not_null(submission["grp_diaarrhoea"]["class_dysentery"])},
                                        # class_persist_diarrhoea
                                        {"dataElement": "TGr80vjjR7B", "value": assign_value_if_not_null(submission["grp_diaarrhoea"]["class_persist_diarrhoea"])},
                                        # class_very_severe_febrile_disease
                                        {"dataElement": "JbuPQSsHDw4", "value": assign_value_if_not_null(submission["grp_fever"]["class_very_severe_febrile_disease"])},
                                        # class_malaria
                                        {"dataElement": "d48e6Ds8vhU", "value": assign_value_if_not_null(submission["grp_fever"]["class_malaria"])},
                                        # class_anemia
                                        {"dataElement": "V5P8OylHtNg", "value": assign_value_if_not_null(submission["grp_anemia"]["class_anemia"])},
                                        # class_child_in_danger                                            
                                        {"dataElement": "Bb0IJ1kQ5ng", "value": assign_value_if_not_null(submission["class_child_in_danger"])},
                                        # class_nrc_refer_advice
                                        {"dataElement": "AghS7OYFla6", "value": assign_value_if_not_null(submission["class_nrc_refer_advice"])},
                                        # class_recurrent_illness
                                        {"dataElement": "D2PteSuzxGq", "value": assign_value_if_not_null(submission["class_recurrent_illness"])},
                                        # class_ecd_warning
                                        {"dataElement": "aeYgpJcrEri", "value": assign_value_if_not_null(submission["class_ecd_warning"])},
                                        # class_atrisk_youngchild
                                        {"dataElement": "DpnWj8gXGTB", "value": assign_value_if_not_null(submission["class_atrisk_youngchild"])},
                                        # class_atrisk
                                        {"dataElement": "KlfTevfcwup", "value": assign_value_if_not_null(submission["class_atrisk"])},
                                        # class_referral
                                        {"dataElement": "Z1tLjzHkCrR", "value": assign_value_if_not_null(submission["class_referral"])}, 
                                        # exclusive_breastfeed
                                        {"dataElement": "HeBSBTpvdmL", "value": assign_value_if_not_null(submission["grp_feed"]["exclusive_breastfeed"])},
                                        # breastfed_every2hrs
                                        {"dataElement": "roNYbMVXSot", "value": assign_value_if_not_null(submission["grp_feed"]["breastfed_every2hrs"])},
                                        # breastfed_atnight
                                        {"dataElement": "q45FLpjKdTh", "value": assign_value_if_not_null(submission["grp_feed"]["breastfed_atnight"])},
                                        # passess_urin
                                        {"dataElement": "MaQjcls4E1y", "value": assign_value_if_not_null(submission["grp_feed"]["passess_urin"])}, 
                                        # mixed_top_feed
                                        {"dataElement": "cXk6TfQjto1", "value": assign_value_if_not_null(submission["grp_feed"]["mixed_top_feed"])},    
                                        # breastfeeding_continued
                                        {"dataElement": "JhSKzQhGoNl", "value": assign_value_if_not_null(submission["grp_feed"]["breastfeeding_continued"])},
                                        # compli_food_yn6_36
                                        {"dataElement": "HtJ16qWLOoK", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_yn6_36"])},
                                        # compli_food_qty6_9
                                        {"dataElement": "vkORsb6oZhv", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_qty6_9"])},
                                        # compli_food_times6_9
                                        {"dataElement": "eRGi7isukcu", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_times6_9"])},
                                        # compli_food_qty9_12
                                        {"dataElement": "nv7id0KOtQ6", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_qty9_12"])},
                                        # compli_food_times9_12
                                        {"dataElement": "ifrI6gwHKjW", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_times9_12"])},
                                        # compli_food_snack9_12
                                        {"dataElement": "IUgqINAvdDz", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_snack9_12"])},
                                        # compli_food_qty12_18    
                                        {"dataElement": "vFPpQh3rpdV", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_qty12_18"])},
                                        # compli_food_times12_18
                                        {"dataElement": "v68d5N3dyk8", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_times12_18"])},
                                        # compli_food_qty18_36
                                        {"dataElement": "szkRggeTQaY", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_qty18_36"])},
                                        # compli_food_times18_36
                                        {"dataElement": "tGDPTqTjtED", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_times18_36"])},
                                        # compli_food_snack18_36
                                        {"dataElement": "eumNL3LjsiL", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_snack18_36"])},
                                        # compli_food_milk18_36
                                        {"dataElement": "GUeez82mfDP", "value": assign_value_if_not_null(submission["grp_feed"]["compli_food_milk18_36"])},
                                        # c_dewarm
                                        {"dataElement": "WJI3wh2rjad", "value": assign_value_if_not_null(submission["grp_feed"]["c_dewarm"])},
                                        # c_vit_a
                                        {"dataElement": "RNnj2FYXFZ9", "value": assign_value_if_not_null(submission["grp_feed"]["c_vit_a"])},
                                        # c_ifa
                                        {"dataElement": "ml5NndeXqji", "value": assign_value_if_not_null(submission["grp_feed"]["c_ifa"])},
                                        # c_ors    
                                        {"dataElement": "pvcaSFzPpTX", "value": assign_value_if_not_null(submission["grp_feed"]["c_ors"])},
                                        # diff_breastfeed
                                        {"dataElement": "uhgZIrDtju2", "value": assign_value_if_not_null(submission["grp_feed"]["diff_breastfeed"])},
                                        # breast_engorge
                                        {"dataElement": "abDS7P8F2NO", "value": assign_value_if_not_null(submission["grp_feed"]["breast_engorge"])},
                                        # kmc_received
                                        {"dataElement": "H50aJJVjCS8", "value": assign_value_if_not_null(submission["grp_feed"]["kmc_received"])},
                                        # skin_pustules
                                        {"dataElement": "q4swF6q2RtS", "value": assign_value_if_not_null(submission["grp_feed"]["skin_pustules"])},
                                        # eye_yellow
                                        {"dataElement": "MUET0IWg2Ie", "value": assign_value_if_not_null(submission["grp_feed"]["eye_yellow"])},
                                        # umbilicus_pus_bleed
                                        {"dataElement": "EHRXyq59s6M", "value": assign_value_if_not_null(submission["grp_feed"]["umbilicus_pus_bleed"])},
                                        # ssnb_family_safety_newborn
                                        {"dataElement": "OJDYxwz1oGN", "value": assign_value_if_not_null(submission["grp_household1"]["ssnb_family_safety_newborn"])},
                                        # ssnb_family_need_newborn
                                        {"dataElement": "oAdKVjriEs0", "value": assign_value_if_not_null(submission["grp_household1"]["ssnb_family_need_newborn"])},
                                        # ssyc_family_spend_time
                                        {"dataElement": "xKYfDEmPJQ9", "value": assign_value_if_not_null(submission["grp_household1"]["ssyc_family_spend_time"])},
                                        # ssyc_child_tv_mobile
                                        {"dataElement": "Zzqbgd3Jg2Q", "value": assign_value_if_not_null(submission["grp_household1"]["ssyc_child_tv_mobile"])},
                                        # ssyc_screen_duration
                                        {"dataElement": "kwX6ngMlfq9", "value": assign_value_if_not_null(submission["grp_household1"]["ssyc_screen_duration"])},
                                        # ssyc_family_aware_harmful   
                                        {"dataElement": "pi8tN7GskvG", "value": assign_value_if_not_null(submission["grp_household1"]["ssyc_family_aware_harmful"])},
                                        # parent_counsel_ECD
                                        {"dataElement": "ritpz4tWR4D", "value": assign_value_if_not_null(submission["grp_household1"]["parent_counsel_ECD"])},
                                        # mother_info_security
                                        {"dataElement": "vuhqYSvu9zu", "value": assign_value_if_not_null(submission["grp_household1"]["mother_info_security"])},
                                        # hh_pollution_adverse
                                        {"dataElement": "Utxw4EZKygQ", "value": assign_value_if_not_null(submission["grp_household2"]["hh_pollution_adverse"])},
                                        # hh_pollution_counsel
                                        {"dataElement": "z7piqQNBq7L", "value": assign_value_if_not_null(submission["grp_household2"]["hh_pollution_counsel"])},
                                        # hh_heat_adverse_effect
                                        {"dataElement": "jLDHd76iW4M", "value": assign_value_if_not_null(submission["grp_household2"]["hh_heat_adverse_effect"])},
                                        # hh_heat_effect_counsel
                                        {"dataElement": "hNRoDoklLPK", "value": assign_value_if_not_null(submission["grp_household2"]["hh_heat_effect_counsel"])},
                                        # vstatus
                                        {"dataElement": "pwgJTIaCMoy", "value": assign_value_if_not_null(submission["grp_vaccine"]["vstatus"])},
                                        # class_mother_in_danger
                                        {"dataElement": "Jmc5QyosPla", "value": assign_value_if_not_null(submission["grp_danger_mother"]["class_mother_in_danger"])},
                                        # mother_diet
                                        {"dataElement": "YVMTW1LFtVq", "value": assign_value_if_not_null(submission["grp_health_mother"]["mother_diet"])},
                                        # mother_wash
                                        {"dataElement": "CdO1Y7nTNPy", "value": assign_value_if_not_null(submission["grp_health_mother"]["mother_wash"])},
                                        # mother_ifa
                                        {"dataElement": "VsSOYmadE54", "value": assign_value_if_not_null(submission["grp_health_mother"]["mother_ifa"])},
                                        # mother_spacing
                                        {"dataElement": "I4KK6mjLpk1", "value": assign_value_if_not_null(submission["grp_health_mother"]["mother_spacing"])},
                                        # mother_mns_1
                                        {"dataElement": "QTc8gPGeboX", "value": assign_value_if_not_null(submission["grp_mental_health"]["mother_mns_1"])},
                                        # mother_mns_2
                                        {"dataElement": "kl7rKBgq2UJ", "value": assign_value_if_not_null(submission["grp_mental_health"]["mother_mns_2"])},
                                        # refer_mother
                                        {"dataElement": "cbhCAY5eJbD", "value": assign_value_if_not_null(submission["grp_report_mother"]["refer_mother"])},
                                        # refered_facility
                                        {"dataElement": "vVO6xroFg99", "value": assign_value_if_not_null(submission["grp_refer"]["refered_facility"])},
                                        # class_visit_day_covered
                                        {"dataElement": "wsvbXNyzrtQ", "value": assign_value_if_not_null(submission["class_visit_day_covered"])},
                                        # class_visit03d_actual_mochoanm
                                        {"dataElement": "uPdNNuc7zi5", "value": assign_value_if_not_null(submission["class_visit03d_actual_mochoanm"])},
                                        # class_visit07d_actual_mochoanm
                                        {"dataElement": "xk4d6CfybnD", "value": assign_value_if_not_null(submission["class_visit07d_actual_mochoanm"])},
                                        # class_visit06m_actual_mochoanm
                                        {"dataElement": "c40Fyb0eg8Z", "value": assign_value_if_not_null(submission["class_visit06m_actual_mochoanm"])},
                                        # class_visit01d_actual_asha
                                        {"dataElement": "X7ygKtk1tHA", "value": assign_value_if_not_null(submission["class_visit01d_actual_asha"])},
                                        # class_visit03d_actual_asha
                                        {"dataElement": "TBk7mUFKq8B", "value": assign_value_if_not_null(submission["class_visit03d_actual_asha"])},
                                        # class_visit05d_actual_asha
                                        {"dataElement": "wYTnjZ83qcg", "value": assign_value_if_not_null(submission["class_visit05d_actual_asha"])},
                                        # class_visit07d_actual_asha
                                        {"dataElement": "ZbomrgJhHhE", "value": assign_value_if_not_null(submission["class_visit07d_actual_asha"])},
                                        # class_visit10d_actual_asha
                                        {"dataElement": "zFDGSB4jy7D", "value": assign_value_if_not_null(submission["class_visit10d_actual_asha"])},
                                        # class_visit14d_actual_asha
                                        {"dataElement": "wHkC4kRhiTt", "value": assign_value_if_not_null(submission["class_visit14d_actual_asha"])},
                                        # class_visit21d_actual_asha
                                        {"dataElement": "D07WD1FHeI8", "value": assign_value_if_not_null(submission["class_visit21d_actual_asha"])},
                                        # class_visit28d_actual_asha
                                        {"dataElement": "Ah7W2f2AWlo", "value": assign_value_if_not_null(submission["class_visit28d_actual_asha"])},
                                        # class_visit42d_actual_asha
                                        {"dataElement": "Ftnin96VwEa", "value": assign_value_if_not_null(submission["class_visit42d_actual_asha"])},
                                        # class_visit03m_actual_asha
                                        {"dataElement": "MuHN3Iv1uEo", "value": assign_value_if_not_null(submission["class_visit03m_actual_asha"])},
                                        # class_visit06m_actual_asha
                                        {"dataElement": "hU4VBB538lk", "value": assign_value_if_not_null(submission["class_visit06m_actual_asha"])},
                                        # class_visit09m_actual_asha
                                        {"dataElement": "aoJW5i7Jtyn", "value": assign_value_if_not_null(submission["class_visit09m_actual_asha"])},
                                        # class_visit12m_actual_asha
                                        {"dataElement": "KK3IAWhRpls", "value": assign_value_if_not_null(submission["class_visit12m_actual_asha"])},
                                        # class_visit18m_actual_asha
                                        {"dataElement": "peuEiWSfJSU", "value": assign_value_if_not_null(submission["class_visit18m_actual_asha"])},
                                        # class_visit24m_actual_asha
                                        {"dataElement": "ilfBjsiJnTO", "value": assign_value_if_not_null(submission["class_visit24m_actual_asha"])},
                                        # class_visit30m_actual_asha
                                        {"dataElement": "tDojoRfW39B", "value": assign_value_if_not_null(submission["class_visit30m_actual_asha"])},
                                        # class_visit36m_actual_asha
                                        {"dataElement": "ZrL0OXlRpbe", "value": assign_value_if_not_null(submission["class_visit36m_actual_asha"])}
                                    ])                                    

                                }
                            ]
                        }
                    ]
                }

                #print(" tracker --- ",tracker)
                # boolean type de's
                ''''
                {"dataElement": "aIHwYTVZ8xa", "value": convert_to_boolean(
                    submission["g_symptom4"]["stiff_neck"])},
                {"dataElement": "AjzxOrYrNiX", "value": convert_to_boolean(
                    submission["g_symptom"]["sym_jau"])},

                # Modify the vaccine section
                if submission["vaccine"]["Births"] is not None and "1" in submission["vaccine"]["Births"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "jQ0FytRaeiz", "value": "true"})
                if submission["vaccine"]["Births"] is not None and "2" in submission["vaccine"]["Births"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "OhXL8sA7OXO", "value": "true"})
                if submission["vaccine"]["Births"] is not None and "3" in submission["vaccine"]["Births"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "mYy9vokQqUw", "value": "true"})

                if submission["vaccine"]["w6v"] is not None and "1" in submission["vaccine"]["w6v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "XFSwnBeWvWA", "value": "true"})
                if submission["vaccine"]["w6v"] is not None and "2" in submission["vaccine"]["w6v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "DUkbY3oYF8l", "value": "true"})
                if submission["vaccine"]["w6v"] is not None and "3" in submission["vaccine"]["w6v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "fTDLA0N1nBF", "value": "true"})
                if submission["vaccine"]["w6v"] is not None and "4" in submission["vaccine"]["w6v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "EVuYbOwDJQG", "value": "true"})
                if submission["vaccine"]["w6v"] is not None and "5" in submission["vaccine"]["w6v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "qWhs2vOUshg", "value": "true"})

                if submission["vaccine"]["w10v"] is not None and "1" in submission["vaccine"]["w10v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "vUzJzfhN4gF", "value": "true"})
                if submission["vaccine"]["w10v"] is not None and "2" in submission["vaccine"]["w10v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "aCVif9XCeAp", "value": "true"})
                if submission["vaccine"]["w10v"] is not None and "3" in submission["vaccine"]["w10v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "Hp4nc4xHQFb", "value": "true"})

                if submission["vaccine"]["w14v"] is not None and "1" in submission["vaccine"]["w14v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "MuA9gqApApT", "value": "true"})
                if submission["vaccine"]["w14v"] is not None and "2" in submission["vaccine"]["w14v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "wwI4BTxvO2H", "value": "true"})
                if submission["vaccine"]["w14v"] is not None and "3" in submission["vaccine"]["w14v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "cBVSBNN9Ij5", "value": "true"})
                if submission["vaccine"]["w14v"] is not None and "4" in submission["vaccine"]["w14v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "r8RTl9y1IBX", "value": "true"})
                if submission["vaccine"]["w14v"] is not None and "5" in submission["vaccine"]["w14v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "DmIlUKrCK5c", "value": "true"})

                if submission["vaccine"]["m9v"] is not None and "1" in submission["vaccine"]["m9v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "WqGN5HkViYK", "value": "true"})
                if submission["vaccine"]["m9v"] is not None and "2" in submission["vaccine"]["m9v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "XJxoT9268rK", "value": "true"})

                if submission["vaccine"]["m16v"] is not None and "3" in submission["vaccine"]["m16v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "ey7fPlduahf", "value": "true"})
                if submission["vaccine"]["m16v"] is not None and "2" in submission["vaccine"]["m16v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "cwYwhTdZaRG", "value": "true"})
                if submission["vaccine"]["m16v"] is not None and "1" in submission["vaccine"]["m16v"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "Gt1Lafhtu9O", "value": "true"})

                if submission["pvdose"] is not None and "1" in submission["pvdose"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "ksGjrirdozT", "value": "true"})
                if submission["pfpvdose"] is not None and "1" in submission["pfpvdose"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "o8lTwLwyK5W", "value": "true"})
                if submission["maldose"] is not None and "1" in submission["maldose"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "gT6Ga1rXYHv", "value": "true"})

                if submission["refer"] is not None and "1" in submission["refer"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "dNn1kiXHaRp", "value": "true"})
                if submission["amoxidose"] is not None and "1" in submission["amoxidose"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "Ea6oKhCo7FQ", "value": "true"})
                if submission["gentadose"] is not None and "1" in submission["gentadose"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "RPxjehRGRKT", "value": "true"})
                if submission["ifadose"] is not None and "1" in submission["ifadose"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "MGhCCxKUzwX", "value": "true"})
                if submission["pcmdose"] is not None and "1" in submission["pcmdose"]:
                    tracker["enrollments"][0]["events"][0]["dataValues"].append(
                        {"dataElement": "m2KVw0VPRLl", "value": "true"})
          
                '''
                # json_data = json.dumps(tracker, indent=4)

                # print("-----------",tracker)
               
                # Check if "dg_sign" contains multiple values
                # dg_sign_values = submission.get("group_dgsign", {}).get("dg_sign", "").split()
                # feeding_values = submission.get("g_feeding", {}).get("Fassessment", "").split()

                #print(" tracker 2 ----------- 2 ",tracker)
                tracker_payloads.append(tracker)
                
                dg_sign_values = submission.get("group_dgsign", {}).get("dg_sign")
                

                if dg_sign_values is None:
                    dg_sign_values = []
                else:
                    dg_sign_values = dg_sign_values.split()

                feeding_values = submission.get("g_feeding", {}).get("Fassessment")
                if feeding_values is None:
                    feeding_values = []
                else:
                    feeding_values = feeding_values.split()

                ecd_warning_values = submission.get("dss_ecd", {}).get("ecd_warning")
                if ecd_warning_values is None:
                    ecd_warning_values = []
                else:
                    ecd_warning_values = ecd_warning_values.split()

               # Loop through each value in dg_sign_values
                for dg_sign_value in dg_sign_values:
                    # Convert the value to an integer
                    dg_sign_int = int(dg_sign_value)
                    # Check if the value is in the mapping
                    if dg_sign_int in dg_sign_mapping:
                        # print("dg_sign_int-uid", dg_sign_mapping[dg_sign_int])
                        # print("dg_sign_int-value", dg_sign_int)
                        # Append the corresponding DHIS2 data element to dataValues
                        tracker["enrollments"][0]["events"][0]["dataValues"].append(
                            {"dataElement": dg_sign_mapping[dg_sign_int], "value": dg_sign_value}
                        )
                #Loop through each value in dg_sign_values
                for feeding_value in feeding_values:
                    # Convert the value to an integer
                    feeding_int = int(feeding_value)
                    # Check if the value is in the mapping
                    if feeding_int in feeding_mapping:
                        # print("feeding_int-uid", feeding_mapping[feeding_int])
                        # print("feeding_int-value", feeding_int)
                        # Append the corresponding DHIS2 data element to dataValues
                        tracker["enrollments"][0]["events"][0]["dataValues"].append(
                            {"dataElement": feeding_mapping[feeding_int], "value": feeding_value}
                        )
                for ecd_warning_value in ecd_warning_values:
                    # Convert the value to an integer
                    ecd_warning_int = int(ecd_warning_value)
                    # Check if the value is in the mapping
                    if ecd_warning_int in ecd_warning_mapping:
                        # print("feeding_int-uid", feeding_mapping[feeding_int])
                        # print("feeding_int-value", feeding_int)
                        # Append the corresponding DHIS2 data element to dataValues
                        tracker["enrollments"][0]["events"][0]["dataValues"].append(
                            {"dataElement": ecd_warning_mapping[ecd_warning_int], "value": ecd_warning_value}
                        )
               
                 
                if tracker_payloads:
                    #print(f"tracker_payloads {tracker_payloads}")
                    push_to_dhis2(DHIS2_API_URL, session_dhis2 ,tracker_payloads,index+1, temp_class_child_uid, submission["assessment_date"])
            else:
                global  total_skip_count 
                total_skip_count = total_skip_count + 1
                print("Child with uuid:", child_unique_id, " and Event date: ", execution_date, "already exists in DHIS2. Skipping.")
                log_info( f"Child with ID {child_unique_id} and Event date {execution_date} already exists in DHIS2. Skipping.")
        else:
            log_info(f"DHIS2 organization unit not found for facility nin: {facility_nin} -- block: {block_name} and parent: {district_name}. Skipping.")
            print("DHIS2 organization unit not found for facility nin :" , facility_nin , "-- block:", block_name, "and parent:", district_name, "Skipping.")
    return tracker_payloads

# def push_to_dhis2(dhis2_events):
#     try:
#         for event in dhis2_events:
#             # print("123---",event)
#             response = requests.post(f"{DHIS2_API_URL}/trackedEntityInstances", json=event, auth=DHIS2_AUTH)
#             if response.status_code != 200:
#                 log_error("Failed to create event in DHIS2 for: " + str(response.content))
#         log_info(f"Ev----status-- {response.status_code} ")
#         log_info(f"Ev---- {response} ")
#         log_info("Data successfully pushed to DHIS2.")
#     except Exception as e:
#         log_error("An error occurred while pushing data to DHIS2: " + str(e))



def push_to_dhis2(
    DHIS2_API_URL,
    session_dhis2,
    tracked_entities,
    row,
    patient_id,
    event_date
):
    try:

        tracker_payload = {
            "trackedEntities": tracked_entities
        }

        dhis2_tracker_url = (
            f"{DHIS2_API_URL}/tracker"
            f"?async=false"
            f"&importStrategy=CREATE_AND_UPDATE"
        )

        #print(f"DHIS2 Tracker URL: {dhis2_tracker_url}")

        response = session_dhis2.post(
            dhis2_tracker_url,
            json=tracker_payload,
            headers={
                "Content-Type": "application/json"
            }
        )

        if response.status_code not in (200, 201):

            print(
                f"Failed to push data to DHIS2. "
                f"Status code: {response.status_code}, "
                f"Event Date: {event_date}, "
                f"Patient ID: {patient_id}, "
                f"Response: {response.text}"
            )

            log_error(
                f"Failed to push data to DHIS2. "
                f"Status code: {response.status_code}, "
                f"Event Date: {event_date}, "
                f"Patient ID: {patient_id}, "
                f"Response: {response.text}"
            )

            try:
                response_json = response.json()

                for conflict in response_json.get("conflicts", []):
                    print(
                        f"DHIS2 Conflict: "
                        f"{conflict.get('object')} - "
                        f"{conflict.get('value')} - "
                        f"{conflict.get('errorMessage')}"
                    )

            except Exception:
                pass

            return False

        else:

            global event_push_count
            event_push_count += 1

            print(
                f"Data successfully pushed to DHIS2. "
                f"ODK Sl.No: {row}, "
                f"Patient ID: {patient_id}, "
                f"Event Date: {event_date}, "
                f"event_push_count: {event_push_count}"
            )

            #print(f"DHIS2 Response: {response.text}")

            log_info(
                f"Data successfully pushed to DHIS2. "
                f"ODK Sl.No: {row}, "
                f"Patient ID: {patient_id}, "
                f"Event Date: {event_date}, "
                f"event_push_count: {event_push_count}"
            )

            return True

    except Exception as e:

        print(
            f"An error occurred while pushing data to DHIS2: {e}"
        )

        log_error(
            f"An error occurred while pushing data to DHIS2: {e}"
        )

        return False



def main():

    with ThreadPoolExecutor(max_workers=1) as executor:
        try:
            configure_logging()
            current_time_start = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print( f"pushing Tracker event data in DHIS2 start . { current_time_start }" )
            log_info(f"pushing Tracker event data in DHIS2 start . { current_time_start }")
            
            odk_data = fetch_odk_data()
            print(f"odk_data size {len(odk_data)}")
            log_info(f"odk_data size {len(odk_data)}")

            orgUnit_code_uid_dict = get_orgUnit_code_uid_dict(org_unit_api_url, session_dhis2, META_ATTRIBUTE_SSBSK_ORG_UNIT_CODE)
            print(f"orgUnit_code_uid_dict facility size {len(orgUnit_code_uid_dict)}")
            log_info(f"orgUnit_code_uid_dict facility size  -- {len(orgUnit_code_uid_dict)}")

            if odk_data is not None:
                print(f"odk_data size {len(odk_data)}")
                log_info(f"odk_data size {len(odk_data)}")
                dhis2_events = transform_to_dhis2_events(odk_data, orgUnit_code_uid_dict )
                #if dhis2_events:
                    #print( f"push_to_dhis2 . { push_to_dhis2 }" )
                    #push_to_dhis2(dhis2_events)
        except Exception as e:
           
            print(f"An error occurred in the main process: {str(e)}")
            log_error(f"An error occurred in the main process: {str(e)}")


if __name__ == "__main__":

    event_push_count = 0
    null_temp_class_child_uid_count = 0
    total_child_count = 0
    total_skip_count = 0

    main()
    current_time_end = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print( f"pushing Tracker event data in DHIS2 finished . { current_time_end }" )
    log_info(f"pushing Tracker event data in DHIS2 finished . { current_time_end }")

    print(f"total_child_count. {total_child_count}, null_temp_class_child_uid_count. {null_temp_class_child_uid_count}, event_push_count {event_push_count}, total_skip_count {total_skip_count}")
    log_info(f"total_child_count. {total_child_count}, null_temp_class_child_uid_count. {null_temp_class_child_uid_count}, event_push_count {event_push_count}, total_skip_count {total_skip_count}")
    #sendEmail()
