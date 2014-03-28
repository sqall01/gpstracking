GPS tracking system server
===========

This is a simple server written in PHP. It uses MySQL as database backend and stores the GPS data transmitted by the clients. To show the current position of a client or the taken path, it either uses OpenLayer with OpenStreetMap within the browser or exports the data via the GPX format.


How to install it
===========

Installing the server is rather simple. It needs a MySQL server and PHP 5. You have to create a MySQL user for the server and a database for it. Insert the information into "config/config.php" and execute "config/install.php". After that the database is configured.

In order to differentiate between the clients/devices the server uses HTTP authentication. This means you have to configure the "get/.htaccess" and "submit/.htaccess" files. The server will store the HTTP authentication user as the device name. The directories "get" and "submit" are separately configured because only the "submit" directory is accessed by the clients/devices. The "get" directory should be accessed by a browser in order to view the collected GPS data.

All clients are written to use HTTPS to submit the gathered GPS data. So in order to protect your data transmission only use HTTPS (without HTTPS the HTTP authentication would be pointless).