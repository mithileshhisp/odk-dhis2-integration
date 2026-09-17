#!/bin/bash

# Navigate to the directory where main.py is located
#cd /var/dss-child-new
cd /var/dss-child-new || exit 1

# Activate virtual environment if needed (replace 'venv/bin/activate' with your venv path)
# source venv/bin/activate

# Run the main.py script
#python3 main.py
#python3 main.py
#python3 main_today.py

#!/bin/bash
/usr/bin/python3 /var/dss-child-new/main.py
#/usr/bin/python3 /var/dss-child-new/main_today.py

# Deactivate virtual environment if activated
# deactivate

# Navigate for saans
##cd /var/odk-dhis2
##python3 main.py