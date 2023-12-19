from sqlalchemy import Column, Integer, String, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from ujson import load
from os import path
# from dbupdate_steps import csv_to_json

Base = declarative_base()


class ServerConfigs(Base):
    __tablename__ = "serverconfigs"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(100), nullable=False)
    channel = Column(Integer, nullable=True, default=None)
    muted = Column(Boolean, default=False)
    neutral_color = Column(String(20), nullable=True, default=None)
    involvedmin = Column(Integer, nullable=True, default=None)

    def __repr__(self) -> str:
        return f"ServerConfig{self.id}, {self.name}, {self.channel}"


class WatchLists(Base):
    __tablename__ = "watchlists"

    server_id = Column(Integer, primary_key=True, autoincrement=False)
    systems = Column(String(5000), nullable=False, default="[]")
    constellations = Column(String(1000), nullable=False, default="[]")
    regions = Column(String(500), nullable=False, default="[]")
    corporations = Column(String(2000), nullable=False, default="[]")
    alliances = Column(String(500), nullable=False, default="[]")
    players = Column(String(1000), nullable=False, default="[]")
    f_corporations = Column(String(1000), nullable=False, default="[]")
    f_alliances = Column(String(500), nullable=False, default="[]")

    def __repr__(self) -> str:
        return f"WatchList:{self.server_id}"


class Ships(Base):
    __tablename__ = "ships"

    id = Column(Integer, primary_key=True, autoincrement=False)
    group_id = Column(Integer, nullable=False)
    name = Column(String(50), nullable=False, unique=True)


