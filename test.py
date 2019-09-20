import adventureController as ac

def output(x):
  print('{}: Level {} {} {} with {} XP'.format(x.name,x.level,x.race,x.cls, x.xp))
  print('{} STR, {} DEX, {} CON, {} INT, {} WIS, {} CHA'.format(x.rawStrength,x.rawDexterity,x.rawConstitution,x.rawIntelligence,x.rawWisdom,x.rawCharisma))
  print('{} MH, {} OH, {} HELM, {} ARM, {} GLV, {} BTS'.format(x.mainhand.name,x.offhand.name,x.helmet.name,x.armor.name,x.gloves.name,x.boots.name))
  print('Inventory: {}'.format(x.inventory))
  print('Skills: {}'.format(x.skills))

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