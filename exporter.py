# -*- encoding: utf-8 -*-
#
# pip install requests
# pip install prometheus_client
#

import datetime
import os
import sys
import time

import requests
from prometheus_client import (PLATFORM_COLLECTOR, PROCESS_COLLECTOR, REGISTRY,
                               Gauge, start_http_server)


# -------------------------------------------------------
# Get zones list
# -------------------------------------------------------
def getZones(timeout: int):
    url = gcore_dns_api_url + "/zones?limit=" + str(gcore_dns_api_zones_limit)
    try:
        r = requests.get(
            url,
            headers=headers,
            timeout=timeout,
        )
        return r.json()
    except Exception as e:
        sys.stderr.write("Error during zone retrieval on " + url)
        sys.stderr.write("error:" + str(e))
        return None


# -------------------------------------------------------
# Get zone stats
# -------------------------------------------------------
def getZoneStats(zones: str, dt_from: int, dt_to: int, timeout: int):
    sys.stdout.write(
        "Zones count: "
        + str(zones["total_amount"])
        + " [limit: "
        + str(gcore_dns_api_zones_limit)
        + "]\n"
    )

    for zone in zones["zones"]:
        # Avoid rate limiting. See https://api.gcore.com/docs/iam#section/Rate-limits-and-throttling
        time.sleep(1)
        zone = zone["name"]
        url = gcore_dns_api_url + "/zones/" + zone + "/statistics"
        try:
            params = {"granularity": "1h", "from": dt_from, "to": dt_to}
            r = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=timeout,
            )
        except Exception as e:
            sys.stderr.write("Error during zone " + zone + " stat retrieval on " + url)
            sys.stderr.write("error:" + str(e))
            continue

        zone_stats_total = r.json()["total"]
        sys.stdout.write(
            "* zone: " + str(zone) + " Reqs: " + str(zone_stats_total) + "\n"
        )
        GaugeZoneStats.labels(zone).set(zone_stats_total)


# -------------------------------------------------------
# Get all zones stats
# -------------------------------------------------------
def getAllZonesStats(dt_from: int, dt_to: int, timeout: int):
    url = gcore_dns_api_url + "/zones/all/statistics"
    try:
        params = {"granularity": "1h", "from": dt_from, "to": dt_to}
        r = requests.get(
            url,
            params=params,
            headers=headers,
            timeout=timeout,
        )
        zones_stats_total = r.json()["total"]
        sys.stdout.write(
            "All zones requests since midnight: " + str(zones_stats_total) + "\n"
        )
        GaugeAllZonesStats.set(zones_stats_total)
    except Exception as e:
        sys.stderr.write("Error during all zone stat retrieval on " + url)
        sys.stderr.write("error:" + str(e))
        return None


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():

    # Start up the server to expose the metrics.
    start_http_server(port)

    # Generate some requests.
    while True:
        zones = getZones(timeout)
        if zones:
            # Reset per zone metrics
            GaugeZoneStats.clear()
            dt_from = int(
                datetime.datetime.combine(
                    datetime.datetime.today(), datetime.time.min
                ).timestamp()
            )  # timestamp of today midnight
            dt_to = int(datetime.datetime.now().timestamp())  # timestamp now

            getZoneStats(zones, dt_from, dt_to, timeout)
            getAllZonesStats(dt_from, dt_to, timeout)
            time.sleep(interval)


# -------------------------------------------------------
# RUN
# -------------------------------------------------------

# http port - default 9886
port = int(os.getenv("PORT", 9886))

# Refresh interval between collects in seconds - default 300
interval = int(os.getenv("INTERVAL", 300))
timeout = int(os.getenv("TIMEOUT", 10))

gcore_dns_api_url = os.getenv("GCORE_DNS_API_URL", "https://api.gcore.com/dns/v2")
gcore_dns_api_key = os.getenv("GCORE_DNS_API_KEY", None)
# Amount of zones for getZones() - default : 999
gcore_dns_api_zones_limit = int(os.getenv("GCORE_DNS_API_ZONES_LIMIT", 999))

if not gcore_dns_api_key:
    sys.stderr.write(
        "Application key is required please set GCORE_DNS_API_KEY environment variable.\n"
    )
    exit(1)

headers = {"Authorization": "APIKey " + gcore_dns_api_key}

# Show init parameters
sys.stdout.write("----------------------\n")
sys.stdout.write("Init parameters\n")
sys.stdout.write("port: " + str(port) + "\n")
sys.stdout.write("interval: " + str(interval) + "s\n")
sys.stdout.write("----------------------\n")

# Disable default python metrics
REGISTRY.unregister(PROCESS_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)

# Create gauge
GaugeZoneStats = Gauge(
    "gcore_dns_zone_requests", "Amount of requests per zone since midnight", ["zone"]
)
GaugeAllZonesStats = Gauge(
    "gcore_dns_all_zones_requests", "Amount of requests from all zones since midnight"
)

if __name__ == "__main__":
    main()
