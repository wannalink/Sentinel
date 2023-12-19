import asyncio
import json
import threading
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from os import environ
from urllib.request import Request, urlopen
import aiohttp
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()
USESYSTEM = int(environ['USESYSTEM'])
REGIONLIMIT = int(environ['REGIONLIMIT'])


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'k', 'm', 'b', 't', 'p'][magnitude])


def time_conv(input=None, flags=[], offset=int):
    local_tz = "Europe/Moscow"
    order_format = "%Y-%m-%dT%H:%M:%SZ"
    header_format = "%a, %d %b %Y %H:%M:%S %Z"
    output_format = "%Y-%m-%d %H:%M:%S"
    output = input
    if isinstance(output, datetime):
        # print('this is a time obj')
        pass
    else:
        if 'order' in flags:
            try:
                output = datetime.strptime(
                    output, order_format).replace(tzinfo=ZoneInfo("UTC"))
                output = output + timedelta(days=offset)
            except TypeError:
                print(f"Input missing offset for expiration date")
                return
            except ValueError:
                print(f"Formatting doesn't match {order_format}")
                return
        elif 'header' in flags:
            try:
                output = datetime.strptime(
                    output, header_format).replace(tzinfo=ZoneInfo("UTC"))
            except ValueError:
                print(f"Formatting doesn't match {header_format}")
                return
        else:
            print('Input format not specified')
            return
    if 'inp_loc' in flags:
        output = output.replace(tzinfo=ZoneInfo(local_tz))
    if 'delta' in flags:
        output = datetime.now(timezone.utc) - output
        return str(output).split(".")[0]
        # return output
    if 'ret_loc' in flags:
        output = output.astimezone(ZoneInfo(local_tz))
    if 'ret_str' in flags:
        output = output.strftime(output_format)
    return output


@lru_cache(maxsize=2)
def load_names(json_name):
    try:
        with open(f"json/{json_name}.json", 'r') as json_data:
            json_data = json.load(json_data)
            return json_data
    except FileNotFoundError:
        if json_name == (f"stations_{USESYSTEM}"):
            from staticDataGenerator import extract_stations
            extract_stations('staStations', systemid=USESYSTEM)
            try:
                with open(f"json/{json_name}.json", 'r') as json_data:
                    json_data = json.load(json_data)
                return json_data
            except FileNotFoundError:
                print("json generating failed")


def name_id_lookup(id=None, name=None, station=None):
    if id or name:
        lookup_data = load_names('names')
    elif station:
        station_scope = (f"stations_{USESYSTEM}")
        lookup_data = load_names(station_scope)
    else:
        print('Lookup type not specified')
        return
    if id:
        for i in lookup_data:
            if i['typeID'] == str(id):
                return i['typeName']
    elif name:
        if lookup_data:
            for i in lookup_data:
                if i['typeName'] == str(name):
                    return i['typeID']
        name = name.replace(" ", "%20")
        req_url = 'https://www.fuzzwork.co.uk/api/typeid2.php?typename='
        req = Request(req_url+name, headers={'User-Agent': 'XYZ/3.0'})
        webpage = urlopen(req, timeout=10).read()
        lookup_data = json.loads(webpage)
        if lookup_data[0]['typeID'] and lookup_data[0]['typeID'] != 0:
            return lookup_data[0]['typeID']
    elif station:
        station_name = lookup_data[str(station)]['stationName']
        station_type = lookup_data[str(station)]['stationTypeID']
        return station_name, station_type


def load_data(json_filename):
    try:
        with open(f"json/{json_filename}.json", 'r') as json_data:
            json_data = json.load(json_data)
            return json_data
    except FileNotFoundError:
        print(f"{json_filename} json not found.")
        return None


def market_info():
    def get_data_json(typeid=None):
        url_str = (
            f"https://esi.evetech.net/latest/markets/{REGIONLIMIT}/orders/?datasource=tranquility&order_type=sell&page=1&type_id={typeid}")
        use_headers = {'User-Agent': 'XYZ/3.0'}
        req = Request(url_str, headers=use_headers)
        item_orders = {}
        for attempt in range(1, 3):
            try:
                response = urlopen(req, timeout=8)
                # code = webpage.getcode()
                headers = dict(response.getheaders())
                load = json.loads(response.read())
                for order in load:
                    if USESYSTEM == 0 or order['system_id'] == USESYSTEM:
                        order['Expires'] = headers['Expires']
                        order['Last-Modified'] = headers['Last-Modified']
                        item_orders[order['order_id']] = order
                new[typeid] = item_orders
                return
            except Exception:
                print(
                    f"Attempt: {attempt} failed. Data of {typeid} not retrieved")
                continue
        try:
            new[typeid] = orig[typeid]
            print(f'Using old data for {typeid}')
        except Exception:
            print(
                f'All retry attempts failed, old data for {typeid} not found')

    def compare_jsons(orig, new):
        if orig == new:
            return None
        if len(orig) != len(new):
            print('json structure is not comparable')
            return None
        diff_list = []
        for typeid in orig.keys():
            lowest_price_order = None
            for order in orig[typeid].keys():
                old_vol = orig[typeid][order]['volume_remain']
                new_vol = 0
                if order in new[typeid].keys():                
                    new_vol = new[typeid][order]['volume_remain']
                # Checking for expired orders:
                elif time_conv(orig[typeid][order]['Expires'], flags=['header']) > time_conv(orig[typeid][order]['issued'], flags=['order'], offset=orig[typeid][order]['duration']):
                    break
                if old_vol > new_vol:
                    if not lowest_price_order:
                        lowest_price_order = min(orig[typeid].values(), key=lambda d: d['price'])['order_id']
                    cheapest = orig[typeid][order]['order_id'] == lowest_price_order
                    station_name, station_type = name_id_lookup(
                        station=orig[typeid][order]['location_id'])
                    order_last_seen = time_conv(
                        orig[typeid][order]['Last-Modified'], flags=['header', 'delta'])
                    diff_list.append(
                        {'name': name_id_lookup(id=typeid), 'name_id': typeid, 'old_vol': old_vol, 'new_vol': new_vol, 'price': human_format(orig[typeid][order]['price']), 'station_name': station_name, 'station_type': station_type, 'region_id': REGIONLIMIT, 'cheapest': cheapest, 'order_age': order_last_seen, 'evetime': time_conv(orig[typeid][order]['Last-Modified'], flags=['header', 'ret_str'])})
        return diff_list


    id_from_names = load_names('names')
    id_list = []
    for i in id_from_names:
        id_list.append(i['typeID'])
    orig = load_data('data_esi')
    new = {}
    downloadThreads = []
    for i in id_list:
        downloadThread = threading.Thread(target=get_data_json, args=(i, ))
        downloadThreads.append(downloadThread)
        downloadThread.start()

    # Wait for all threads to end.
    for downloadThread in downloadThreads:
        downloadThread.join()

    with open('json/data_esi.json', 'w') as fp:
        json.dump(new, ensure_ascii=False, indent=4, fp=fp)
    # For some reason dict doesn't works without reloading from json?
    new = load_data('data_esi')
    if orig and new:
        return compare_jsons(orig, new)


