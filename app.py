from flask import Flask, jsonify, render_template, request
import json
from pathlib import Path

app = Flask(__name__, template_folder=".", static_folder=".", static_url_path="/static")
DATA_FILE = Path(__file__).with_name("game_data.json")

# ─────────────────────────────────────────────────────────────────────────────
# GAME DATA  –  All story content, events, choices, endings, and aftermaths.
#
# Four storylines selected from the full design tree:
#   1. The Mountain Feral       (Origin 1)
#   2. Red Ribbon Vanguard      (Origin 3)
#   3. Crane School Assassin    (Origin 4)
#   4. Turtle School Defector   (Origin 5)
#
# Node connection logic (mirrors updatetree.html):
#   Origin → Prologue Choice (stats) →
#   Bridge Choice (auto-derives Alignment) →
#   Crisis Choice/Raditz (auto-derives Ending + Aftermath)
#
# Alignment derivation:  bridge "to-feral"   → Feral Bloodlust
#                        bridge "to-saiyan"  → Saiyan Duty
#                        bridge "to-tyrant"  → Calculated Tyranny
#
# Ending derivation:     crisis "to-saiyan"  → Ending 1 (Loyal Vanguard)
#                        crisis "to-feral"   → Ending 2 (Apex Predator)
#                        crisis "to-tyrant"  → Ending 3 (God-King)
#                        crisis "redemption" → Secret Ending (Shenron's Mercy)
# ─────────────────────────────────────────────────────────────────────────────

STORIES = [
    {
        "id": "mountain_feral",
        "title": "The Mountain Feral",
        "subtitle": "Mount Paozu · Age 749",
        "tagline": "Born wild. Never tamed.",
        "description": (
            "Grandpa Gohan discovers the Saiyan pod but cannot contain the infant warrior. "
            "One full moon is all it takes. Kakarot walks free — and feral."
        ),
        "color": "#e74c3c",
        "icon": "🐾",
        "starting_stats": {"ki": 20, "malice": 50, "infamy": 5, "health": 80},
        "sequence": ["intro", "mf_origin", "mf_prologue", "mf_bridge"],
    },
    {
        "id": "red_ribbon",
        "title": "Red Ribbon Vanguard",
        "subtitle": "RR Headquarters · Age 749",
        "tagline": "Weaponized. Deployed. Unstoppable.",
        "description": (
            "The Red Ribbon Army intercepts the pod. Dr. Gero and Commander Red raise "
            "Kakarot in a militarized compound as a living weapon of mass conquest."
        ),
        "color": "#c0392b",
        "icon": "⚙️",
        "starting_stats": {"ki": 40, "malice": 30, "infamy": 20, "health": 70},
        "sequence": ["intro", "rr_origin", "rr_prologue", "rr_bridge"],
    },
    {
        "id": "crane_school",
        "title": "Crane School Assassin",
        "subtitle": "Crane School · Age 750",
        "tagline": "Precision. Cruelty. Calculated death.",
        "description": (
            "Master Shen senses the alien child's dark potential and trains him alongside "
            "Tien Shinhan and Chiaotzu. The Dodon Ray. The art of silent elimination."
        ),
        "color": "#27ae60",
        "icon": "🏹",
        "starting_stats": {"ki": 35, "malice": 40, "infamy": 10, "health": 75},
        "sequence": ["intro", "cs_origin", "cs_prologue", "cs_bridge"],
    },
    {
        "id": "turtle_defector",
        "title": "Turtle School Defector",
        "subtitle": "Kame House · Age 750",
        "tagline": "Trained. Turned. Unleashed.",
        "description": (
            "Master Roshi attempts to instill discipline. Krillin trains as his classmate. "
            "But Saiyan programming cannot be buried — and when it surfaces, no one is safe."
        ),
        "color": "#e67e22",
        "icon": "🐢",
        "starting_stats": {"ki": 30, "malice": 35, "infamy": 15, "health": 85},
        "sequence": ["intro", "td_origin", "td_prologue", "td_bridge"],
    },
]

