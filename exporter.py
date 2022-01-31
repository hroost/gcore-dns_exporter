# -*- encoding: utf-8 -*-
#
# pip install requests
# pip install prometheus_client
#

from prometheus_client import start_http_server
from prometheus_client import Gauge
from prometheus_client import REGISTRY, PROCESS_COLLECTOR, PLATFORM_COLLECTOR

import time
import os
import sys
import requests
import datetime

# -------------------------------------------------------
# Reset local cache
# -------------------------------------------------------
def resetCacheState(cache):
  for zone in cache:
    GaugeZoneStats.labels(zone).set(0)

# -------------------------------------------------------
# Get zones list
# -------------------------------------------------------
def getZones():
  try:
    r = requests.get(gcore_dns_api_url + '/zones?limit=' + str(gcore_dns_api_zones_limit), headers=headers, timeout=5)
    return r.json()
  except Exception as e:
    sys.stderr.write('error:'+str(e))
    exit(1)

# -------------------------------------------------------
# Get zone stats
# -------------------------------------------------------
def getZoneStats(zones, dt_from, dt_to, cache):
  sys.stdout.write('Zones count: ' + str(zones['total_amount']) + ' [limit: ' + str(gcore_dns_api_zones_limit)+ ']\n')

  for zone in zones['zones']:
    # Avoid rate limiting. See https://apidocs.gcorelabs.com/account#section/Rate-Limits
    time.sleep(0.5)
    zone = zone['name']
    try:
      params = {
        'granularity': '1h',
        'from': dt_from,
        'to': dt_to
        }
      r = requests.get(gcore_dns_api_url + '/zones/' + zone + '/statistics', params=params, headers=headers, timeout=5)
      zone_stats_total = r.json()['total']
      sys.stdout.write('* zone: ' + str(zone) + ' Reqs: ' + str(zone_stats_total) + '\n')
      GaugeZoneStats.labels(zone).set(zone_stats_total)
      cache[zone] = True
    except Exception as e:
      sys.stderr.write('error:'+str(e))
      exit(1)

# -------------------------------------------------------
# Get all zones stats
# -------------------------------------------------------
def getAllZonesStats(dt_from, dt_to):
  try:
    params = {
      'granularity': '1h',
      'from': dt_from,
      'to': dt_to
      }
    r = requests.get(gcore_dns_api_url + '/zones/all/statistics', params=params, headers=headers, timeout=5)
    zones_stats_total = r.json()['total']
    sys.stdout.write('All zones requests since midnight: ' + str(zones_stats_total) + '\n')
    GaugeAllZonesStats.set(zones_stats_total)
  except Exception as e:
    sys.stderr.write('error:'+str(e))
    exit(1)


# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
def main():

  # Start up the server to expose the metrics.
  start_http_server(port)

  cache = {}

  # Generate some requests.
  while True:
      zones = getZones()
      # Reset internal cache
      resetCacheState(cache)
      dt_from = int(datetime.datetime.combine(datetime.datetime.today(), datetime.time.min).timestamp()) # timestamp of today midnight
      dt_to = int(datetime.datetime.now().timestamp()) # timestamp now
      getZoneStats(zones, dt_from, dt_to, cache)
      getAllZonesStats(dt_from, dt_to)
      time.sleep(interval)

# -------------------------------------------------------
# RUN
# -------------------------------------------------------

# http port - default 9886
port = int(os.getenv('PORT', 9886))

# Refresh interval between collects in seconds - default 300
interval = int(os.getenv('INTERVAL', 300))

gcore_dns_api_url = os.getenv('GCORE_DNS_API_URL', 'https://dnsapi.gcorelabs.com/v2')
gcore_dns_api_key = os.getenv('GCORE_DNS_API_KEY', None)
# Amount of zones for getZones() - default 999
gcore_dns_api_zones_limit = int(os.getenv('GCORE_DNS_API_ZONES_LIMIT', 999))

if not gcore_dns_api_key:
  sys.stderr.write("Application key is required please set GCORE_DNS_API_KEY environment variable.\n")
  exit(1)

headers = {'Authorization':'APIKey ' + gcore_dns_api_key}

# Show init parameters
sys.stdout.write('----------------------\n')
sys.stdout.write('Init parameters\n')
sys.stdout.write('port: ' + str(port) + '\n')
sys.stdout.write('interval: ' + str(interval) + 's\n')
sys.stdout.write('----------------------\n')

# Disable default python metrics
REGISTRY.unregister(PROCESS_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)

# Create gauge
GaugeZoneStats = Gauge('gcore_dns_zone_requests', 'Amount of requests per zone since midnight', ['zone'])
GaugeAllZonesStats = Gauge('gcore_dns_all_zones_requests', 'Amount of requests from all zones since midnight')

if __name__ == '__main__':
  main()
