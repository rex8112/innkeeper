import logging
import semantic_version
import sys

from ConfigObject import ConfigObject

logger = logging.getLogger('configLoader')
config = ConfigObject(filename = 'config.ini')

try: ##Check if config.ini exist, if not, create a new file and kill the program
  f = open('config.ini')
  f.close()
except IOError as e:
  f = open('config.ini', 'w+')
  f.close()
  logger.critical('config.ini not found, generating one now. Please fill it in.')
  config['settings']['token'] = ''
  config['settings']['ownerID'] = '180067685986467840'
  config['db']['host'] = 'localhost'
  config['db']['port'] = '3306'
  config['db']['user'] = 'root'
  config['db']['pass'] = ''
  config['db']['dbname'] = 'innkeeper'
  config['blueprint']['host'] = 'fwts.ddns.net'
  config['blueprint']['port'] = '3316'
  config['blueprint']['user'] = 'blueprintViewer'
  config['blueprint']['pass'] = '6IPivu'
  config['blueprint']['dbname'] = 'innkeeper_static'
  config.write()
  sys.exit()

class settings:
  token = config['settings']['token']
  owner = config['settings']['ownerID'].as_int()
  dbhost = config['db']['host']
  dbport = config['db']['port'].as_int()
  dbname = config['db']['dbname']
  dbuser = config['db']['user']
  dbpass = config['db']['pass']
  blueprinthost = config['blueprint']['host']
  blueprintport = config['blueprint']['port'].as_int()
  blueprintname = config['blueprint']['dbname']
  blueprintuser = config['blueprint']['user']
  blueprintpass = config['blueprint']['pass']