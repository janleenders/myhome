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
- Version: 1.1.3 (10-01-2023)
- Name: MyHome
- Author: Jan Leenders (janleenders@kpnplanet.nl)

Design overview
---------------
The design is based on the following requirements:
- Must be able to run on a Raspberry pi 2B or higher
- Make use of broadly accepted general components where necessary
- Make use of broadly accepted programming language(s)
- Relatively easy configurable for specific home situations in the netherlands (and probably also in Belgium)
- Enphase and Fronius solar systems are supported. Other can be added on request.
 
Release notes 1.1.3 (10-01-2023)
--------------------------------
- Correct presentation of the graphs, depending on the chosen filter: granularity, scrolling back in time. 
- Presenting the total usage figures for the chosen report period.
- Added some indexes to the database. Schema is described in 'schema.sql'. 
Product backlog items
---------------------
- Try to make it 'running out of the box'
- Create the first version of the control functionality
  - change the time intervals for which datapoints are collected.
  - Let the reader look into a database parameter table every hour to adjust the time interval parameters.
- Add additional control on the quality of the configuration file input, to enhance the stability of the application. 

Installation, general steps
---------------------------
- Create  directory  within which the application will be installed. f.e. : '/home/user/myhome' .
  The 'user' can be any user you have defined. The myhome.config file uses user 'pi'. You are free to change this. 
- Copy the application files (including the application directory structure) into this directory.
- Edit the parameter values in the config file myhome.config (in the root of the application directory). You are allowed to rename this file. Make sure you use the correct filename when defining the cron jobs.
- Make sure you install the following software on your rasberry pi:
	- Python
	- Flask (webserver)
	- sqlite3 (database environment)

- Add two lines to the crontab definitions ( sudo crontab -e) :

	@reboot python3 /home/user/myhome/py/reader.py /home/user/myhome/myhome.config >> /home/user/myhome/log/reader.log
	@reboot python3 /home/user/myhome/py/site.py /home/user/myhome/myhome.config >> /home/user/myhome/log/site.log

  As you can see the parameterfile is passed to the python code using the first argument during startup of the application services. 

- See to it that the cron service is configured correctly. This is not always the case! This service can be configured using the following steps for the Raspberry pi:

	Log in to your pi
	switch to root user using 'sudo bash'
	start the cron service by running '/etc/init.d/cron start'
	edit file '/etc/rc.local' and add the following line before 'exit 0':
		/etc/init.d/cron start
	reboot your system: shutdown -r now
	After reboot, check whether your cron job is started: 'ps aux | grep cron'.
	Also check the log tail of '/var/log/syslog' : cat /var/log/syslog | tail
 
- Restart your raspberry pi (from commandline: shutdown -r now) and wait a couple of minutes

- Check whether the services are running using the command: 
	ps aux | grep reader
	ps aux | grep site
	

- By now you should be able to see data in the database. Go to sqlite3 <database name> and check this:
	- select * from p1_channel_detail order by tst desc limit 10;
	- You should see a couple of detail records

Last words
----------
The above should do the trick to get MyHome running within your own home. If not, please contact me on my e-mail address so I can give some support on the issues.
If you have any suggestions for future versions of this application I would be happy to hear from you!

Earlier releasenotes
--------------------
v1.2.0 Changed the way solar systems can be supported. Currently fronius and enphase are suppoert. Other will folow in time or on request.
v1.1.0 some reportig enhancement, fixing some technical debt.
v1.0.0 Initial increment: basic functionality usable already!

