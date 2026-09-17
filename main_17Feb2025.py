# main.py
import requests
from datetime import datetime
from constants import ODK_AUTH, ODK_API_URL, DHIS2_API_URL, DHIS2_AUTH
from utils import (
    configure_logging,
    log_info,
    log_error,
    get_dhis2_orgunit_uid_by_block_district,
    get_dhis2_orgunit_uid_by_nin,
    data_value_exists_in_dhis2,
)


def fetch_odk_data():
    try:
        today_date = datetime.now().strftime("%Y-%m-%d")
        updated_odk_api_url = f"{ODK_API_URL}?$filter=__system/submissionDate ge {today_date}"
        print("Data fetched for:", updated_odk_api_url)
       
        response = requests.get(updated_odk_api_url, auth=ODK_AUTH)

        if response.status_code == 200:
            if response.json() and "value" in response.json():
                log_info("ODK data fetched successfully.")
                return response.json()["value"]
            else:
                log_error("Invalid or missing JSON content in the ODK response.")
                return []
        else:
            log_error(
                f"Failed to fetch ODK data. Status code: {response.status_code}")
            return []
    except Exception as e:
        log_error("An error occurred while fetching ODK data: " + str(e))
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


def format_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%y-%m-%d")
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


def transform_to_dhis2_events(odk_data):
    tracker_payloads = []

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
    for submission in odk_data:
        # Ensure 'login_check1' and 'g_info' keys exist
        if 'login_check1' not in submission or 'g_info' not in submission:
            log_error(f"Missing 'login_check1' or 'g_info' in submission: {submission}")
            continue
       
        block_name = submission["login_check1"]["BLOCK_NAME"]
        district_name = submission["login_check1"]["DISTRICT_NAME"]
        facility_name = submission["login_check1"]["Facility"]
        facility_nin = submission["login_check1"]["srch_nin"]
        # orgunit_uid = get_dhis2_orgunit_uid_by_block_district(block_name, district_name,facility_name)
        orgunit_uid = get_dhis2_orgunit_uid_by_nin(facility_nin)
        # print("--", orgunit_uid)
        # print("name--", block_name, "--", district_name, "--", facility_name)
        if orgunit_uid:
            event_id = str(submission["g_info"]["patient_id"])
            if not data_value_exists_in_dhis2(event_id, orgunit_uid):
                print("---nexist orgunit--",
                      assign_value_if_not_null(submission["login_check1"]["y_mobile"]))
                tracker = {
                    "trackedEntityType": "oATSCRUUP2e",
                    "orgUnit": orgunit_uid,
                    "attributes": remove_null_values([
                        {"attribute": "taR4U6rFoJe", "value": assign_value_if_not_null(
                            submission["login_check1"]["y_mobile"])},
                        {"attribute": "P3rzcSSRXl2", "value": assign_value_if_not_null(
                            submission["login_check1"]["Ass_name"])},
                        {"attribute": "VTCQOcgxnbu", "value": assign_value_if_not_null(
                            submission["login_check1"]["srch_nin"])},
                        {"attribute": "vJ5V1IQXZjP", "value": str(
                            submission["g_info"]["patient_id"])},
                        {"attribute": "Pjefw1pegya", "value": assign_value_if_not_null(
                            submission["ch_info_new"]["p_mnumber"])},
                        {"attribute": "PZpInnrrLro", "value": assign_value_if_not_null(
                            submission["ch_info_new"]["p_name"])},
                        {"attribute": "LrySs4kH5RF", "value": assign_value_if_not_null(
                            submission["ch_info_new"]["p_gname"])},
                        {"attribute": "OQjRgNoLfSX", "value": assign_value_if_not_null(
                            submission["g_info"]["p_village"])},
                        {"attribute": "oEMrehxUj3q", "value": assign_value_if_not_null(
                            submission["ch_info_new"]["gender"])},
                    ]),
                    "enrollments": [
                        {
                            "orgUnit": orgunit_uid,
                            "program": "Tt9ILP7v4Fd",
                            "enrollmentDate": submission["g_info"]["cdate"],
                            "incidentDate": submission["g_info"]["cdate"],
                            "dueDate": submission["g_info"]["cdate"],
                            "events": [
                                {
                                    "program": "Tt9ILP7v4Fd",
                                    "orgUnit": orgunit_uid,
                                    "eventDate": submission["g_info"]["cdate"],
                                    "status": "COMPLETED",
                                    "storedBy": "admin",
                                    "programStage": "rLqP0fc0ezB",
                                    "dataValues": remove_null_values([
                                        {"dataElement": "jjrFSLhONiM", "value": assign_value_if_not_null(
                                            submission["ageindays"])},
                                        {"dataElement": "Tg78gykR93z", "value": assign_value_if_not_null(submission["g_info"]["dob_month1"])},
                                           {"dataElement": "wiPBFA12xk3", "value": assign_value_if_not_null(submission["g_info"]["dob_year1"])},
                                        # {"dataElement": "SfbOkRY9DpZ", "value": assign_value_if_not_null(submission["age_group"]["age_week"])},
                                        {"dataElement": "k6FVpUuqsS2", "value": assign_value_if_not_null(
                                            submission["age2m"])},
                                        {"dataElement": "K2wIle8NT6W", "value": assign_value_if_not_null(
                                            submission["age6m"])},

                                        {"dataElement": "hqgCOHJInA0", "value": assign_value_if_not_null(
                                            submission["g_assessment"]["p_height"])},
                                        {"dataElement": "ZSsWwLEqGKk", "value": assign_value_if_not_null(
                                            submission["g_assessment"]["cweight_kg"])},
                                        #   {"dataElement": "WoNcJwJRnQw", "value": assign_value_if_not_null(submission["g_assessment"]["cweight_gram"])},

                                        {"dataElement": "GdDpEB7ynVN", "value": assign_value_if_not_null(
                                            submission["g_assessment"]["wsd"])},
                                        {"dataElement": "VTmoPxkBo6E", "value": assign_value_if_not_null(
                                            submission["g_assessment"]["ctof"])},
                                        #   {"dataElement": "UpVOPm0GEGs", "value": assign_value_if_not_null(submission["g_assessment"]["tstatus"])},
                                        {"dataElement": "O5AhfFlx7mo", "value": assign_value_if_not_null(
                                            submission["g_assessment"]["Respiratory_Rate"])},

                                        #   {"dataElement": "TsgCP7DmoOk", "value": assign_value_if_not_null(submission["g_assessment"]["fbreath"])},
                                        #   {"dataElement": "JspJkmCqjVi", "value": assign_value_if_not_null(submission["g_assessment"]["rstatus"])},
                                        {"dataElement": "FIbRtWyuYTV", "value": assign_value_if_not_null(
                                            submission["g_symptom2"]["SpO2"])},
                                        # {"dataElement": "TTLmU9uVNms", "value": assign_value_if_not_null(
                                        #     submission["group_dgsign"]["dg_sign"])},

                                        {"dataElement": "heeMNNzHx5F", "value": convert_to_boolean(
                                            submission["sbi"])},
                                        {"dataElement": "RS49bAM8eqt", "value": convert_to_boolean(
                                            submission["lbi"])},
                                        {"dataElement": "SL23KYREYx6", "value": convert_to_boolean(
                                            submission["vsd"])},

                                        {"dataElement": "vCM8aknxuHa", "value": convert_to_boolean(
                                            submission["g_symptom4"]["sym_fev"])},
                                        {"dataElement": "WZ20khHO6hY", "value": assign_value_if_not_null(
                                            submission["g_symptom4"]["fever_days"])},
                                        {"dataElement": "ZORujXaBDIq", "value": convert_to_boolean(
                                            submission["g_symptom4"]["rdt_yn"])},
                                        {"dataElement": "axEK4FrVKId", "value": assign_value_if_not_null(
                                            submission["g_symptom4"]["Malaria_RDT"])},
                                        {"dataElement": "Cap7heibSuc", "value": assign_value_if_not_null(
                                            submission["g_symptom4"]["RDT_Result"])},
                                        {"dataElement": "GFuAmDGOwU3", "value": convert_to_boolean(
                                            submission["g_symptom2"]["sym_cou"])},
                                        {"dataElement": "zSMO6Z9ZYuW", "value": assign_value_if_not_null(
                                            submission["g_symptom2"]["cough_days"])},
                                        {"dataElement": "us1ejneunla", "value": convert_to_boolean(
                                            submission["g_symptom2"]["chest_indrawing"])},
                                        {"dataElement": "bh29EbIXtoW", "value": convert_to_boolean(
                                            submission["g_symptom3"]["sym_dia"])},
                                        {"dataElement": "ZYBgaRdy2P2", "value": convert_to_boolean(
                                            submission["g_symptom3"]["Blood_in_stool"])},
                                        {"dataElement": "dCcDZpeI2CU", "value": assign_value_if_not_null(
                                            submission["g_symptom3"]["Duration_dia"])},
                                        {"dataElement": "QexgEXFBJjU", "value": convert_to_boolean(
                                            submission["g_symptom3"]["sunken_eye"])},
                                        {"dataElement": "mGmc5SBuSTU", "value": assign_value_if_not_null(
                                            submission["g_symptom3"]["Diasign1"])},
                                        {"dataElement": "AaD3wFRPJuR", "value": assign_value_if_not_null(
                                            submission["g_symptom3"]["Diasign2"])},
                                        {"dataElement": "Mwm0FWAKx91", "value": assign_value_if_not_null(
                                            submission["g_symptom3"]["Diasign3"])},
                                        {"dataElement": "wPaepUry0zP", "value": convert_to_boolean(
                                            submission["sdehy"])},
                                        {"dataElement": "FrqeyskmmRO", "value": convert_to_boolean(
                                            submission["mdehy"])},
                                        {"dataElement": "DWN5ro9apBK", "value": convert_to_boolean(
                                            submission["g_symptom"]["Yellowps"])},

                                        {"dataElement": "lKVfb0PQmKG", "value": convert_to_boolean(
                                            submission["g_physical"]["Oedema"])},
                                        {"dataElement": "lwfojBDB21L", "value": assign_value_if_not_null(
                                            submission["g_physical"]["MUAC"])},
                                        {"dataElement": "Rup9mAN7poA", "value": assign_value_if_not_null(
                                            submission["g_symptom5"]["Palmar_Pallor"])},
                                  
                                        {"dataElement": "aNYzfJzRR1z", "value": assign_value_if_not_null(
                                            submission["g_symptom5"]["hb_result"])},
                                        {"dataElement": "hFU3TpxkusV", "value": assign_value_if_not_null(
                                            submission["g_feeding"]["Fedinday"])},
                                        # {"dataElement": "TI4L48NhpRv", "value": assign_value_if_not_null(
                                        #     submission["g_feeding"]["Fassessment"])},

                                        {"dataElement": "joGoMEmXjws", "value": convert_to_boolean(
                                            submission["vaccine"]["vverify"])},


                                        {"dataElement": "bOscllt4kTF", "value": assign_value_if_not_null(
                                            submission["vaccine"]["vcount"])},
                                        {"dataElement": "yTmNn1h7GF1", "value": assign_value_if_not_null(
                                            submission["vaccine"]["vuptoage"])},
                                        {"dataElement": "kh3PWQZqGJ7", "value": assign_value_if_not_null(
                                            submission["vaccine"]["vstatus"])},

                                        {"dataElement": "UPneh8IFQaS", "value": assign_value_if_not_null(
                                            submission["class_danger"])},
                                        {"dataElement": "drVi4hwvtf4", "value": assign_value_if_not_null(
                                            submission["class_cough"])},
                                        {"dataElement": "dZ6ILZRGYwG", "value": assign_value_if_not_null(
                                            submission["class_diarrhoea"])},
                                        {"dataElement": "b1GoUpmpCY3", "value": assign_value_if_not_null(
                                            submission["class_dehydration"])},
                                        {"dataElement": "DYyANDuDU8h", "value": assign_value_if_not_null(
                                            submission["class_fever"])},
                                        {"dataElement": "pJbgYDfbV3r", "value": assign_value_if_not_null(
                                            submission["class_jaundice"])},
                                        {"dataElement": "dKXzAeX5O4q", "value": assign_value_if_not_null(
                                            submission["class_nutri_L2M"])},
                                        {"dataElement": "ZJS5H5EolmS", "value": assign_value_if_not_null(
                                            submission["class_nutri_M2M"])},
                                        {"dataElement": "DZoPvl0fICU", "value": assign_value_if_not_null(
                                            submission["g_symptom5"]["class_anemia"])},

                                        # {"dataElement": "CU97c3f2hq5", "value": assign_value_if_not_null(submission["dose_calculation"]["Amoxi"])},

                                        # {"dataElement": "uqiT3mFx1Ox", "value": assign_value_if_not_null(submission["dose_calculation"]["Genta"])},

                                        # {"dataElement": "c06TNXTQBBT", "value": assign_value_if_not_null(submission["dose_calculation"]["IFA"])},

                                        # {"dataElement": "argWDxZqqj8", "value": assign_value_if_not_null(submission["dose_calculation"]["PCM"])},

                                        # {"dataElement": "ZAMHgk9dHAR", "value": assign_value_if_not_null(submission["ORS"])},

                                        # {"dataElement": "faumbnV5vJl", "value": assign_value_if_not_null(submission["Zinc"])},

                                        # {"dataElement": "A4wSm6a0yQ8", "value": assign_value_if_not_null(submission["Atrisunate"])},
                                        #  {"dataElement": "Q6KwOxtgTek", "value": assign_value_if_not_null(submission["Sulphadoxine"])},

                                        #  {"dataElement": "Z9jX6G0kt5x", "value": assign_value_if_not_null(submission["Pyramethamine"])},
                                        #  {"dataElement": "hzXTJCuq9gf", "value": assign_value_if_not_null(submission["Primaquine"])},
                                        #  {"dataElement": "S6c1UVYurC5", "value": assign_value_if_not_null(submission["Chloroquine5"])},
                                        #  {"dataElement": "jJxKlcp97yD", "value": assign_value_if_not_null(submission["Chloroquine10"])},
                                        #  {"dataElement": "njWT7dalFqz", "value": assign_value_if_not_null(submission["malless5"])},
                                        #  {"dataElement": "aQ9xskOsjhD", "value": assign_value_if_not_null(submission["mal5to60"])},
                                        #  {"dataElement": "UG1Iroe8LPQ", "value": assign_value_if_not_null(submission["mal12to60"])},

                                        {"dataElement": "xPM9IdEvtuI", "value": format_date(
                                            submission["f_cdate"])},
                                        {"dataElement": "uHT7yTuxaVh", "value": assign_value_if_not_null(
                                            submission["action"]["action_taken"])},
                                        {"dataElement": "JC7QLcTk2jk", "value": assign_value_if_not_null(
                                            submission["action"]["refered_facility"])},
                                        {"dataElement": "DrDGvWlEwZ3", "value": assign_value_if_not_null(
                                            submission["login_check1"]["designation"])}
                                    ])
                                }
                            ]
                        }
                    ]


                }
                # print("---",tracker)
                # boolean type de's
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
          

                # json_data = json.dumps(tracker, indent=4)

                # print("-----------",tracker)
               
                # Check if "dg_sign" contains multiple values
                # dg_sign_values = submission.get("group_dgsign", {}).get("dg_sign", "").split()
                # feeding_values = submission.get("g_feeding", {}).get("Fassessment", "").split()
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
               

            else:
                print("Event with uuid:", event_id,
                      "already exists in DHIS2. Skipping.")
                log_info(
                    f"Event with ID {event_id} already exists in DHIS2. Skipping.")
        else:
            log_info(
                f"DHIS2 organization unit not found for facility nin: {facility_nin} -- block: {block_name} and parent: {district_name}. Skipping.")
            print("DHIS2 organization unit not found for block:",
                  block_name, "and parent:", district_name, "Skipping.")
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


