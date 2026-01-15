# utils.py

import requests
import logging

import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders
from datetime import datetime

from constants import DHIS2_API_URL, DHIS2_AUTH, LOG_FILE, ODK_API_URL



def configure_logging():
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

def get_orgUnit_code_uid_dict( session_post ):
    orgUnit_code_uid_dict = {}

    #ORGUNIT_CODE_UID = PcIkF2inBB3
    sql_view_url = f"{DHIS2_API_URL}/sqlViews/PcIkF2inBB3/data?paging=false"
    print(f"sql_view_url : {sql_view_url}")
    response_sql_view = session_post.get(sql_view_url)

    if response_sql_view.status_code == 200:
        #print(f"response_sql_view : {response_sql_view.status_code}")
        response_sql_view_data = response_sql_view.json()
        #print(f"response_sql_view_data : {response_sql_view_data}")

        
        tempListGrid   = response_sql_view.json().get('listGrid', {})
        #print(f"tempListGrid : {tempListGrid}")
        #print(f"title : {tempListGrid.get('title')}")
        tempRows = tempListGrid.get('rows',[])

        if tempRows:
            for rows in tempRows:
                org_unit_code = rows[0]
                org_unit_uid = rows[1]
                orgUnit_code_uid_dict[org_unit_code] = org_unit_uid
                #print(f"org_unit_code : {org_unit_code}, org_unit_uid : {org_unit_uid}")
                
        else:
            error_message = f"No data received for sqlview"
            print(error_message)

        #print(tempRows)

    else:
        print(f"Failed to retrieve sqlview data. Status code: {response_sql_view.status_code}")

    return orgUnit_code_uid_dict


















def get_orgUnit_code_uid_dict( session_post ):
    orgUnit_code_uid_dict = {}

    #ORGUNIT_CODE_UID = PcIkF2inBB3
    sql_view_url = f"{DHIS2_API_URL}/sqlViews/PcIkF2inBB3/data?paging=false"
    print(f"sql_view_url : {sql_view_url}")
    response_sql_view = session_post.get(sql_view_url)

    if response_sql_view.status_code == 200:
        #print(f"response_sql_view : {response_sql_view.status_code}")
        response_sql_view_data = response_sql_view.json()
        #print(f"response_sql_view_data : {response_sql_view_data}")

        
        tempListGrid   = response_sql_view.json().get('listGrid', {})
        #print(f"tempListGrid : {tempListGrid}")
        #print(f"title : {tempListGrid.get('title')}")
        tempRows = tempListGrid.get('rows',[])

        if tempRows:
            for rows in tempRows:
                org_unit_code = rows[0]
                org_unit_uid = rows[1]
                orgUnit_code_uid_dict[org_unit_code] = org_unit_uid
                #print(f"org_unit_code : {org_unit_code}, org_unit_uid : {org_unit_uid}")
                
        else:
            error_message = f"No data received for sqlview"
            print(error_message)

        #print(tempRows)

    else:
        print(f"Failed to retrieve sqlview data. Status code: {response_sql_view.status_code}")

    return orgUnit_code_uid_dict




def get_dhis2_orgunit_uid_by_block_district(session_post,block, district,facility):
    params = {
        "filter": f"displayName:like:{facility}",
        "fields": "id,name,parent[id,name]",
    }
    #response = requests.get(f"{DHIS2_API_URL}/organisationUnits", params=params, auth=DHIS2_AUTH)
    response = session_post.get(f"{DHIS2_API_URL}/organisationUnits", params=params )

    if response.status_code == 200:
        orgunits = response.json()["organisationUnits"]
        for orgunit in orgunits:
            parent_name = orgunit["parent"]["name"]
            if parent_name.lower() == block.lower():
                return orgunit["id"]
    return None









