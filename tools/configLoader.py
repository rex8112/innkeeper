import logging
import semantic_version
import tools.database as db
import sys

from configobj import ConfigObj

logger = logging.getLogger('configLoader')
config = ConfigObj(infile = 'config.ini', write_empty_values = True)

try: ##Check if config.ini exist, if not, create a new file and kill the program
  f = open('config.ini')
  f.close()
except IOError as e:
  f = open('config.ini', 'w+')
  f.close()
  logger.critical('config.ini not found, generating one now. Please fill it in.')
  config['token'] = ''
  config['ownerID'] = '180067685986467840'
  config['dbVersion'] = str(db.database_version)
  config.write()
  sys.exit()

class settings:
  token = config['token']
  owner = config['ownerID']
  current_version = config['dbVersion']