EVENTS = {
    # ── Shared intro ─────────────────────────────────────────────────────────
    "intro": {
        "id": "intro",
        "title": "Kakarot's Descent",
        "year": "Age 749",
        "text": (
            "A Saiyan pod tears through Earth's atmosphere like a comet of fire and steel. "
            "Inside, an infant warrior named Kakarot sleeps through reentry — his battle "
            "programming intact, his instincts sharp and unbroken.\n\n"
            "This is not the story of Son Goku. No kind hermit will successfully soothe this "
            "child. No bump on the head will rewrite his nature. The head injury never "
            "happens. What lands on this world today is exactly what the Saiyan race intended "
            "it to be: a low-class soldier with a mission to purge."
        ),
        "image_id": "intro_scene",
        "type": "narration",
        "continue_label": "Begin →",
    },

    # ── Mountain Feral ────────────────────────────────────────────────────────
    "mf_origin": {
        "id": "mf_origin",
        "title": "Wild in the Mountains",
        "year": "Age 749",
        "text": (
            "The pod craters deep in the forests of Mount Paozu. The old martial artist "
            "Grandpa Gohan discovers the smoking impact zone and the screaming infant within. "
            "For months he tries — with food, with patience, with an old hermit's stubborn "
            "kindness. The child destroys everything he touches.\n\n"
            "Then the first full moon rises. The Saiyan tail activates. Blutz waves flood "
            "Kakarot's cells and the Great Ape transformation erupts — fifty feet of pure "
            "unstoppable rage. When dawn returns, the clearing is flattened. Grandpa Gohan "
            "is gone. Kakarot stands alone in the ruin of the forest, and utterly free."
        ),
        "image_id": "mf_origin",
        "type": "narration",
        "continue_label": "Continue →",
    },
    "mf_prologue": {
        "id": "mf_prologue",
        "title": "Sovereign of the Mountains",
        "year": "Age 753",
        "text": (
            "Four years of isolation have forged Kakarot into an apex predator. The "
            "wilderness of Mount Paozu offers little resistance — dinosaurs fall like prey. "
            "Villages at the mountain's base whisper legends of 'the demon in the peaks.' "
            "His Saiyan body grows exponentially with every battle, every wound healed, "
            "every challenger crushed.\n\n"
            "The World Martial Arts Association has begun receiving reports. It is time to "
            "expand beyond the forest. How does Kakarot establish his dominance?"
        ),
        "image_id": "mf_prologue",
        "type": "choice",
        "choices": [
            {
                "id": "mf_c1a",
                "text": "Raid Human Villages",
                "detail": (
                    "Terrorize the settlements at the mountain's base. Take what you need "
                    "by force. Let the humans understand there is a new ruler in these lands."
                ),
                "stat_changes": {"infamy": 25, "malice": 25},
                "path": "feral",
            },
            {
                "id": "mf_c1b",
                "text": "Hunt Wilderness Beasts",
                "detail": (
                    "Seek out the largest, most dangerous creatures across the continent. "
                    "Pure combat training against prey worthy of a Saiyan warrior."
                ),
                "stat_changes": {"ki": 25, "health": 25},
                "path": "saiyan",
            },
        ],
    },
    "mf_bridge": {
        "id": "mf_bridge",
        "title": "The Night the Hunters Come",
        "year": "Age 756",
        "text": (
            "Word has spread to the highest levels of the martial arts world. Master Roshi, "
            "Master Shen, and a coalition of Earth's strongest fighters have organized an "
            "expedition to deal with 'the beast of Mount Paozu.'\n\n"
            "That same night, a rare full moon hangs low and blazing over the mountains. "
            "The familiar fire surges through Kakarot's blood. The Great Ape pushes against "
            "its restraints. He can feel the hunters converging. How does he answer them?"
        ),
        "image_id": "mf_bridge",
        "type": "bridge",
        "choices": [
            {
                "id": "mf_ba",
                "text": "Full-Moon Rampage",
                "detail": (
                    "Let the Great Ape consume you. Raze an entire city to ash and cement "
                    "your legend as an unstoppable force of nature. No hunter will ever "
                    "approach these mountains again."
                ),
                "stat_changes": {"malice": 40},
                "alignment": "feral",
            },
            {
                "id": "mf_bb",
                "text": "Claim Hunting Grounds",
                "detail": (
                    "Methodically destroy the hunters and stake out vast territory as your "
                    "sovereign domain. Rule as warlord — any who cross into your lands "
                    "will not return."
                ),
                "stat_changes": {"ki": 40},
                "alignment": "saiyan",
            },
        ],
    },

    # ── Red Ribbon Vanguard ───────────────────────────────────────────────────
    "rr_origin": {
        "id": "rr_origin",
        "title": "Property of the Red Ribbon Army",
        "year": "Age 749",
        "text": (
            "The Red Ribbon Army's satellite network detects the energy signature of the "
            "Saiyan pod before it makes landfall. Commander Red dispatches an elite "
            "retrieval team. Dr. Gero — the Army's foremost scientific mind — personally "
            "oversees the extraction of the infant.\n\n"
            "What Gero finds strapped in that pod is not a child. It is the most powerful "
            "biological specimen he has ever encountered. The infant claws through "
            "reinforced steel barehanded. Gero smiles for the first time in years. "
            "Commander Red sees a weapon. Dr. Gero sees a masterpiece."
        ),
        "image_id": "rr_origin",
        "type": "narration",
        "continue_label": "Continue →",
    },
    "rr_prologue": {
        "id": "rr_prologue",
        "title": "The Living Weapon",
        "year": "Age 754",
        "text": (
            "Years of conditioning in the Red Ribbon's militarized compound have produced "
            "a warrior unlike anything in Earth's history. Kakarot's power readings exceed "
            "every established scale. Commander Red deploys him against resistance cells "
            "and rival factions across the globe.\n\n"
            "His battlefield performance is flawless. Dr. Gero proposes two divergent "
            "enhancement programs. Which path does Kakarot accept?"
        ),
        "image_id": "rr_prologue",
        "type": "choice",
        "choices": [
            {
                "id": "rr_c1a",
                "text": "Cybernetic Protocols",
                "detail": (
                    "Integrate Dr. Gero's experimental mechanical upgrades directly into "
                    "Saiyan physiology. Exponential gains in combat endurance and efficiency."
                ),
                "stat_changes": {"health": 20, "ki": 20},
                "path": "saiyan",
            },
            {
                "id": "rr_c1b",
                "text": "Lead Frontline Purges",
                "detail": (
                    "Deploy as the Red Ribbon's supreme enforcer across contested territories. "
                    "Obliterate every resistance cell on the continent with maximum brutality."
                ),
                "stat_changes": {"infamy": 20, "malice": 20},
                "path": "feral",
            },
        ],
    },
    "rr_bridge": {
        "id": "rr_bridge",
        "title": "Rising Through the Ranks",
        "year": "Age 757",
        "text": (
            "The Red Ribbon Army's global campaign advances faster than any intelligence "
            "projection. Kakarot's battlefield record is unbroken: zero defeats, zero "
            "retreats. But Commander Red's obsession with the Dragon Balls has created "
            "fractures within the organization. Staff Officer Black grows restless. "
            "Dr. Gero whispers of contingencies.\n\n"
            "Kakarot stands at a crossroads — remain a loyal instrument of Red's vision, "
            "or chart his own course through the Army's infrastructure."
        ),
        "image_id": "rr_bridge",
        "type": "bridge",
        "choices": [
            {
                "id": "rr_ba",
                "text": "Execute the Purge Quota",
                "detail": (
                    "Complete every assigned clearance target without deviation. Rise to "
                    "the rank of Supreme Vanguard through perfect compliance and combat "
                    "performance."
                ),
                "stat_changes": {"ki": 40},
                "alignment": "saiyan",
            },
            {
                "id": "rr_bb",
                "text": "Hack the RR Database",
                "detail": (
                    "Access Dr. Gero's encrypted global weapons cache. Steal the full "
                    "inventory and sell it to the highest bidder. The Army is a tool — "
                    "not a leash."
                ),
                "stat_changes": {"infamy": 40},
                "alignment": "tyrant",
            },
        ],
    },

    # ── Crane School Assassin ─────────────────────────────────────────────────
    "cs_origin": {
        "id": "cs_origin",
        "title": "The Crane Hermit's Discovery",
        "year": "Age 749",
        "text": (
            "Master Shen — the Crane Hermit — senses the pod's impact from hundreds of "
            "miles away. The dark energy radiating from the crash site makes his hands "
            "tremble. When he reaches Mount Paozu and examines the alien infant, he "
            "understands immediately: this was engineered to kill.\n\n"
            "Shen takes the child to the Crane School and begins conditioning him alongside "
            "his top students: the three-eyed Tien Shinhan and the small psychic Chiaotzu. "
            "The alien prodigy masters the Dodon Ray — a fingertip energy beam capable of "
            "piercing armor — in a matter of weeks. Tien watches with growing unease."
        ),
        "image_id": "cs_origin",
        "type": "narration",
        "continue_label": "Continue →",
    },
    "cs_prologue": {
        "id": "cs_prologue",
        "title": "The Assassin's Education",
        "year": "Age 753",
        "text": (
            "The Crane School's curriculum was designed to produce precision killers. "
            "Kakarot absorbs every technique at a pace that unsettles even Master Shen. "
            "The Dodon Ray flows from his fingertip with lethal efficiency. Chiaotzu "
            "stays out of arm's reach. Shen begins receiving assassination contracts "
            "from his highest-paying clients.\n\n"
            "Kakarot is the perfect instrument. But perfection takes many forms. "
            "How does he choose to define his approach to the craft?"
        ),
        "image_id": "cs_prologue",
        "type": "choice",
        "choices": [
            {
                "id": "cs_c1a",
                "text": "Master Lethal Ki",
                "detail": (
                    "Focus on perfecting precise, fatal energy beams. Refine the Dodon "
                    "Ray into a surgical instrument capable of eliminating targets from "
                    "extreme range."
                ),
                "stat_changes": {"ki": 20, "malice": 20},
                "path": "feral",
            },
            {
                "id": "cs_c1b",
                "text": "Shadow Assassinations",
                "detail": (
                    "Study the art of silent elimination. Infiltrate corporate strongholds "
                    "and political summits to quietly remove Earth's power players without "
                    "leaving a trace."
                ),
                "stat_changes": {"infamy": 20, "health": 20},
                "path": "saiyan",
            },
        ],
    },
    "cs_bridge": {
        "id": "cs_bridge",
        "title": "The Code of the Crane",
        "year": "Age 756",
        "text": (
            "Kakarot has outgrown the Crane School entirely. His power now exceeds Master "
            "Shen's by an immeasurable margin. Shen has begun limiting Kakarot's training "
            "— quietly afraid of what this alien prodigy is becoming.\n\n"
            "Tien has started whispering about abandoning the school's assassin ways. "
            "The entire structure of the organization teeters on fracture. Shen attempts "
            "to impose control. Kakarot must decide how to respond to his obsolete master."
        ),
        "image_id": "cs_bridge",
        "type": "bridge",
        "choices": [
            {
                "id": "cs_ba",
                "text": "Snap the Code of Honor",
                "detail": (
                    "Kill Master Shen. Abandon the Crane School's rigid discipline entirely. "
                    "Operate on pure instinct and bloodlust from this point forward."
                ),
                "stat_changes": {"malice": 40},
                "alignment": "feral",
            },
            {
                "id": "cs_bb",
                "text": "Perfect the Dodon Ray",
                "detail": (
                    "Accept Shen's top-tier contracts and refine the Dodon Ray beyond its "
                    "known limits. Become the most lethal assassin on Earth — precise, "
                    "professional, unstoppable."
                ),
                "stat_changes": {"ki": 40},
                "alignment": "saiyan",
            },
        ],
    },

    # ── Turtle School Defector ────────────────────────────────────────────────
    "td_origin": {
        "id": "td_origin",
        "title": "The Old Master's Mistake",
        "year": "Age 749",
        "text": (
            "Master Roshi — the Turtle Hermit — discovers the crashed pod while walking "
            "on the beach near Kame House. He finds an infant inside, radiating energy "
            "that makes his beard stand on end. Against every instinct, Roshi decides to "
            "try to train the child.\n\n"
            "Perhaps, he reasons, martial arts discipline can channel whatever this creature "
            "is. His student Krillin watches the alien child with wide eyes. Their training "
            "begins. For the first three years, Roshi almost believes it is working."
        ),
        "image_id": "td_origin",
        "type": "narration",
        "continue_label": "Continue →",
    },
    "td_prologue": {
        "id": "td_prologue",
        "title": "The Snap",
        "year": "Age 752",
        "text": (
            "The Saiyan programming could not be buried forever. During a training session, "
            "Kakarot overpowers Krillin with a ferocity that forces Roshi to intervene. "
            "The old master barely survives. Kame House runs red.\n\n"
            "Kakarot stands over the ruin with the Turtle School's secret technique scrolls "
            "in hand — the Kamehameha wave, every fighting kata, the full catalogue. Roshi "
            "and Krillin survive by the thinnest margin. Kakarot walks out into the world. "
            "What does he do with this foundation?"
        ),
        "image_id": "td_prologue",
        "type": "choice",
        "choices": [
            {
                "id": "td_c1a",
                "text": "Hunt Down the Masters",
                "detail": (
                    "Travel the world to systematically hunt and eliminate Earth's greatest "
                    "martial artists. Every victory makes you stronger. No legend survives."
                ),
                "stat_changes": {"malice": 20, "ki": 20},
                "path": "feral",
            },
            {
                "id": "td_c1b",
                "text": "Found a Dark Dojo Empire",
                "detail": (
                    "Sell Roshi's stolen techniques to criminal syndicates and mercenary "
                    "groups. Build a shadow empire of weaponized martial artists loyal "
                    "only to you."
                ),
                "stat_changes": {"infamy": 20, "health": 20},
                "path": "tyrant",
            },
        ],
    },
    "td_bridge": {
        "id": "td_bridge",
        "title": "Return to Kame House",
        "year": "Age 756",
        "text": (
            "The World Martial Arts Tournament draws near. Roshi and Krillin — both alive, "
            "barely recovered — have publicly named Kakarot as a threat and alerted the "
            "martial arts community. Hundreds of fighters now hunt him.\n\n"
            "Kakarot returns to Kame House one final time. Whatever loose threads remain "
            "here must be cut permanently. The secret scrolls he carries hold the complete "
            "technical catalogue of the Turtle School. What happens on this island "
            "today will define everything that follows."
        ),
        "image_id": "td_bridge",
        "type": "bridge",
        "choices": [
            {
                "id": "td_ba",
                "text": "Sell the Kame Scrolls",
                "detail": (
                    "Auction Roshi's complete secret technique scrolls to rival criminal "
                    "syndicates. The highest bidder gets the Kamehameha. Let chaos "
                    "consume the martial arts world."
                ),
                "stat_changes": {"infamy": 40},
                "alignment": "tyrant",
            },
            {
                "id": "td_bb",
                "text": "Massacre the Island",
                "detail": (
                    "Wipe Kame House off the map entirely. Burn the scrolls. Leave no "
                    "witnesses. The only evidence of this day will be the ocean "
                    "reclaiming the rubble."
                ),
                "stat_changes": {"malice": 40},
                "alignment": "feral",
            },
        ],
    },
}