def push_to_dhis2(dhis2_events):
    try:
        log_info("Data successfully pushed to DHIS2.")
        for event in dhis2_events:
            response = requests.post(
                f"{DHIS2_API_URL}/trackedEntityInstances", json=event, auth=DHIS2_AUTH)
            if response.status_code != 200:
                # Log detailed error information
                log_error(
                    f"Failed to create event in DHIS2. Status code: {response.status_code}, Response: {response.content}")
                # Check for conflict messages in the response
                if 'conflicts' in response.json():
                    for conflict in response.json()['conflicts']:
                        log_error(
                            f"DHIS2 Conflict: {conflict['object']} - {conflict['value']}")
            else:
                log_info("Data successfully pushed to DHIS2.")
                # Log the response
                log_info(f"Tracker event posted. Response: {response.status_code}, {response.text}")
    except Exception as e:
        log_error(f"An error occurred while pushing data to DHIS2: {e}")


def main():
    try:
        configure_logging()
        odk_data = fetch_odk_data()
        if odk_data is not None:
            dhis2_events = transform_to_dhis2_events(odk_data)
        if dhis2_events:
            push_to_dhis2(dhis2_events)
    except Exception as e:
        log_error("An error occurred in the main process: " + str(e))


if __name__ == "__main__":
    main()