async def as_market_info():
    async def get_data_json(typeid=None):
        url_str = (
            f"https://esi.evetech.net/latest/markets/{REGIONLIMIT}/orders/?datasource=tranquility&order_type=sell&page=1&type_id={typeid}")
        use_headers = {'User-Agent': 'XYZ/3.0'}
        async with aiohttp.ClientSession(headers=use_headers) as session:
            async with session.get(url_str) as response:
                headers = response.headers
                load = await response.json()
                item_orders = {}
                for order in load:
                    if USESYSTEM == 0 or order['system_id'] == USESYSTEM:
                        order['Expires'] = headers['Expires']
                        order['Last-Modified'] = headers['Last-Modified']
                        item_orders[order['order_id']] = order
                new[typeid] = item_orders

    async def compare_jsons(orig, new):
        if orig == new:
            return None
        if len(orig) != len(new):
            print('json structure is not comparable')
            return None
        diff_list = []
        for typeid in orig.keys():
            lowest_price_order = None
            for order in orig[typeid].keys():
                old_vol = orig[typeid][order]['volume_remain']
                new_vol = 0
                if order in new[typeid].keys():                
                    new_vol = new[typeid][order]['volume_remain']
                # Checking for expired orders:
                elif time_conv(orig[typeid][order]['Expires'], flags=['header']) > time_conv(orig[typeid][order]['issued'], flags=['order'], offset=orig[typeid][order]['duration']):
                    break
                if old_vol > new_vol:
                    if not lowest_price_order:
                        lowest_price_order = min(orig[typeid].values(), key=lambda d: d['price'])['order_id']
                    cheapest = orig[typeid][order]['order_id'] == lowest_price_order
                    station_name, station_type = name_id_lookup(
                        station=orig[typeid][order]['location_id'])
                    order_last_seen = time_conv(
                        orig[typeid][order]['Last-Modified'], flags=['header', 'delta'])
                    diff_list.append(
                        {'name': name_id_lookup(id=typeid), 'name_id': typeid, 'old_vol': old_vol, 'new_vol': new_vol, 'price': human_format(orig[typeid][order]['price']), 'station_name': station_name, 'station_type': station_type, 'region_id': REGIONLIMIT, 'cheapest': cheapest, 'order_age': order_last_seen, 'evetime': time_conv(orig[typeid][order]['Last-Modified'], flags=['header', 'ret_str'])})
        return diff_list


    id_from_names = load_names('names')
    id_list = []
    for i in id_from_names:
        id_list.append(i['typeID'])
    orig = load_data('data_esi')
    new = {}
    tasks = []
    for i in id_list:
        task = asyncio.create_task(get_data_json(i))
        tasks.append(task)
    await asyncio.gather(*tasks)
    with open('json/data_esi.json', 'w') as fp:
        json.dump(new, ensure_ascii=False, indent=4, fp=fp)
    # For some reason dict doesn't works without reloading from json?
    new = load_data('data_esi')
    if orig and new:
        return await compare_jsons(orig, new)


def orders_status():
    orig = load_data('data_esi')
    sum = 0
    active_orders = []
    for typeid in orig.keys():
        volume = 0
        price = []
        order_last_seen = None
        for order in orig[typeid].keys():
            volume += orig[typeid][order]['volume_remain']
            price.append(orig[typeid][order]['price'])
            if order_last_seen == None:
                order_last_seen = time_conv(
                    orig[typeid][order]['Last-Modified'], flags=['header', 'delta'])
        if len(orig[typeid]) > 0:
            sum += volume
            active_orders.append({'typeName': name_id_lookup(
                id=typeid), 'volume': volume, 'price': human_format(min(price)), 'timedelta': order_last_seen})
    sorted_orders = sorted(
        active_orders, key=lambda d: d['volume'], reverse=True)
    return sorted_orders, sum

# import time
# start_time = time.time()

# with open('json/data_esi.json', 'r') as json_data:
#             orig = json.load(json_data)
# with open('json/data_esi copy.json', 'r') as json_data:
#             new = json.load(json_data)

# print("--- %s seconds ---" % (time.time() - start_time))