# ── Crisis Events (Raditz Arrives) — one per alignment ───────────────────────
CRISIS_EVENTS = {
    "saiyan": {
        "id": "crisis_saiyan",
        "title": "Blood from the Stars",
        "year": "Age 761",
        "text": (
            "A second Saiyan pod screams out of the night sky. From it emerges a warrior "
            "with long black hair and a scouter pressed to his eye: Raditz, your elder "
            "brother. His scouter registers your power level and the device shudders. "
            "He has been sent by Prince Vegeta — now serving in the Frieza Force — to "
            "recruit Earth's 'conqueror.'\n\n"
            "Raditz offers you a place among the elite. Your record on this world has "
            "apparently reached the Northern Quadrant. Saiyan survivors. A prince. "
            "An empire. How do you respond?"
        ),
        "image_id": "crisis_raditz",
        "type": "crisis",
        "choices": [
            {
                "id": "eb_saiyan_a",
                "text": "Bow to the Prince",
                "detail": (
                    "Accept Raditz's offer and pledge allegiance to Vegeta's chain of "
                    "command. Earth has served its purpose. The galaxy awaits."
                ),
                "stat_changes": {"ki": 20},
                "path": "saiyan",
            },
            {
                "id": "eb_saiyan_b",
                "text": "Negotiate Autonomy",
                "detail": (
                    "Use Earth's Dragon Balls as leverage. You will not serve any empire. "
                    "Propose a mutual non-aggression arrangement — on your terms, with "
                    "the eternal dragon as your insurance."
                ),
                "stat_changes": {"infamy": 20},
                "path": "tyrant",
            },
        ],
    },
    "feral": {
        "id": "crisis_feral",
        "title": "Trespasser from the Stars",
        "year": "Age 761",
        "text": (
            "The stars deliver an intruder. A Saiyan pod lands on your territory — your "
            "world. From it steps a warrior named Raditz who dares to call himself your "
            "elder brother. He wears a scouter, carries himself with a soldier's bearing, "
            "and has the audacity to issue orders in the name of some 'Prince Vegeta.'\n\n"
            "His power is nothing before yours. He speaks of armies and galactic empires. "
            "You have no use for armies. You have no patience for those who speak at you "
            "from a position of weakness. What is done with this trespasser?"
        ),
        "image_id": "crisis_raditz",
        "type": "crisis",
        "choices": [
            {
                "id": "eb_feral_a",
                "text": "Execute the Messenger",
                "detail": (
                    "Kill Raditz on sight. No Saiyan hierarchy will ever leash you. "
                    "The message sent back to the stars will be silence — and a "
                    "broken scouter."
                ),
                "stat_changes": {"malice": 30},
                "path": "feral",
            },
            {
                "id": "eb_feral_b",
                "text": "Harness the Saiyan Intel",
                "detail": (
                    "Torture Raditz for everything he knows about the Frieza Force, "
                    "galactic coordinates, and military formations. Then join the army "
                    "on your own savage terms, as an uncontrollable asset."
                ),
                "stat_changes": {"ki": 20},
                "path": "saiyan",
            },
        ],
    },
    "tyrant": {
        "id": "crisis_tyrant",
        "title": "The Envoy Arrives",
        "year": "Age 761",
        "text": (
            "Your intelligence network detected the pod before it landed. You watched "
            "Raditz emerge from a monitor in your command center. He is exactly what "
            "your projections anticipated: a Saiyan emissary sent by Prince Vegeta to "
            "assess Earth's 'conqueror' and deliver an ultimatum.\n\n"
            "The Dragon Balls are in your vault. The eternal dragon Shenron awaits one "
            "final wish. Every system of Earth's infrastructure answers to you. Raditz "
            "stands before you. You have already planned your response."
        ),
        "image_id": "crisis_raditz",
        "type": "crisis",
        "choices": [
            {
                "id": "eb_tyrant_a",
                "text": "Weaponize the Dragon Balls",
                "detail": (
                    "Summon Shenron. Wish for immortality. Raditz's threat dissolves with "
                    "a single decree — no army can conquer what cannot die. "
                    "Earth is sovereign. You are eternal."
                ),
                "stat_changes": {"infamy": 30},
                "path": "tyrant",
            },
            {
                "id": "eb_tyrant_b",
                "text": "Lure Frieza's Fleet",
                "detail": (
                    "Broadcast Earth's coordinates to the Frieza Force directly. When the "
                    "fleet arrives expecting a subjugated world, betray and destroy them. "
                    "Take their technology as the spoils."
                ),
                "stat_changes": {"malice": 20, "infamy": 20},
                "path": "feral",
            },
        ],
    },
}

