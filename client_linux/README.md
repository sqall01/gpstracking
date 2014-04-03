GPS tracking system Linux client
===========

This is a linux client for the GPS tracking system written in Python. It will track the movement of the client by gathering GPS data in a given interval. The client will store the gathered data locally until it is able to send it to the GPS tracking server. HTTPS is used for the transmission in order to protect the data.


How to install it
===========

The client depends on Python 2.7, gpsd and python-gps. Under Debian like systems you can install it with

apt-get install gpsd python-gps python2.7

To install the GPS tracking client, you have to copy the directory to your filesystem (for example to "/home/pi/gpstracking"). Then modify the necessary information in the configuration file under "/home/pi/gpstracking/config/gpstracker.conf".

To start the GPS tracking client when the system comes up, copy the "gpstracker.sh" file which lies in the "init.d_example" directory to "/etc/init.d/" and modify the USER and DAEMON variable in it to fit your system. Make the start up script executable by executing

chmod 755 /etc/init.d/gpstracker.sh

and add this script to your run levels. Under Debian like systems you can do this by executing

update-rc.d gpstracker.sh defaults