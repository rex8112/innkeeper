import adventureController as ac
import tools.database as db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='test.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler2 = logging.FileHandler(filename='latest.log', encoding='utf-8', mode='w')
handler2.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

db.initDB()

def output(x):
  print('----------')
  print('{}: Level {} {} {} with {} XP'.format(x.name,x.level,x.race,x.cls, x.xp))
  print('{} STR, {} DEX, {} CON, {} INT, {} WIS, {} CHA'.format(x.rawStrength,x.rawDexterity,x.rawConstitution,x.rawIntelligence,x.rawWisdom,x.rawCharisma))
  print('{} MH, {} OH, {} HELM, {} ARM, {} GLV, {} BTS'.format(x.mainhand.name,x.offhand.name,x.helmet.name,x.armor.name,x.gloves.name,x.boots.name))
  print('Inventory: {}'.format(x.inventory))
  print('Skills: {}'.format(x.skills))
  print('----------')

def equipout(z: ac.Equipment):
  print('----------')
  print('{}: {} {}'.format(z.id, z.rarity, z.name))
  print(z.flavor)
  print('Mods: {}'.format(z.mods))
  print('Slot: {}. Price: {}'.format(z.slot, z.price))
  print('----------')

logger.info('Beginning Test')
e = ac.Enemy()
e.generate_new_elite(3)
e.calculate()
save = e.save()
print(save)
b = ac.Enemy(raw_data=save)
print(b.save())

m = ac.Modifier('test', 1)
n = ac.Modifier('test', 1)
g = m + n
m += n
print(m.value)