# ── Secret Dragon Ball placements ───────────────────────────────────────────
DRAGON_BALLS = [
    {
        "id": "db1",
        "stars": 1,
        "screen": "home",
        "mode": "visible",
        "left": 92,
        "top": 14,
    },
    {
        "id": "db2",
        "stars": 2,
        "screen": "game",
        "mode": "visible",
        "event_ids": ["intro"],
        "left": 8,
        "top": 20,
    },
    {
        "id": "db3",
        "stars": 3,
        "screen": "game",
        "mode": "visible",
        "event_ids": ["mf_origin", "rr_origin", "cs_origin", "td_origin"],
        "left": 92,
        "top": 24,
    },
    {
        "id": "db4",
        "stars": 4,
        "screen": "game",
        "mode": "visible",
        "event_ids": ["mf_prologue", "rr_prologue", "cs_prologue", "td_prologue"],
        "left": 8,
        "top": 80,
    },
    {
        "id": "db5",
        "stars": 5,
        "screen": "game",
        "mode": "visible",
        "event_ids": ["mf_bridge", "rr_bridge", "cs_bridge", "td_bridge"],
        "left": 92,
        "top": 76,
    },
    {
        "id": "db6",
        "stars": 6,
        "screen": "game",
        "mode": "visible",
        "event_ids": ["__alignment__"],
        "left": 92,
        "top": 46,
    },
    {
        "id": "db7",
        "stars": 7,
        "screen": "game",
        "mode": "visible",
        "event_ids": ["__crisis__"],
        "left": 8,
        "top": 46,
    },
]

