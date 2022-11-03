import re
import requests
from datetime import timedelta
import datetime
import asyncio
from kafka import KafkaProducer


def getBikeRecords(limite=-1):
    yesterday = (datetime.datetime.now() - timedelta(days=1)).strftime(
        "%Y-%m-%d %H:00:00"
    )
    print("call for time: " + yesterday)
    req = (
        "https://opendata.paris.fr/api/v2/catalog/datasets/comptage-velo-donnees-compteurs/exports/json?select=%2A&where=date%20%3D%20date%27"
        + yesterday
        + "%27&limit="
        + str(limite)
        + "&offset=0&timezone=UTC"
    )
    response = requests.get(req)

    if response.status_code == 200:
        print("Success!")
    else:
        print("Not Found.")
    print("number of results", len(response.json()))
    return response.json()


def getCarRecords(limite=-1):
    yesterday = (datetime.datetime.now() - timedelta(days=1)).strftime(
        "%Y-%m-%d %H:00:00"
    )
    print("call for time: " + yesterday)
    req = (
        "https://opendata.paris.fr/api/v2/catalog/datasets/comptages-routiers-permanents/exports/json?select=%2A&where=t_1h%20%3D%20date%27"
        + yesterday
        + "%27&limit="
        + str(limite)
        + "&offset=0&timezone=UTC"
    )
    response = requests.get(req)

    if response.status_code == 200:
        print("Success!")
    else:
        print("Not Found. code: " + str(response.status_code))
        print(response.text)
    print("number of results", len(response.json()))
    return response.json()


def bikeStream(bike_records, background_tasks, kafka_producer):
    for record in bike_records:
        task = asyncio.ensure_future(simulateBikeStream(record, kafka_producer))
        background_tasks.append(task)


def carStream(car_records, background_tasks, kafka_producer):
    for record in car_records:
        task = asyncio.ensure_future(simulateCarStream(record, kafka_producer))
        background_tasks.append(task)


async def simulateBikeStream(record, kafka_producer):
    n_counter = int(record["sum_counts"])
    if n_counter > 0:
        for i in range(n_counter):
            sleep_time = 3500 / n_counter
            print(f"Bike {str(i)} / {n_counter} detected at {record['nom_compteur']}")
            kafka_producer.send("velo", record["nom_compteur"].encode("utf-8"))
            await asyncio.sleep(sleep_time)
    return 0


async def simulateCarStream(record, kafka_producer):
    if record["q"]:
        n_counter = int(record["q"])
        if n_counter > 0:
            for i in range(n_counter):
                sleep_time = 3600 / n_counter
                print(
                    f"Car {str(i)} / {n_counter} detected at {record['libelle']} from {record['libelle_nd_amont']} to {record['libelle_nd_aval']} "
                )
                await asyncio.sleep(sleep_time)
    return 0


async def main():
    bike_records = getBikeRecords()
    # car_records = getCarRecords()
    background_tasks = []
    kafka_producer = KafkaProducer(bootstrap_servers="localhost:9092")
    bikeStream(bike_records, background_tasks, kafka_producer)
    # carStream(car_records, background_tasks, kafka_producer)
    res = await asyncio.gather(*background_tasks)
    return res


asyncio.run(main())
