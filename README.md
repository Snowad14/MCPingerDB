I made a mess of things I have to redo

# MCPingerDB
Ping servers using masscan files to try to find minecraft servers and retrieve information (connected players, motd, verson and other) stored in a database Mongodb, There is also a website available soon

## Usage

Install requirements for **python 3**:

```
Have a text file containing the results of a masscan scan in the form -oL
```
```
pip3 install -r requirements.txt
```
```
modify the variables with those you need and your mongodb credentials in main.py (on the top)
```
```
python3 main.py
```

## Disclaimer

Don't use it to destroy minecraft servers, it's immoral.

## Special Thanks

- Some of the code used from https://github.com/Zerogoki00/minescanner
- https://github.com/Dinnerbone/mcstatus
- https://github.com/robertdavidgraham/masscan
- https://github.com/Footsiefat/Minecraft-Server-Scanner Multithreading part because concurrent.futures cause memory leak with big file

## TODO

- Display more than 11 players in arrays
- Display if the server is Whitelisted
- Display if the server allow crack
- Website
