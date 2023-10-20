import random
import re

def handle_response(message) -> tuple:
    p_message = message.lower()
    pv = False
    if p_message.startswith("pv "):
        pv = True
        p_message = p_message[3:]
    match = re.match(r'^roll (\d{1,2})?d(\d{1,3})(\+(\d{1,2})?d(\d{1,3}))?([+-]\d+)?$', p_message)
    if match:
        num_dice_1 = int(match.group(1) or 1)
        sides_1 = int(match.group(2))
        num_dice_2 = int(match.group(4)) if match.group(4) else 0
        sides_2 = int(match.group(5)) if match.group(5) else 0
        mod = int(match.group(6) or 0)
        rolls_1 = [random.randint(1, sides_1) for _ in range(num_dice_1)]
        rolls_2 = [random.randint(1, sides_2) for _ in range(num_dice_2)]
        total = sum(rolls_1) + sum(rolls_2) + mod
        rolls_text = f"Rolls: 🎲{rolls_1}🎲"
        if num_dice_2 > 0:
            rolls_text += f" + 🎲{rolls_2}🎲"
        return f"{rolls_text}, total: {total}", pv
    if p_message == '!secret':
        return   ("`Este es un mensaje de ayuda.`", pv)
    if p_message == 'wotc':
        return  ("`#OpenDND`", pv)
    return None, False