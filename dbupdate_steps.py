from concurrent.futures import ThreadPoolExecutor
import csv
import os
import time
from commands import *
from Schema import *
import ujson as json
import urllib.request
import requests
from sqlalchemy import Table

# make it work nice across threads

create_database()

url = "https://esi.evetech.net/latest"


"""

!!!!!!!!!!!!!!!  READ THIS   !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    These functions are used to pull data from ESI, and populate the persistent json files, 
    which are used to re-build the database should it need to be deleted for a schema change.
    Absolutely never run these unless you know what you are doing!

"""


"""Populate Systems Database from ESI"""


def csv_to_json(filename):
    '''Using CSV names from
    https://www.fuzzwork.co.uk/dump/latest/
    '''
    # getting file from fuzzwork
    url_str = (f"https://www.fuzzwork.co.uk/dump/latest/{filename}.csv")
    filename_final = 'json/' + filename + '.csv'
    urllib.request.urlretrieve(url_str, filename_final)

    jsonArray = []

    # read csv file
    with open(f"json/{filename}.csv", encoding='utf-8') as csvf:
        # load csv file data using csv library's dictionary reader
        csvReader = csv.DictReader(csvf)

        # convert each csv row into python dict
        for row in csvReader:
            # add this python dict to json array
            jsonArray.append(row)

    # convert python jsonArray to JSON String and write to file
    with open(f"json/{filename}.json", 'w', encoding='utf-8') as jsonf:
        jsonString = json.dumps(jsonArray, indent=4)
        jsonf.write(jsonString)

    myfile = f"json/{filename}.csv"
    # If file exists, delete it.
    if os.path.isfile(myfile):
        os.remove(myfile)
    else:
        # If it fails, inform the user.
        print("Error: %s file not found" % myfile)


def step1():
    def single_request(system):
        for attempt in range(1,4):        
            try:
                resp = requests.get(
                    f"{url}/universe/systems/{system}/?datasource=tranquility")
                resp.raise_for_status()                
                return json.loads(resp.text)
            except Exception as e:
                print(e)
                if attempt <3:
                    time.sleep(attempt*20)
                else:
                    print("************************* ALL RETRY ATTEMPTS FAILED *************************")


    def submit_request(system):
        with Session as session:
            new_data = single_request(system)
            entry = Systems(id=new_data['system_id'], name=new_data["name"],
                            constellation_id=new_data["constellation_id"])
            print(entry)
            session.add(entry)
            session.commit()

    # Purging content of systems table
    with Session as session:
        my_table = Table('systems', metadata, autoload=True)
        session.query(my_table).delete()
        print("Deleting table")
        session.commit()

    response = requests.get(f"{url}/universe/systems/?datasource=tranquility")
    data = response.json()

    with ThreadPoolExecutor(max_workers=8) as executor:
        executor.map(submit_request, data)
    print("Populate Systems dbupdate step finished")


"""Populate Constellations Database from ESI"""


def step2():
    def single_request(constellation):
        for attempt in range(1,4):        
            try:
                resp = requests.get(
                    f"{url}/universe/constellations/{constellation}/?datasource=tranquility")
                resp.raise_for_status()                
                return json.loads(resp.text)
            except Exception as e:
                print(e)
                if attempt <3:
                    time.sleep(attempt*20)
                else:
                    print("************************* ALL RETRY ATTEMPTS FAILED *************************")


    with Session as session:
        def submit_request(constellation):
            new_data = single_request(constellation)
            entry = Constellations(id=new_data['constellation_id'], name=new_data["name"],
                                region_id=new_data["region_id"])
            print(entry)
            session.add(entry)

        # Purging content of constellations table
        with Session as session:
            my_table = Table('constellations', metadata, autoload=True)
            session.query(my_table).delete()
            print("Deleting table")
            session.commit()            
        response = requests.get(
            f"{url}/universe/constellations/?datasource=tranquility")
        data = response.json()

        with ThreadPoolExecutor(max_workers=8) as executor:
            executor.map(submit_request, data)
        session.commit()
        print("Populate Constellations dbupdate step finished")


"""Populate Regions Database from ESI"""


def step3():
    def single_request(region):
        for attempt in range(1,4):        
            try:
                resp = requests.get(
                    f"{url}/universe/regions/{region}/?datasource=tranquility")
                resp.raise_for_status()                
                return json.loads(resp.text)
            except Exception as e:
                print(e)
                if attempt <3:
                    time.sleep(attempt*20)
                else:
                    print("************************* ALL RETRY ATTEMPTS FAILED *************************")


    with Session as session:
        def submit_request(region):
            new_data = single_request(region)
            entry = Regions(id=new_data['region_id'], name=new_data["name"])
            print(entry)
            session.add(entry)


        # Purging content of regions table
        with Session as session:
            my_table = Table('regions', metadata, autoload=True)
            session.query(my_table).delete()
            print("Deleting table")
            session.commit()

        response = requests.get(
            f"{url}/universe/regions/?datasource=tranquility")
        data = response.json()

        with ThreadPoolExecutor(max_workers=3) as executor:
            executor.map(submit_request, data)
        session.commit()
        print("Populate Regions dbupdate step finished")


"""Populate Station Database from ESI"""


def step4():

    with Session as session:
        # Purging content of stations table
        my_table = Table('stations', metadata, autoload=True)
        session.query(my_table).delete()
        print("Deleting table")
        session.commit()
    
        filename = 'staStations'
        if not path.exists(f"json/{filename}.json"):
            csv_to_json(filename)
        with open(f"json/{filename}.json", 'r') as file:
            obj = load(file)
            for _ in obj:
                if _['stationID']:
                    entry = Stations(id=_['stationID'], name=_['stationName'],
                                    solarSystemID=_['solarSystemID'])
                    session.add(entry)
        session.commit()
        print("Populate Stations dbupdate step finished")


