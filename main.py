import sys
import threading
import datetime
import concurrent.futures
import json
import geoip2.database
from pymongo import MongoClient
from mcstatus import MinecraftServer

# DB CONFIGURATION
client = MongoClient("YOUR CRUSTER CREDENTIALS CONNECTION URL")
DB = client["YOUR DATABASE NAME"]
col = DB["YOUR COLLECTION NAME"]

# PARAMETERS
NUMBER_OF_WORKER = 40

# FILES LOCATIONS
DATABASE_FILE = "GeoLite2-Country.mmdb"
MASSCAN_INPUT = "text.txt"

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
    return list(set(hosts)) # remove duplicate

def split_array(L,n):
    return [L[i::n] for i in range(n)]

def checkMasscan(checkActivated):
    hosts = read_hosts(MASSCAN_OUTPUT)
    resetServerList(ServerList)
    global split
    split = list(split_array(hosts, NUMBER_OF_WORKER))
    for x in range(NUMBER_OF_WORKER):
        thread = myThread(x, str(x), checkActivated).start()

class myThread (threading.Thread): # View credit for multithreading author
    def __init__(self, threadID, name, check):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.check = check
    def run(self):
        print ("Starting Thread " + self.name)
        threaded_scan(self.name, self.check)
        print ("Exiting Thread " + self.name)

def threaded_scan(threadname, checkActivated):
    with geoip2.database.Reader(DATABASE_FILE) as reader:
        for ip, port in split[int(threadname)]:
            if 0:
                threadname.exit()
            try:
                server = MinecraftServer(ip, port)
                status = server.status()

                country = reader.country(ip).country.names["en"]
                latency = int(server.ping())

                if checkActivated == True: # Just checkActivated will work but i prefer to write like that
                    for x in ServerList:
                        if (x["IP"] + x["Port"]) == ip + str(port):
                            print("Already in database : " + ip + ":" + str(port))
                            return

                playerlist = []
                if status.players.online > 0:
                    for i in status.raw["players"]["sample"]:
                        playerlist.append(i["name"])

                print("Found Server " + ip + ":" + str(port))
                
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
        time = datetime.datetime.now()
        timestring = f"{str(time.year)}/{str(time.month)}/{str(time.day)}/{str(time.hour)}/{str(time.minute)}/{str(time.second)}" # just str() with all will work i think
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

        playerArrayDate = (timestring, playerlist)
        col.find_one_and_update({"_id":srvinfos["_id"]}, {
            "$set": {
            "Version": status.version.name.translate(string_translator),
            "Online": status.players.online,
            "Max": status.players.max,
            "Ping": latency,
            "MOTD": status.description.translate(string_translator),
            "Status": "ONLINE"},
            "$push": {"OnlinePlayers": playerArrayDate}
        })

        print("Updated " + srvinfos["IP"] + " - " + str(ServerList.index(srvinfos)) + "/" + str(len(ServerList)))

    except Exception as e:
        #print(str(e)) if you want to s how errors delete #
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
    # Examples :
    #removeDuplicates()
     updateAll()
    # checkMasscan(False)
    # checkMasscan(True)


