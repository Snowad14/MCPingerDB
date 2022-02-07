import sys
import threading

import concurrent.futures
import json
import geoip2.database
from pymongo import MongoClient
from mcstatus import MinecraftServer

# DB CONFIGURATION
client = MongoClient("YOUR CRUSTER CREDENTIALS CONNECTION URLS")
DB = client["YOUR DATABASE NAME"]
col = DB["YOUR COLLECTION NAME"]

# PARAMETERS
NUMBER_OF_WORKER = 100

# FILES LOCATIONS - Modify with your path of file
DATABASE_FILE = "GeoLite2-Country.mmdb"
MASSCAN_OUTPUT = "sample.txt" 

# GLOBAL ARRAYS
ServerList = []

# CHARACTER TO EXCLUDE
BAD_CHARACTERS = ("'", '"', "`", "\n", "\t", ",", ";")
string_translator = str.maketrans({char: "" for char in BAD_CHARACTERS})

def resetServerList(array):
    array.clear()
    for srvinfo in col.find({}, {"_id":1, "IP": 1, "Port": 1 }):
        array.append(srvinfo)

def read_hosts(file_name):
    hosts = []
    try:
        with open(file_name, 'r') as f:
            for line in f:
                if "open" in line:
                    data = line.split()
                    hosts.append((data[3], int(data[2]),))
    except FileNotFoundError:
        print("File not found")
        sys.exit(1)
    return hosts

def checkMasscan(checkActivated):
    resetServerList(ServerList)
    hosts = read_hosts(MASSCAN_OUTPUT)
    with geoip2.database.Reader(DATABASE_FILE) as reader:
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_OF_WORKER) as executor:
            for ip, port in hosts:
                executor.submit(threaded_scan, ip, port, reader, checkActivated)

def threaded_scan(ip, port, reader, checkActivated):
    try:
        server = MinecraftServer(ip, port)
        status = server.status()

        if checkActivated == True:
            for x in ServerList:
                if (x["IP"] + x["Port"]) == ip + str(port):
                    print("Already in database : " + ip + ":" + str(port))
                    return

        print("Found Server " + ip + ":" + str(port))
        country = reader.country(ip).country.names["en"]
        latency = int(server.ping())


        playerlist = []
        if status.players.online > 0:
            for i in status.raw["players"]["sample"]:
                playerlist.append(i["name"])

        col.insert_one({
            "IP": ip,
            "Port": str(port),
            "Country": country,
            "Version": status.version.name.translate(string_translator),
            "Online": status.players.online,
            "Max": status.players.max,
            "Ping": latency,
            "MOTD": status.description.translate(string_translator),
            "OnlinePlayers": playerlist,
            "Status": "ONLINE"
        })

    except:
        print("IP is not a minecraft server or the server is not online : " + ip + ":" + str(port))

def updateAll():
    while True:
        resetServerList(ServerList)
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUMBER_OF_WORKER) as executor:
            for i in range(0, len(ServerList)):
                executor.submit(UpdateServer, ServerList[i])

def UpdateServer(srvinfos):
    try:
        server = MinecraftServer(srvinfos["IP"], int(srvinfos["Port"]))
        latency = int(server.ping())
        status = server.status()

        playerlist = []
        if status.players.online > 0:
            for i in status.raw["players"]["sample"]:
                playerlist.append(i["name"])

        col.find_one_and_update({"_id":srvinfos["_id"]}, {'$set':
        {"Version": status.version.name.translate(string_translator),
         "Online": status.players.online,
         "Max": status.players.max,
         "Ping": latency,
         "MOTD": status.description.translate(string_translator),
         "OnlinePlayers": playerlist,
         "Status": "ONLINE"}})

        print("Updated " + srvinfos["IP"] + " - " + str(ServerList.index(srvinfos)) + "/" + str(len(ServerList)))

    except Exception as e:
        #print(str(e))
        documentToUpdate = col.find_one_and_update({"_id": srvinfos["_id"]}, {'$set': { "Status": "OFFLINE" }})
        print("server not online " + srvinfos["IP"] + " - " + str(ServerList.index(srvinfos)) + "/" + str(len(ServerList)))

def removeDuplicates():
    for doc in col.find({}, {"IP": 1, "Port": 1}):
        try:
            numberOfIP = col.count_documents({"IP": doc["IP"], "Port": doc["Port"]})
        except:
            print("Error with IP " + doc["IP"] + " no port found, deleting")
            col.delete_one({"IP": doc["IP"]})
        if numberOfIP > 1:
            for i in range(numberOfIP - 1):
                print("Deleting " + doc["IP"] + ':' + doc["Port"])
                col.delete_one({"IP": doc["IP"], "Port": doc["Port"]})

if __name__ == '__main__':
    pass
    # Examples :
    # removeDuplicates()
    # updataAll()
    # checkMasscan(True)
    # checkMasscan(False)