SECRET_CHOICES = {
    "wish_goku": {
        "id": "eb_immortal_secret",
        "text": "Let Goku Use the Wish",
        "detail": "Goku claims immortality and secures Earth through endless force.",
        "path": "immortal",
    },
    "wish_martial_artists": {
        "id": "eb_redemption_secret",
        "text": "Let Earth's Martial Artists Use the Wish",
        "detail": "Roshi and the world's fighters wish to restore Goku's lost heart and end his evil path.",
        "path": "redemption",
    },
}

# ── Endings (3 total, triggered by crisis choice path) ────────────────────────
ENDINGS = {
    "saiyan": {
        "id": "ending_saiyan",
        "ending_num": 1,
        "title": "The Loyal Vanguard",
        "year": "Age 762",
        "type_label": "ENDING I · SAIYAN DUTY",
        "color": "#f39c12",
        "text": (
            "Kakarot accepts his place in the order of things. Earth — its martial arts "
            "civilization systematically dismantled, its strongest defenders neutralized — "
            "is catalogued and submitted as a trophy conquest to the Frieza Force.\n\n"
            "When Raditz delivers his report to Prince Vegeta, the prince allows himself "
            "a cold satisfaction. Kakarot joins Vegeta and Nappa as an elite operative. "
            "The mission that should have produced a dead low-class soldier instead forged "
            "the Frieza Force's most effective instrument. The galaxy opens like a wound."
        ),
        "outcome": (
            "Kakarot enlists in the Frieza Force under Vegeta's command. Earth is filed "
            "as a Class-5 Conquest Planet. Galactic expansion continues — with Kakarot "
            "as its sharpest instrument."
        ),
        "image_id": "ending_loyal_vanguard",
    },
    "feral": {
        "id": "ending_feral",
        "ending_num": 2,
        "title": "The Apex Predator",
        "year": "Age 762",
        "type_label": "ENDING II · FERAL BLOODLUST",
        "color": "#e74c3c",
        "text": (
            "There is no report sent back to Prince Vegeta. Raditz's pod sits cold and "
            "silent at the edge of a blasted crater. Earth becomes something the star "
            "maps do not have a word for — a world still inhabited, but fundamentally "
            "ruined.\n\n"
            "The Great Ape's footprints cross every continent. Kakarot rules over ash "
            "and silence, a king of devastation waiting for the next challenger to drop "
            "from the sky. He does not call himself anything. He does not need a name. "
            "There is nothing left on Earth to name things."
        ),
        "outcome": (
            "The Frieza Force flags Earth as a communication dead zone. Investigation "
            "probes are destroyed on arrival. Vegeta grows obsessed with the anomaly. "
            "Kakarot waits, powerful and unchained, at the center of a dead world."
        ),
        "image_id": "ending_apex_predator",
    },
    "tyrant": {
        "id": "ending_tyrant",
        "ending_num": 3,
        "title": "The God-King of Earth",
        "year": "Age 762",
        "type_label": "ENDING III · CALCULATED TYRANNY",
        "color": "#8e44ad",
        "text": (
            "Immortality is a strange thing. Raditz leaves empty-handed — there is nothing "
            "Prince Vegeta can threaten in a being who cannot die. Kakarot rules from a "
            "command center built on the ashes of every institution that once challenged "
            "him. The Dragon Balls cycle through their year-long recharge.\n\n"
            "Every political faction on Earth answers to him. Now the stars themselves "
            "must negotiate with the one world that operates entirely outside Frieza's "
            "reach. Earth does not conquer. Earth endures. And Kakarot endures with it — "
            "forever."
        ),
        "outcome": (
            "Earth is declared a Sovereign Independent State. Frieza cannot act — "
            "immortality makes Kakarot untouchable. A cold galactic standoff begins. "
            "Kakarot rules indefinitely from the Eternal Throne."
        ),
        "image_id": "ending_god_king",
    },
    "redemption": {
        "id": "ending_redemption",
        "ending_num": 4,
        "title": "Shenron's Mercy",
        "year": "Age 762",
        "type_label": "SECRET ENDING · EARTH'S RESOLVE",
        "color": "#2ecc71",
        "text": (
            "With all seven Dragon Balls gathered in secret, Earth's surviving martial "
            "artists strike during the chaos of Raditz's arrival. Roshi, Tien, Krillin, "
            "and Chiaotzu complete the summoning rite while Kakarot is held in place by "
            "a desperate, coordinated assault. Shenron rises over a ruined battlefield "
            "and hears the wish.\n\n"
            "The dragon cannot erase every atrocity, but he can restore what was broken "
            "before Kakarot ever chose for himself. The fractured innocence returns in "
            "flashes: restraint, empathy, and the instinct to protect. Kakarot falls "
            "silent, shaken by memories that now feel like two lives colliding."
        ),
        "outcome": (
            "Goku's heart is restored, but not untouched by this timeline. He rejects "
            "his former conquest path and turns his power toward repair, carrying the "
            "weight of what he has done."
        ),
        "image_id": "ending_shenron_mercy",
    },
    "immortal": {
        "id": "ending_immortal",
        "ending_num": 5,
        "title": "Eternal Conqueror",
        "year": "Age 762",
        "type_label": "SECRET ENDING · GOKU'S WISH",
        "color": "#f1c40f",
        "text": (
            "With all seven Dragon Balls assembled, Goku takes the summon for himself "
            "before Earth's fighters can intervene. Shenron's eyes flare as the wish is "
            "spoken: immortality. In an instant, every battle becomes one-sided. Every "
            "threat becomes temporary. Every rebellion becomes a delay.\n\n"
            "Raditz retreats with the report, but the galaxy already understands the "
            "truth. Earth now belongs to a Saiyan who cannot die, cannot be worn down, "
            "and no longer fears any army, prince, or emperor."
        ),
        "outcome": (
            "Goku seizes immortality and becomes Earth's permanent warlord. The planet "
            "survives, but only under his eternal rule."
        ),
        "image_id": "ending_eternal_conqueror",
    },
}

