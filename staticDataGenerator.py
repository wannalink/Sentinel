import csv
import json
import os

import urllib.request


def csv_to_json(filename):
    '''Using CSV names from
    https://www.fuzzwork.co.uk/dump/latest/
    '''
    # getting file from fuzzwork
    url_str = (f"https://www.fuzzwork.co.uk/dump/latest/{filename}.csv")
    filename_final = 'json/' + filename + '.csv'
    urllib.request.urlretrieve(url_str, filename_final)
    # try:
        # response = requests.get(url_str)
        
    #     with open(f"assets/{filename}.csv", 'w') as f:
    #         writer = csv.writer(f)
    #         for line in response.iter_lines():
    #             writer.writerow(line.decode('utf-8').split(','))
    # except Exception as err:
    #     print(err)

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


def extract_stations(filename, systemid=None, regionid=None):
    try:
        with open(f"json/{filename}.json", 'r') as json_data:
            json_data = json.load(json_data)
    except FileNotFoundError:
        print(f"{filename} json not found, downloading CSV")
        csv_to_json(filename)
        try:
            with open(f"json/{filename}.json", 'r') as json_data:
                json_data = json.load(json_data)
        except FileNotFoundError:
            print(f"CSV converting failed")
    result_dict = {}
    for i in json_data:
        if (systemid and i['solarSystemID'] == str(systemid)) or (regionid and i['regionID'] == str(regionid)):
            result_dict[i['stationID']] = i
    result_id = regionid if regionid else systemid
    with open(f"json/stations_{result_id}.json", 'w') as fp:
        json.dump(result_dict, ensure_ascii=False, indent=4, fp=fp)


# Example for getting all stations in Maila:

# csv_to_json('invTypes')
# extract_stations('staStations', systemid=30000162)
