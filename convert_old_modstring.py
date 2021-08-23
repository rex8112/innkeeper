from adventure.modifiers import ModifierString
from json.decoder import JSONDecodeError
import adventure
import json


def convert_old_modstring(mod_string):
    if mod_string == '':
        return []
    mods = []
    mod_string_list = mod_string.split('|')
    for mod in mod_string_list:
        key, value_string = tuple(mod.split(':'))
        min_string, max_string = tuple(value_string.split('/'))
        min_value, min_per_level = tuple(min_string.split('+'))
        max_value, max_per_level = tuple(max_string.split('+'))
        final_mod = adventure.ModifierString(id=key, min_value=float(min_value), min_value_scale=float(min_per_level), max_value=float(max_value), max_value_scale=float(max_per_level))
        
        mods.append(final_mod)
    return mods

def convert_old_reqstring(req_string):
    if req_string == '':
        return []
    reqs = []
    req_string_list = req_string.split('|')
    for req in req_string_list:
        key, value_string = tuple(req.split(':'))
        value, value_per_level = tuple(value_string.split('+'))
        final_req = adventure.ModifierString(id=key, value=float(value), value_scale=float(value_per_level))
        reqs.append(final_req)
    return reqs

def convert_old_dmgstring(dmg_string):
    if dmg_string == '':
        return []
    dmgs = []
    damage_list = dmg_string.split('|')
    for d in damage_list:
        scalars = {}
        damage_type, values = tuple(d.split(':'))
        values_list = values.split(',')
        base, per_level = values_list[0].split('+')
        if len(values_list) > 1:
            scales = values_list[1:]
            for s in scales:
                attribute, amount = tuple(s.split('.'))
                scalars[attribute] = float(amount)
        dmg_dict = {
            'id': damage_type,
            'value': float(base),
            'value_scale': float(per_level),
        }
        dmg_dict = {**dmg_dict, **scalars}
        ds = adventure.ModifierString(**dmg_dict)
        dmgs.append(ds)
    return dmgs



with adventure.Database() as db:
    for row in db.get_base_equipment():
        update_dict = {}
        mod_string = row['startingModString']
        try:
            mod_string = json.loads(mod_string)
            mods = [ModifierString(**x) for x in mod_string]
        except JSONDecodeError:
            mods = convert_old_modstring(mod_string)
        startingModString = adventure.dumps(mods)
        update_dict['startingModString'] = startingModString

        mod_string = row['randomModString']
        try:
            mod_string = json.loads(mod_string)
            mods = [ModifierString(**x) for x in mod_string]
        except JSONDecodeError:
            mods = convert_old_modstring(mod_string)
        randomModString = adventure.dumps(mods)
        update_dict['randomModString'] = randomModString
        
        req_string = row['requirementString']
        try:
            req_string = json.loads(req_string)
            reqs = [ModifierString(**x) for x in req_string]
        except JSONDecodeError:
            reqs = convert_old_reqstring(req_string)
        requirementString = adventure.dumps(reqs)
        update_dict['requirementString'] = requirementString

        dmg_string = row['damageString']
        try:
            dmg_string = json.loads(dmg_string)
            dmgs = [ModifierString(**x) for x in dmg_string]
        except JSONDecodeError:
            dmgs = convert_old_dmgstring(dmg_string)
        damageString = adventure.dumps(dmgs)
        update_dict['damageString'] = damageString

        skills = row['skills']
        try:
            skills = json.loads(skills)
        except JSONDecodeError:
            if skills == '':
                skills = []
            else:
                skills = skills.split(',')
                skills = [skill.strip() for skill in skills]
            skills = adventure.dumps(skills)
            update_dict['skills'] = skills
        
        if update_dict:
            db.update_base_equipment(row['indx'], **update_dict)
