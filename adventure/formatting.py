class Formatting:
    emojis = {}

    @staticmethod
    def get_rarity_emoji(rarity):
        if rarity == 0:
            return Formatting.emojis.get('common_rarity', '')
        elif rarity == 1:
            return Formatting.emojis.get('uncommon_rarity', '')
        elif rarity == 2:
            return Formatting.emojis.get('rare_rarity', '')
        elif rarity == 3:
            return Formatting.emojis.get('epic_rarity', '')
        elif rarity == 4:
            return Formatting.emojis.get('legendary_rarity', '')

    @staticmethod
    def get_difference_emoji(value: int):
        if value >= 0:
            return Formatting.emojis.get('positive_triangle', '')
        else:
            return Formatting.emojis.get('negative_triangle', '')