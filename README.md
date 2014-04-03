GPS tracking system (server and clients)
===========

This is a GPS tracking system that allows you to track the taken paths of a client or to track the current position and movements of a client. It consists of a server component that stores all GPS data in a MySQL database and a client component that gathers the current GPS data in an interval and transmits it to the server.

The server supports multiple clients and with the help of OpenStreetMap it can show you the taken GPS data directly with the browser.

The data is transmitted via HTTPS from the client to the server. If you are interested in this project and want to write your own client (for example for Android or iOS), you just have to be able to log in via HTTP authentication and transmit "latitude", "longitude", "altitude", "utctime" and "speed" via a POST request. The server will take care of the rest (which is storing the GPS data in a database and providing an interface to work with this data).

If you are interested in this project or just want to see some screenshots from the tracking, you can visit: [http://h4des.org/blog/index.php?/archives/342-Introduction-GPS-tracking-system.html](http://h4des.org/blog/index.php?/archives/342-Introduction-GPS-tracking-system.html)