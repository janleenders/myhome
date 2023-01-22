# Name: site.py
# Author: Jan Leenders
# Description: 
#    This is the main part of the website
#    Each page is defined using a seperate module and html template.
#    webserver listens on port 6701 (can be adjusted).
#

from flask import Flask, render_template
from flask import request

from package_site import site_dashboard
from package_site import site_control
from package_site import site_report
from package_generic import parameters
import sys

args = sys.argv[1:] # get access to the parameters. First one is the configuration file location.

# Set your own preferences here

param_dict = {
                "application_path" : ["/home/pi/myhome/", "str", False],
                "solar_path"  : ["<unknown>","str",False],
                "solar_system": ["<unknown>","str",False],
                "web_port"    : [80, "int", False]
             }
if parameters.setParameters(args[0], param_dict):
   parameters.showParameters(param_dict)
   try:
      application_path = param_dict["application_path"][0]
      web_port = param_dict["web_port"][0]
      db_path = "db/"
      db = application_path + db_path + 'p1r.db'
   except Exception:
      print("Essential parameter not set: 'application_path' or 'web_port'. Abort execution.")
      raise
   try:
      solar_system = param_dict["solar_system"][0]
      solar_path = param_dict["solar_path"][0]
   except Exception:
      print("Solar parameters not set: 'solar_system' and/or 'solar_request_path'. Execution continues without solar data.")
      solar_system = "<not defined>"
      solar_path = "<not defined>"
      pass
else:
   print("error while reading parameter file. Execution aborted.")
   quit()

app_name = "MyHome" 
main_menu = [['Dashboard', '/'], ['Control', '/control/'], ['Report', '/report/'] ]

app = Flask(__name__)
# main page show the dashboard
@app.route("/")
def site():
   interval_hrs = request.args.get('i', default=4, type = int)
   history_hrs = request.args.get('h', default=0, type = int)
   if interval_hrs > 25: interval_hrs = 25
   if interval_hrs < 1: interval_hrs = 1
   if history_hrs < -24 : history_hrs = -24
   if history_hrs > 0 : history_hrs = 0
   return site_dashboard.show_dashboard(main_menu, 0, app_name, interval_hrs, history_hrs, db, solar_system, solar_path)

@app.route("/report/")
def report():
   level = request.args.get('l', default='d', type = str)
   period = request.args.get('p', default=0, type = int)
   return site_report.show_report(main_menu, 2, app_name, level, period, db)

@app.route("/control/")
def control():
   
   return site_control.show_control(main_menu, 1, app_name)
      
if __name__ == "__main__":
   app.run(host='0.0.0.0', port=str(web_port), debug=True)

