# utils.py

import requests
import logging

import smtplib
from email.mime.multipart import MIMEMultipart 
from email.mime.text import MIMEText 
from email.mime.base import MIMEBase 
from email import encoders
from datetime import datetime
import os


from constants import DHIS2_API_URL, DHIS2_AUTH, LOG_FILE, LOG_FILE_EVENT_ERROR_LOG,ODK_API_URL

def configure_logging():
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def log_info(message):
    logging.info(message)

def log_error(message):
    logging.error(message)

def get_dhis2_orgunit_uid_by_block_district(session_post, block, district):
    params = {
        "filter": f"displayName:like:{block}",
        "fields": "id,name,parent[id,name]",
    }
    #http://172.105.253.84:8665/odk_nipi/api/organisationUnits.json?paging=false&fields=id,name,parent[id,name]&filter=displayName:like:Shopian
    #response = requests.get(f"{DHIS2_API_URL}/organisationUnits", params=params, auth=DHIS2_AUTH)
    response = session_post.get(f"{DHIS2_API_URL}/organisationUnits", params=params)
    #print("response --",response)

    if response.status_code == 200:
        orgunits = response.json()["organisationUnits"]
        for orgunit in orgunits:
            parent_name = orgunit["parent"]["name"]
            if parent_name.lower() == district.lower():
                return orgunit["id"]
    return None

def data_value_exists_in_dhis2(session_post,event_id):
    try:
        # response = requests.get(f"{DHIS2_API_URL}/events?dataElement=zkhndIoBYH7&filter=zkhndIoBYH7:like:{event_id}", auth=DHIS2_AUTH)
        #response = requests.get(f"{DHIS2_API_URL}/events?", params={"dataElement": "zkhndIoBYH7", "filter": f"zkhndIoBYH7:like:{event_id}"}, auth=DHIS2_AUTH)
        response = session_post.get(f"{DHIS2_API_URL}/events?", params={"dataElement": "zkhndIoBYH7", "filter": f"zkhndIoBYH7:like:{event_id}"})

        # print("matching uuid--",response.url)
        if response.status_code == 200:
            events = response.json()["events"]
            return len(events) > 0
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
    li = ["mithilesh.thakur@hispindia.org", "saurabh.leekha@hispindia.org","dpatankar@nipi-cure.org"]
    #li = ["mithilesh.thakur@hispindia.org","mithilesh.hisp@gmail.com","yoursmithilesh@gmail.com"]

    for toaddr in li:

        #toaddr = "mithilesh.thakur@hispindia.org"
        
        # instance of MIMEMultipart 
        msg = MIMEMultipart() 
        
        # storing the senders email address   
        msg['From'] = fromaddr 
        
        # storing the receivers email address  
        msg['To'] = toaddr 
        
        # storing the subject  
        msg['Subject'] = "ODK To DHIS2 Anemia Program data import log file"
        
        # string to store the body of the mail 
        #body = "Python Script test of the Mail"

        today_date = datetime.now().strftime("%Y-%m-%d")
        updated_odk_api_url = f"{ODK_API_URL}?$filter=__system/submissionDate ge {today_date}"
        body = f"ODK To DHIS2 Anemia Program data import log file for the url { updated_odk_api_url }"
        
        # attach the body with the msg instance 
        msg.attach(MIMEText(body, 'plain')) 
        
        
        # open the file to be sent

        '''
        files = [LOG_FILE]
        for a_file in files:
            attachment = open(a_file, 'rb')
            file_name = os.path.basename(a_file)
            part = MIMEBase('application','octet-stream')
            part.set_payload(attachment.read())
            part.add_header('Content-Disposition','attachment',filename=file_name)
            encoders.encode_base64(part)
            msg.attach(part)
        '''   


        '''
        # open the file to be sent  

        LOG_DIR = "logs"
        PATTERN = "*_dataValueSet_post.log"

        # Find latest matching log file
        log_files = glob.glob(os.path.join(LOG_DIR, PATTERN))
        if not log_files:
            raise FileNotFoundError("No log files found")

        latest_log = max(log_files, key=os.path.getmtime)

        filename = LOG_FILE
        #attachment = open(filename, "rb") 
        attachment = open(latest_log, "rb") 
        '''
        
        filename_log = LOG_FILE
        attachment = open(filename_log, "rb") 
        
        # instance of MIMEBase and named as p 
        p = MIMEBase('application', 'octet-stream') 
        
        # To change the payload into encoded form 
        p.set_payload((attachment).read()) 
        
        # encode into base64 
        encoders.encode_base64(p) 
        
        p.add_header('Content-Disposition', "attachment; filename= %s" % filename_log) 
        
        # attach the instance 'p' to instance 'msg' 
        msg.attach(p) 
        
        # creates SMTP session 

        #smtpserver = smtplib.SMTP("smtp.gmail.com", 587)
        
        try:
            smtpserver = smtplib.SMTP('smtp.gmail.com', 587) 
            smtpserver.ehlo()
            # start TLS for security 
            smtpserver.starttls()
            smtpserver.ehlo()

            # Authentication 
            
            smtpserver.login(fromaddr, "********")
            #smtpserver.login(fromaddr, "********")
            # start TLS for security 
            #s.starttls() 
            
            # Authentication 
            #s.login(fromaddr, "*********") 
            
            # Converts the Multipart msg into a string 
            text = msg.as_string() 
            
            # sending the mail 
            smtpserver.sendmail(fromaddr, toaddr, text) 
            print(f"mail send to: {toaddr}")
            log_info(f"mail send to: {toaddr}")
            # terminating the session 
            smtpserver.quit()
        except Exception as exception:
            print("Error: %s!\n\n" % exception)