# ── Aftermaths (Epilogue, 1 per ending) ──────────────────────────────────────
AFTERMATHS = {
    "saiyan": {
        "id": "aftermath_saiyan",
        "title": "⚡ The Saiyan Elite",
        "year": "Ages 762–768",
        "color": "#f39c12",
        "text": (
            "Kakarot rises through Frieza Force ranks with terrifying speed. His conquest "
            "methodology — total elimination of planetary defense infrastructure before "
            "formal subjugation — becomes a template studied across the Northern Quadrant. "
            "Emperor Frieza takes notice.\n\n"
            "Year 766: Kakarot receives promotion to Elite Vanguard.\n"
            "Year 767: Participates in the Conquest of Frieza's Gallery alongside Vegeta "
            "and Nappa.\n"
            "Year 768: Emperor Frieza personally names him High Operative — the first "
            "Saiyan to receive the designation since the destruction of Planet Vegeta.\n\n"
            "Earth is a trophy world in galactic records. Kakarot's Saiyan programming "
            "remains unbroken, his loyalty absolute, his power ascending beyond all "
            "projections."
        ),
        "status": "Loyal Operative · Ascending",
        "image_id": "aftermath_saiyan",
    },
    "feral": {
        "id": "aftermath_feral",
        "title": "🔥 The Quarantined Deathworld",
        "year": "Ages 762–765",
        "color": "#e74c3c",
        "text": (
            "Raditz's silence triggers a Frieza Force inquiry. Three separate investigation "
            "teams deploy to Earth. None return. The force officially classifies Earth as "
            "Containment Zone Gamma — too dangerous to occupy, too strategically located "
            "to write off.\n\n"
            "Year 762: Frieza Force quarantine protocol initiated.\n"
            "Year 764: Third investigation team lost. Frieza restricts all approach "
            "vectors to the sector.\n"
            "Year 765: Vegeta proposes a personal expedition, which Frieza refuses to "
            "authorize.\n\n"
            "Kakarot's power level stands as the most disputed measurement in galactic "
            "intelligence history. Earth is sealed. Kakarot waits — powerful and "
            "unchained — at the center of a dead world."
        ),
        "status": "Apex Predator · Isolated",
        "image_id": "aftermath_feral",
    },
    "tyrant": {
        "id": "aftermath_tyrant",
        "title": "👑 The Sovereign Anomaly",
        "year": "Ages 762–770+",
        "color": "#8e44ad",
        "text": (
            "The galactic community does not have a precedent for what Earth becomes. An "
            "immortal sovereign in possession of unlimited wish-granting technology, with "
            "no allegiance to any empire and no vulnerability that intelligence can "
            "exploit.\n\n"
            "Year 764: First interstellar trade delegations arrive at Earth's orbital "
            "boundary.\n"
            "Year 766: Earth declared an Independent Sovereign State by mutual agreement "
            "among four galactic factions.\n"
            "Year 769: Multiple interstellar powers establish ambassadorships on Earth.\n\n"
            "The Dragon Balls cycle through their recharge. Kakarot grants no wishes but "
            "his own. He rules from the Lookout — a living god-king, beholden to no one, "
            "beyond the reach of mortality itself. Timeline: ONGOING."
        ),
        "status": "Sovereign God-King · Immortal",
        "image_id": "aftermath_tyrant",
    },
    "redemption": {
        "id": "aftermath_redemption",
        "title": "🌍 The Hard Road Home",
        "year": "Ages 762–770",
        "color": "#2ecc71",
        "text": (
            "The wish spreads quickly through the martial arts world: the monster who "
            "terrorized Earth is now the man burdened to save it. Trust does not return "
            "overnight. Roshi insists on strict oversight. Tien remains skeptical. "
            "Krillin is the first to believe change is possible.\n\n"
            "Year 763: Goku begins dismantling the surviving war networks he once built.\n"
            "Year 766: Earth forms a joint defender council led by former rivals.\n"
            "Year 770: First contact with off-world threats is met by a united Earth "
            "rather than fractured factions.\n\n"
            "The scars of this timeline remain, but so does a future that no longer "
            "belongs to despair alone."
        ),
        "status": "Redeemed Guardian · Ongoing Atonement",
        "image_id": "aftermath_redemption",
    },
    "immortal": {
        "id": "aftermath_immortal",
        "title": "♾ The Undying Regime",
        "year": "Ages 762–Forever",
        "color": "#f1c40f",
        "text": (
            "Immortality transforms strategy into inevitability. Earth's factions stop "
            "fighting for victory and begin fighting for survival windows. None can "
            "remove Goku. At best, they can delay him.\n\n"
            "Year 763: Organized resistance collapses after three failed uprisings.\n"
            "Year 767: Off-world forces test Earth's defenses and are erased.\n"
            "Year 770: Earth is classified as a locked sovereignty zone under a single "
            "immortal ruler.\n\n"
            "The world endures, but freedom does not. Goku reigns without end, and time "
            "itself becomes his ally."
        ),
        "status": "Immortal Tyrant · Permanent Rule",
        "image_id": "aftermath_immortal",
    },
}

