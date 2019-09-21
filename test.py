import adventureController as ac

def output(x):
  print('{}: Level {} {} {} with {} XP'.format(x.name,x.level,x.race,x.cls, x.xp))
  print('{} STR, {} DEX, {} CON, {} INT, {} WIS, {} CHA'.format(x.rawStrength,x.rawDexterity,x.rawConstitution,x.rawIntelligence,x.rawWisdom,x.rawCharisma))
  print('{} MH, {} OH, {} HELM, {} ARM, {} GLV, {} BTS'.format(x.mainhand.name,x.offhand.name,x.helmet.name,x.armor.name,x.gloves.name,x.boots.name))
  print('Inventory: {}'.format(x.inventory))
  print('Skills: {}'.format(x.skills))

def equipout(z: ac.Equipment):
  print('{}: {} {}'.format(z.id, z.rarity, z.name))
  print(z.flavor)
  print('Mods: {}'.format(z.mods))
  print('Slot: {}. Price: {}'.format(z.slot, z.price))

x = ac.Character(8112)
print('Generating New')
x.new('Erika', 'Adventurer', 'Human', [14,11,13,9,10,12], ['Attack','Murder','Kill'])
print('Saving')
x.save()
print('Loading')
x.load()
output(x)
x.rawStrength = 9
x.rawConstitution = 2
x.rawDexterity = 2
x.name = 'Eric'
x.level = 2
x.xp = 321
x.race = 'Gay'
x.cls = 'Slave'
print('Saving')
x.save()
print('Loading')
x.load()
output(x)
x.delete()

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
