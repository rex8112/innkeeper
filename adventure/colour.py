import discord

class Colour:
    creationColour = discord.Colour(0x00DBEB)
    errorColour = discord.Colour(0xFF0000)
    successColour = discord.Colour(0x0DFF00)
    infoColour = discord.Colour(0xFFA41C)
    combatColour = discord.Colour(0xFF0000)
    commonColour = discord.Colour(0xFCFCFC)
    uncommonColour = discord.Colour(0x1EFF00)
    rareColour = discord.Colour(0x0070DD)
    epicColour = discord.Colour(0xA335EE)
    legendaryColour = discord.Colour(0xFF8000)

    @staticmethod
    def get_rarity_colour(rarity: str):
        if isinstance(rarity, str):
            rarity = rarity.lower()
        if rarity == 0 or rarity == 'common':
            return Colour.commonColour
        elif rarity == 1 or rarity == 'uncommon':
            return Colour.uncommonColour
        elif rarity == 2 or rarity == 'rare':
            return Colour.rareColour
        elif rarity == 3 or rarity == 'epic':
            return Colour.epicColour
        elif rarity == 4 or rarity == 'legendary':
            return Colour.legendaryColour