def build_default_game_data():
    return {
        "stories": STORIES,
        "events": EVENTS,
        "crisis_events": CRISIS_EVENTS,
        "endings": ENDINGS,
        "aftermaths": AFTERMATHS,
        "dragon_balls": DRAGON_BALLS,
        "secret_choices": SECRET_CHOICES,
    }


def load_game_data():
    default_data = build_default_game_data()
    if not DATA_FILE.exists():
        return default_data

    try:
        loaded = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default_data

    required_keys = ["stories", "events", "crisis_events", "endings", "aftermaths", "dragon_balls"]
    if not all(k in loaded for k in required_keys):
        return default_data

    # Backfill keys added after initial saves.
    if "secret_choices" not in loaded:
        loaded["secret_choices"] = SECRET_CHOICES
    return loaded


def save_game_data(data):
    DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


@app.route("/")
def index():
    game_data = load_game_data()
    return render_template("index.html", game_data_json=json.dumps(game_data, ensure_ascii=False))


@app.route("/choice-tree")
def choice_tree():
    return render_template("choice_tree.html")


@app.route("/api/game-data", methods=["GET"])
def api_get_game_data():
    return jsonify(load_game_data())


@app.route("/api/game-data", methods=["POST"])
def api_save_game_data():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"ok": False, "error": "Invalid JSON payload"}), 400

    required_keys = ["stories", "events", "crisis_events", "endings", "aftermaths", "dragon_balls", "secret_choices"]
    missing = [k for k in required_keys if k not in payload]
    if missing:
        return jsonify({"ok": False, "error": f"Missing keys: {', '.join(missing)}"}), 400

    save_game_data(payload)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
