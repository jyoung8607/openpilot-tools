#!/usr/bin/env python3
import sys
import os
import getopt
import json
import requests
import urllib.parse as urlparse

UNLOGGER_DATA_DEFAULT = "/home/batman/unlogger_data"
COMMA_API_HOST = "https://api.commadotai.com"

def progressbar(it, prefix="", size=60, file=sys.stderr):
  count = len(it)
  def show(j):
    x = int(size*j/count)
    file.write("%s[%s%s] %i/%i\r" % (prefix, "#"*x, "."*(size-x), j, count))
    file.flush()
  show(0)
  for i, item in enumerate(it):
    yield i, item
    show(i+1)
  file.write("\n")
  file.flush()

def cache_raw_driving_data_json(route_dir, jwt, route):
  url = COMMA_API_HOST + "/v1/route/" + urlparse.quote(route) + "/files"
  auth_token = 'JWT ' + jwt

  raw_data_json = requests.get(url, headers={'Authorization': auth_token}).json()

  with open(os.path.join(route_dir, "files.json"), 'w') as raw_data_json_f:
    json.dump(raw_data_json, raw_data_json_f, indent=4)

  return raw_data_json

def cache_raw_signed_url(signed_url, filename):
  req = requests.get(signed_url)

  with open(filename, 'wb') as f:
    f.write(req.content)

  return

def cache_raw_file_set(dongle_dir, fileset):
  for i, item in progressbar(raw_driving_data_json[fileset], "Downloading {:8} ".format(fileset), 40):
    parsed_url = urlparse.urlparse(item)
    rscd = urlparse.parse_qs(parsed_url.query)['rscd'][0]
    filename = os.path.join(dongle_dir, rscd.split('=')[1])
    cache_raw_signed_url(item, filename)

  return

def download_route(storage_dir, route, fileset):
  route_split = route.split('|')
  dongle = route_split[0]
  drive = route_split[1]

  print("Dongle: %s" % dongle)
  print("Drive:  %s" % drive)
  print("")

  if fileset['qlogs'] is None and fileset['logs'] is None:
    print("ERROR: No data found for the specified drive!")
    sys.exit(2)

  for fileset in ['qlogs', 'logs', 'cameras', 'qcameras', 'dcameras']:
    if not raw_driving_data_json[fileset]:
      print(f"No {fileset} available to download.")
    else:
      cache_raw_file_set(storage_dir, fileset)
  print("Done!")

def print_help():
  print("Usage: download.py --route=\"[route_name]\"\n")
  print("Example: download.py --route=\"269e9812ad3ae3582|2020-01-01--15-58-02\"")
  print("Remove any trailing segment ID (like --0). All segments in the route will be")
  print("downloaded to a directory specified by env variable UNLOGGER_DATA, defaulting")
  print("to %s if unset." % UNLOGGER_DATA_DEFAULT)
  print("Environment variable COMMA_API_JWT must be set to access the Comma drive data")
  print("API. Get a token using the instructions here:")
  print("https://api.comma.ai/#authentication")

if __name__ == "__main__":
  unix_options = "hr"
  gnu_options = ["help", "route="]
  argument_list = sys.argv[1:]

  override_unlogger_data = os.environ.get('UNLOGGER_DATA')
  storage_dir = override_unlogger_data if override_unlogger_data is not None else UNLOGGER_DATA_DEFAULT

  try:
    arguments, values = getopt.getopt(argument_list, unix_options, gnu_options)
  except getopt.error as err:
    print(str(err))
    print_help()
    sys.exit(2)

  if not os.path.isdir(storage_dir):
    print("ERROR: Storage directory %s does not exist or access not permitted!\n" % storage_dir)
    print_help()
    sys.exit(2)

  comma_api_jwt = os.environ.get('COMMA_API_JWT')
  if comma_api_jwt is None:
    print("ERROR: Environment variable COMMA_API_JWT is missing!\n")
    print_help()
    sys.exit(2)

  for cur_arg, cur_arg_val in arguments:
    if cur_arg in ('-h', '--help'):
      print_help()
      sys.exit(0)
    elif cur_arg in ('-r', '--route'):
      raw_driving_data_json = cache_raw_driving_data_json(storage_dir, comma_api_jwt, cur_arg_val)
      download_route(storage_dir, cur_arg_val, raw_driving_data_json)
      sys.exit(0)

  print("ERROR: No arguments specified!\n")
  print_help()
