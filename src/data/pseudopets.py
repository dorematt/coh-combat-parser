"""
Pseudopets in City of Heroes are powers that summon entities that act like pets but are technically not classified as pets in the game's mechanics.
When a power is matched to a pseudopet, all damage and effects will be rolled into an ability of the same name from the character.
"""
PSEUDOPETS = ["Caltrops", "Lightning Rod", "Whirlwind", "Omega Maneuver", "Poison Trap", "Poison Gas", "Detonator", "Trip Mine", "Triage Beacon", "Oil Slick", " Oil Slick Arrow", "Rain of Fire", "Tar Patch",
              "Burn", "Water Spout", "Sleet", "Freezing Rain", "Faraday Cage", "Enflame", "Incandescence", 
              
              
              "Ion Core Final Judgement", "Ion Core Judgement", "Ion Judgement", "Ion Partial Core Judgement", "Ion Partial Radial Judgement", "Ion Radial Final Judgement", "Ion Radial Judgement", "Ion Total Core Judgement", "Ion Total Radial Judgement",
              "Chain Induction", "Chain Induction Jump 1","Chain Induction Jump 2","Chain Induction Jump 3","Chain Induction Jump 4","Chain Induction Jump 5","Chain Induction Jump 6","Chain Induction Jump 7","Chain Induction Jump 8","Chain Induction Jump 9","Chain Induction Jump 10"]




def is_pseudopet(pet_name):
    return pet_name in PSEUDOPETS