def get_dhis2_orgunit_uid_by_nin(session_post,dhis2_get_url,facility_nin):
    # api_url = "http://172.105.253.84:8665/odk_nipi/api/organisationUnits.json"
    params = {
        'fields': 'id,name,code',
        #'level': 5,
        'filter': f'code:eq:{facility_nin}'
    }
    #print(f"dhis2_get_url : {dhis2_get_url}")
    try:
        #response = requests.get(f"{DHIS2_API_URL}/organisationUnits", params=params, auth=DHIS2_AUTH)
        #http://49.50.97.167:8665/odk_nipi/api/organisationUnits.json?fields=id,name,code,level,parent[id,name]&filter=code:eq:1131532820&level=5&paging=false
        #http://49.50.97.167:8665/odk_nipi/api/organisationUnits.json?fields=id,name,code,level&filter=name:eq:Ratlam&level=4&paging=false
        
        #print("dhis2_get_url:", {dhis2_get_url}/"organisationUnits", params=params )
        
        response = session_post.get(f"{dhis2_get_url}/organisationUnits", params=params)

        if response.status_code == 200:
            orgunits = response.json().get('organisationUnits', [])

            if orgunits:
                return orgunits[0]['id']  # Assuming only one orgunit is expected in the response
            else:
                print(f"No orgunit found for code: {facility_nin}")
                return None
        else:
            print(f"Error: Unable to fetch data. Status Code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None
    
def data_value_exists_in_dhis2(session_post,dhis2_get_url,event_id,orgunit_uid):
    try:
        #http://172.105.253.84:8665/odk_nipi/api/trackedEntityInstances.json?ou=cXOfSxAY71d&program=eXm5MqSJmkc&filter=vJ5V1IQXZjP:EQ:784347329
        # response = requests.get(f"{DHIS2_API_URL}/events?dataElement=zkhndIoBYH7&filter=zkhndIoBYH7:like:{event_id}", auth=DHIS2_AUTH)
        
        #tei_search_url = f"{enrollment_endpoint}?ou={orgUnitID}&ouMode=SELECTED&program=vyQPQ07JB9M&filter=HKw3ToP2354:eq:{beneficiary_mapping_reg_id}"
        #response = requests.get(f"{DHIS2_API_URL}/trackedEntityInstances?ou={orgunit_uid}&ouMode=SELECTED&program=Tt9ILP7v4Fd", params={"filter": f"vJ5V1IQXZjP:EQ:{event_id}"}, auth=DHIS2_AUTH)
        #DESCENDANTS
        response = session_post.get(f"{dhis2_get_url}/trackedEntityInstances?ou={orgunit_uid}&ouMode=SELECTED&program=Tt9ILP7v4Fd", params={"filter": f"vJ5V1IQXZjP:EQ:{event_id}"})
        

        if response.status_code == 200:
            events = response.json()["trackedEntityInstances"]
            #print("length events--",len(events))
            #print(f"Event with ID {event_id} not exists in DHIS2. Adding.")
            #log_info(f"Event with ID {event_id} not exists in DHIS2. Adding.")
            if len(events) > 0:
                #print("matching uuid--", response.url)
                return True
            return False
    except Exception as e:
        log_error("An error occurred while checking data value in DHIS2.", e)
        return False
    

def sendEmail():
    # creates SMTP session
    #s = smtplib.SMTP('smtp.gmail.com', 587)
    # start TLS for security
    #s.starttls()
    # Authentication
    #s.login("ipamis@hispindia.org", "IPAMIS@12345")
    # message to be sent
    
    # message to be sent
    #message = "Message_you_need_to_send"

    # sending the mail
    #s.sendmail("ipamis@hispindia.org", "mithilesh.thakur@hispindia.org",message)
    #print(f"Email send to mithilesh.thakur@hispindia.org")
    # terminating the session
    #s.quit()
    


    fromaddr = "dss.nipi@hispindia.org"

    # list of email_id to send the mail
    li = ["mithilesh.thakur@hispindia.org", "saurabh.leekha@hispindia.org","dpatankar@nipi-cure.org","mohinder.singh@hispindia.org"]
    #li = ["mithilesh.thakur@hispindia.org"]

    for toaddr in li:

        #toaddr = "mithilesh.thakur@hispindia.org"
        
        # instance of MIMEMultipart 
        msg = MIMEMultipart() 
        
        # storing the senders email address   
        msg['From'] = fromaddr 
        
        # storing the receivers email address  
        msg['To'] = toaddr 
        
        # storing the subject  
        msg['Subject'] = "ODK To DHIS2 data import log file"
        
        # string to store the body of the mail 
        #body = "Python Script test of the Mail"

        today_date = datetime.now().strftime("%Y-%m-%d")
        updated_odk_api_url = f"{ODK_API_URL}?$filter=__system/submissionDate ge {today_date}"
        body = f"ODK To DHIS2 DSS Child Health Program data import log file for the url { updated_odk_api_url }"
        
        # attach the body with the msg instance 
        msg.attach(MIMEText(body, 'plain')) 
        
        
        # open the file to be sent  
        filename = LOG_FILE
        attachment = open(filename, "rb") 
        
        # instance of MIMEBase and named as p 
        p = MIMEBase('application', 'octet-stream') 
        
        # To change the payload into encoded form 
        p.set_payload((attachment).read()) 
        
        # encode into base64 
        encoders.encode_base64(p) 
        
        p.add_header('Content-Disposition', "attachment; filename= %s" % filename) 
        
        # attach the instance 'p' to instance 'msg' 
        msg.attach(p) 
        try:
            # creates SMTP session 
            s = smtplib.SMTP('smtp.gmail.com', 587) 
            
            # start TLS for security 
            s.starttls() 
            
            # Authentication 
            #s.login(fromaddr, "NIPIODKHispIndia@123")
            s.login(fromaddr, "hvaoefwbpdvnsqts")
            
            # Converts the Multipart msg into a string 
            text = msg.as_string() 
            
            # sending the mail 
            s.sendmail(fromaddr, toaddr, text) 
            print(f"mail send to: {toaddr}")
            log_info(f"mail send to: {toaddr}")
            # terminating the session 
            s.quit()
        except Exception as exception:
            print("Error: %s!\n\n" % exception)
