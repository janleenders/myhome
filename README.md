Quick Reference Card 'MyHome' application
=========================================

Introduction
------------
Thanks for using the MyHome application!

The primary aim of this application is to:
- read the data from the 'P1' port which is part of the installation of a 'slimme meter' in the Netherlands.
- read the data from solar installations at home.
- present the data within a webservice
- be a central command center for all kinds of domotica related components (smart switches, sensors, etc.)

It is based om examples and knowledge which can be found on the internet, mostly within the open source communities.

This version is the first working increment after the first sprint. 

Properties
----------
- Version: 1.0 (01-01-2023)
- Name: MyHome
- Author: Jan Leenders (janleenders@kpnplanet.nl)

Design overview
---------------
The design is based on the following requirements:
- Must be able to run on a Raspberry pi 2B or higher
- Make use of broadly accepted general components where necessary
- Make use of broadly accepted programming language(s)
- Relatively easy configurable for specific home situations in the netherlands (and probably also in Belgium)
 
Product backlog items
---------------------
- Further development of the reports functionality in the webservice. 
- Create the first version of the control functionality
- Add additional control on the quality of the configuration file input, to enhance the stability of the application. 

Installation, general steps
---------------------------
- Create  directory  within which the application will be installed. f.e. : '/home/pi/myhome'
- Copy the application files (including the application directory structure) into this directory.
- Edit the parameter values in the config file myhome.config (in the root of the application directory). You are allowed to rename this file. Make sure you use the correct filename when defining the cron jobs.
- Make sure you install the following software on your rasberry pi:
	- Python
	- Flask (webserver)
	- sqlite3 (database environment)

- Add two lines to the crontab definitions ( sudo crontab -e) :

	@reboot python3 /home/pi/myhome/p1r/reader.py /home/pi/myhome/myhome.config >> /home/pi/myhome/log/reader.log
	@reboot python3 /home/pi/myhome/ws/site.py /home/pi/myhome/myhome.config >> /home/pi/myhome/log/site.log

  As you can see the parameterfile is passed to the python code using the first argument during startup of the application services. 

- Restart your raspberry pi (from commandline: shutdown -r now) and wait a couple of minutes

- Check whether the services are running using the command: 
	ps aux | grep reader
	ps aux | grep site
	
	Make sure that the cron service within Debian running.

- By now you should be able to see data in the database. Go to sqlite3 <database name> and check this:
	- select * from p1_channel_detail order by tst desc limit 10;
	- You should see a couple of detail records

Last words
----------
The above should do the trick to get MyHome running within your own home. If not, please contact me on my e-mail address so I can give some support on the issues.
If you have any suggestions for future versions of this application I would be happy to hear from you!


	
	

