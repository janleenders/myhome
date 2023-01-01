# Name: site.py
# Author: Jan Leenders
# Description: 
#    This is the main part of the website
#    Each page is defined using a seperate module and html template.
#    webserver listens on port 6701 (can be adjusted).
#

from flask import Flask, render_template

from package_site import site_dashboard
from package_site import site_control
from package_generic import parameters
import sys

args = sys.argv[1:] # get access to the parameters. First one is the configuration file location.

# Set your own preferences here

param_dict = {
                "folder_path": ["/home/pi/myhome/", "str", False],
                "database": ["db/P1R.db","str",False]
             }
if parameters.setParameters(args[0], param_dict):
   parameters.showParameters(param_dict)
   folder_path = param_dict["folder_path"][0]
   db = folder_path + param_dict["database"][0]
else:
   print("error while reading parameter file. Execution aborted.")
   quit()

app_name = "MyHome" 
main_menu = [['Dashboard', '/'], ['Control', '/control/'], ['Day', '/day/'], ['Week', '/week/'], ['Month', '/month/'], ['Year', '/year/'] ]

app = Flask(__name__)
# main page show the dashboard
@app.route("/")
def site():

   return site_dashboard.show_dashboard(main_menu, 0, app_name, db)

@app.route("/control/")
def control():
   
   return site_control.show_control(main_menu, 1, app_name)
      
if __name__ == "__main__":
   app.run(host='0.0.0.0', port=6701, debug=True)

