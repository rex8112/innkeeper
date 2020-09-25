import adventure

def print_status_effects(adv: adventure.Player):
    info = f'{adv.name}: HP: {adv.health}\nParmor: {float(adv.mods.get("parmor", 0))}\n'
    for status in adv.status_effects.values():
        effects = ''
        for e in status.effects:
            effects += f'{e.modifier_id}: {e.value} | {"%" if e.effect_type == 1 else "0"}\n'
        round_effects = ''
        for e in status.round_effects:
            round_effects += f'{e.modifier_id}: {e.value} | {"%" if e.effect_type == 1 else "0"}\n'
        info += (
            f'{status.name} | {status.potency} | {status.lifespan}\n'
            f'Effects:\n{effects}\n'
            f'Round Effects:\n{round_effects}\n'
        )
    info += '----------\n'
    print(info)

a = adventure.Player(180067685986467840)
s = adventure.StatusEffect('poison', 0.5)
s1 = adventure.StatusEffect('poison', 0.5)
s2 = adventure.StatusEffect('poison', 0.5)
s3 = adventure.StatusEffect('poison', 0.5)
a.process_per_round()
a.add_status_effect(s)
print_status_effects(a)
a.process_per_round()
a.add_status_effect(s1)
print_status_effects(a)
a.process_per_round()
a.add_status_effect(s2)
print_status_effects(a)
a.process_per_round()
a.add_status_effect(s3)
print_status_effects(a)
a.process_per_round()
print_status_effects(a)
a.process_per_round()
print_status_effects(a)
a.process_per_round()
print_status_effects(a)