class Systems(Base):
    __tablename__ = "systems"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(30), nullable=False, index=True)
    constellation_id = Column(Integer, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"System:{self.id}, {self.name}, {self.constellation_id}"


class Constellations(Base):
    __tablename__ = "constellations"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(30), nullable=False, index=True)
    region_id = Column(Integer, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Constellation:{self.id}, {self.name}, {self.region_id}"


class Regions(Base):
    __tablename__ = "regions"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(30), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Region:{self.id}, {self.name}"


class Corporations(Base):
    __tablename__ = "corporations"

    id = Column(Integer, primary_key=True, autoincrement=False)
    alliance_id = Column(Integer, nullable=True, default=None)
    name = Column(String(51), nullable=False, index=True)
    ticker = Column(String(6), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Corporation:{self.id}, {self.name}:{self.ticker}, Alliance_id:{self.alliance_id}"


class Alliances(Base):
    __tablename__ = "alliances"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(51), nullable=False, index=True)
    ticker = Column(String(6), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Alliance:{self.id}, {self.name}:{self.ticker}"


class Stations(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, autoincrement=False)
    name = Column(String(50), nullable=False, index=True)
    solarSystemID = Column(Integer, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Stations:{self.id}, {self.name}"

class Items(Base):
    __tablename__ = "items"

    typeID = Column(Integer, primary_key=True, autoincrement=False)
    marketGroupID = Column(Integer, nullable=False, index=True)
    typeName = Column(String(50), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Items:{self.typeID}, {self.typeName}"


class MarketGroups(Base):
    __tablename__ = "marketgroups"

    marketGroupID = Column(Integer, primary_key=True, autoincrement=False)
    parentGroupID = Column(Integer, nullable=True, index=True)
    marketGroupName = Column(String(50), nullable=False, index=True)

    def __repr__(self) -> str:
        return f"MarketGroups:{self.marketGroupID}, {self.marketGroupName}"


class Orders(Base):
    __tablename__ = "orders"

    order_id = Column(Integer, primary_key=True, autoincrement=False)
    volume_remain = Column(Integer, nullable=False, index=True)
    duration = Column(Integer, nullable=False, index=False)
    location_id = Column(Integer, nullable=False, index=True)
    price = Column(Float, nullable=False, index=True)
    system_id = Column(Integer, nullable=False, index=True)
    type_id = Column(Integer, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"Orders:{self.order_id}, {self.type_id}"


class MarketWatch(Base):
    __tablename__ = "marketwatch"

    type_id = Column(Integer, primary_key=True, autoincrement=False)
    regionID = Column(Integer, nullable=False, index=True)
    constellationID = Column(Integer, nullable=True, index=False)
    system_id = Column(Integer, nullable=True, index=False)
    location_id = Column(Integer, nullable=True, index=False)
    expires = Column(String(40), nullable=True, index=False)
    last_modified = Column(String(40), nullable=True, index=False)    

    def __repr__(self) -> str:
        return f"Watchlist:{self.type_id}, {self.expires}"


def write_regions_from_json_file(session):
    with open('storage/json/regions.json', 'r') as file:
        obj = load(file)
        for key, value in obj.items():
            entry = Regions(id=key, name=value[0])
            session.add(entry)
    session.commit()


def write_systems_from_json_file(session):
    with open('storage/json/systems.json', 'r') as file:
        obj = load(file)
        for key, value in obj.items():
            entry = Systems(id=key, name=value[0],
                            constellation_id=value[1])
            session.add(entry)
    session.commit()


def write_constellations_from_json_file(session):
    with open('storage/json/constellations.json', 'r') as file:
        obj = load(file)
        for key, value in obj.items():
            entry = Constellations(id=key, name=value[0],
                                   region_id=value[1])
            session.add(entry)
    session.commit()


def write_corporations_from_json_file(session):
    with open('storage/json/corporations.json', 'r') as file:
        obj = load(file)
        for key, value in obj.items():
            entry = Corporations(id=key, name=value[0],
                                 alliance_id=value[1], ticker=value[2])
            session.add(entry)
    session.commit()


def write_alliances_from_json_file(session):
    with open('storage/json/alliances.json', 'r') as file:
        obj = load(file)
        for key, value in obj.items():
            entry = Alliances(id=key, name=value[0], ticker=value[1])
            session.add(entry)
    session.commit()


def write_server_configurations_from_json_file(session):
    with open('storage/json/server_configs.json', 'r') as file:
        obj = load(file)
        for key, value in obj.items():
            entry = ServerConfigs(
                id=key, name=value[0], channel=value[1], muted=value[2], neutral_color=value[3], involvedmin=value[4] if len(value) == 5 else None)
            session.add(entry)
    session.commit()


def write_watchlists_from_json_file(session):
    with open('storage/json/watchlists.json', 'r') as file:
        obj = load(file)
        for key, value in obj.items():
            entry = WatchLists(server_id=key, systems=value[0], constellations=value[1],
                               regions=value[2], corporations=value[3], alliances=value[4], f_corporations=value[5], f_alliances=value[6])
            session.add(entry)
    session.commit()


def write_ships_from_json_file(session):
    with open('storage/json/ships.json', 'r') as file:
        obj = load(file)
        for key, value in obj.items():
            entry = Ships(
                id=key, name=value[0], group_id=value[1])
            session.add(entry)
    session.commit()


def write_stations_from_json_file(session):
    filename = 'staStations'
    # if not path.exists(f"json/{filename}.json"):
    #     csv_to_json(filename)
    with open(f"storage/json/{filename}.json", 'r') as file:
        obj = load(file)
        for _ in obj:
            if _['stationID']:
                entry = Stations(id=_['stationID'], name=_['stationName'],
                                 solarSystemID=_['solarSystemID'])
                session.merge(entry)
    session.commit()


def write_items_from_json_file(session):
    filename = 'invTypes'
    # if not path.exists(f"json/{filename}.json"):
    #     csv_to_json(filename)
    with open(f"storage/json/{filename}.json", 'r', encoding="utf8") as file:
        obj = load(file)
        for _ in obj:
            if _['typeID'].isnumeric() and _['marketGroupID'] and _['published'] == "1":
                entry = Items(typeID=_['typeID'], marketGroupID=_[
                              'marketGroupID'], typeName=_['typeName'])
                session.merge(entry)
    session.commit()


def write_market_groups_from_json_file(session):
    filename = 'invMarketGroups'
    # if not path.exists(f"json/{filename}.json"):
    #     csv_to_json(filename)
    with open(f"storage/json/{filename}.json", 'r') as file:
        obj = load(file)
        for _ in obj:
            if _['marketGroupID'].isnumeric():
                entry = MarketGroups(marketGroupID=_['marketGroupID'], parentGroupID=_[
                                     'parentGroupID'], marketGroupName=_['marketGroupName'])
                session.merge(entry)
    session.commit()


def write_orders_from_json_file(session):
    filename = 'data_esi'
    # if not path.exists(f"json/{filename}.json"):
    #     csv_to_json(filename)
    with open(f"storage/json/{filename}.json", 'r') as file:
        obj = load(file)
        for typeid in obj.keys():
            for order in obj[typeid].keys():
                entry = Orders(order_id=obj[typeid][order]['order_id'], volume_remain=obj[typeid][order]['volume_remain'], duration=obj[typeid][order]['duration'],
                               location_id=obj[typeid][order]['location_id'], price=obj[typeid][order]['price'], system_id=obj[typeid][order]['system_id'], type_id=obj[typeid][order]['type_id'])
                session.merge(entry)
    session.commit()


def create_database():
    if not path.exists('storage/database.db'):
        from commands import Session, engine
        with Session as session:
            Base.metadata.create_all(engine)

            write_systems_from_json_file(session)
            write_constellations_from_json_file(session)
            write_regions_from_json_file(session)
            write_corporations_from_json_file(session)
            write_alliances_from_json_file(session)
            write_server_configurations_from_json_file(session)
            write_watchlists_from_json_file(session)
            write_ships_from_json_file(session)
            write_stations_from_json_file(session)
            write_items_from_json_file(session)
            write_market_groups_from_json_file(session)
        print("Database Created!")
