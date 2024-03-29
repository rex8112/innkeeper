import adventureController as ac
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='test.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler2 = logging.FileHandler(filename='latest.log', encoding='utf-8', mode='w')
handler2.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

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
x = ac.Player(8112)
print('Generating New')
if not x.new('Erika', 'Adventurer', 'Human', [14,11,13,9,10,12]):
  x.load()
print('Saving')
x.save()
print('Loading')
x.load()
x.equip(2)
x.unequip('helmet')
output(x)
x.rawStrength = 9
x.rawConstitution = 2
x.rawDexterity = 2
x.name = 'Eric'
x.level = 2
x.xp = 0
x.race = 'Gay'
x.cls = 'Slave'
print('Saving')
x.save()
print('Loading')
x.load()
output(x)

try:
  if x.testingAtt:
    print('I don\'t even know')
  else:
    print('It worked!')
except AttributeError:
    print('This Works Too')

z = ac.Equipment(0)
z.new('Gauntlet', 'A tough right-handed glove.', 'Common', 'ac:6,health:100', 'gloves', 20)
z.load()
equipout(z)
z = ac.Equipment(z.id)
z.name = 'Aids'
z.price = 6969
z.rarity = 'Legendary'
z.slot = 'helmet'
z.mods['aids'] = 1
z.flavor = 'You have AIDS'
z.save()
z.load()
equipout(z)

e = ac.Enemy(0)
e.new('Skeleton Archer', 'Archer', 'Skeleton', [14,11,13,9,10,12], ['Attack','Murder','Kill'], True)
e.save()
e.load()
output(e)
e.rawStrength = 9
e.rawConstitution = 2
e.rawDexterity = 2
e.name = 'Garry'
e.level = 2
e.xp = 321
e.race = 'Straight'
e.cls = 'Master'
e.save()
e.load()
e.calculate()
output(e)

f = ac.Encounter([x], [e])
print(f.players)
print(f.enemies)
print(f.deadPlayers)
print(f.deadEnemies)
for i in range(30):
  f.automatic_turn()
print(f.players)
print(f.enemies)
print(f.deadPlayers)
print(f.deadEnemies)
print(x.health)
print(e.health)

b = ac.RNGDungeon()
b.new(8112, 1,'medium')
b.save()
b.loadActive(8112)
while b.stage <= b.stages and b.active == True:
  while len(b.encounter.enemies) > 0 and len(b.encounter.players) > 0:
    print('--------------------------------New Turn')
    b.encounter.automatic_turn()
  print('----------------------------------New Stage: {} | {.health}'.format(b.stage + 1, b.adv))
  b.nextStage()

print('All Done: {.health}'.format(b.adv))


print(ac.Equipment(1).rarity)

#x.delete()
z.delete()
e.delete()