def step5():

    with Session as session:
        # Purging content of items table
        my_table = Table('items', metadata, autoload=True)
        session.query(my_table).delete()
        print("Deleting table")
        session.commit()
        filename = 'invTypes'
        if not path.exists(f"json/{filename}.json"):
            csv_to_json(filename)
        with open(f"json/{filename}.json", 'r') as file:
            obj = load(file)
            for _ in obj:
                if _['typeID'].isnumeric() and _['marketGroupID'] and _['published'] == "1":
                    entry = Items(typeID=_['typeID'], marketGroupID=_[
                                'marketGroupID'], typeName=_['typeName'])
                    session.merge(entry)
        session.commit()
        print("Populate Items dbupdate step finished")


def step6():

    with Session as session:
        # Purging content of marketgroups table
        my_table = Table('marketgroups', metadata, autoload=True)
        session.query(my_table).delete()
        print("Deleting table")
        session.commit()
        filename = 'invMarketGroups'
        if not path.exists(f"json/{filename}.json"):
            csv_to_json(filename)
        with open(f"json/{filename}.json", 'r') as file:
            obj = load(file)
            for _ in obj:
                if _['marketGroupID'].isnumeric():
                    entry = MarketGroups(marketGroupID=_['marketGroupID'], parentGroupID=_[
                                        'parentGroupID'], marketGroupName=_['marketGroupName'])
                    session.merge(entry)
        session.commit()
        print("Populate MarketGroups dbupdate step finished")



def write_regions_to_json_file():

    with Session as session:
        mydict = {}

        results = session.query(Regions).all()
        for region in results:
            mydict[region.id] = [
                region.name]
        obj = json.dumps(mydict, indent=4)
        with open("json/regions.json", "w") as file:
            file.write(obj)


def write_constellations_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(Constellations).all()
        for constellation in results:
            mydict[constellation.id] = [
                constellation.name, constellation.region_id]
        obj = json.dumps(mydict, indent=4)
        with open("json/constellations.json", "w") as file:
            file.write(obj)


def write_systems_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(Systems).all()
        for system in results:
            mydict[system.id] = [system.name, system.constellation_id]
        obj = json.dumps(mydict, indent=4)
        with open("json/systems.json", "w") as file:
            file.write(obj)


def write_corporations_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(Corporations).all()
        for corp in results:
            mydict[corp.id] = [
                corp.name, corp.alliance_id, corp.ticker]

        obj = json.dumps(mydict, indent=4)
        with open("json/corporations.json", "w") as file:
            file.write(obj)


def write_alliances_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(Alliances).all()
        for ally in results:
            mydict[ally.id] = [
                ally.name, ally.ticker]

        obj = json.dumps(mydict, indent=4)

        with open("json/alliances.json", "w") as file:
            file.write(obj)


def write_server_configurations_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(ServerConfigs).all()
        for server in results:
            mydict[server.id] = [
                server.name, server.channel, server.muted, server.neutral_color, server.involvedmin]
        obj = json.dumps(mydict, indent=4)
        with open("json/server_configs.json", "w") as file:
            file.write(obj)


def write_watchlists_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(WatchLists).all()
        for watchl in results:
            mydict[watchl.server_id] = [watchl.systems, watchl.constellations,
                                        watchl.regions, watchl.corporations, watchl.alliances, watchl.f_corporations, watchl.f_alliances]
        obj = json.dumps(mydict, indent=4)
        with open("json/watchlists.json", "w") as file:
            file.write(obj)


def write_ships_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(Ships).all()
        for ship in results:
            mydict[ship.id] = [ship.name, ship.group_id]

        obj = json.dumps(mydict, indent=4)
        with open("json/ships.json", "w") as file:
            file.write(obj)


def write_items_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(Items).all()
        for Item in results:
            mydict[Item.typeID] = [Item.typeName, Item.marketGroupID]

        obj = json.dumps(mydict, indent=4)
        with open("json/invTypes.json", "w") as file:
            file.write(obj)


def write_market_groups_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(MarketGroups).all()
        for MarketGroup in results:
            mydict[MarketGroup.MarketGroupID] = [MarketGroup.MarketGroupName, MarketGroup.parentGroupID]

        obj = json.dumps(mydict, indent=4)
        with open("json/invMarketGroups.json", "w") as file:
            file.write(obj)


def write_stations_to_json_file():
    with Session as session:
        mydict = {}

        results = session.query(Stations).all()
        for station in results:
            mydict[station.id] = [station.solarSystemID, station.name]
        obj = json.dumps(mydict, indent=4)
        with open("json/staStations.json", "w") as file:
            file.write(obj)
"""Run before database is deleted for schema reformatting!"""


def PREPARE_FOR_DB_DELETE():
    write_systems_to_json_file()
    write_constellations_to_json_file()
    write_regions_to_json_file()
    write_stations_to_json_file()
    write_ships_to_json_file()
    write_items_to_json_file()
    write_market_groups_to_json_file()
    write_corporations_to_json_file()
    write_alliances_to_json_file()
    write_server_configurations_to_json_file()
    write_watchlists_to_json_file()

PREPARE_FOR_DB_DELETE()

# step1()
# step2()
# step3()
# step4()
# step5()
# step6()