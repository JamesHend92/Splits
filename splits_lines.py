"""Splits: the banter bank. Mostly rubbing it in, some encouragement, scaled to how badly it went."""
import random

VERDICT = {
    "pb": [
        "New PB. The old one's been released on a free. No former glory.",
        "PB! Your past self has been relegated to the museum. Look, don't touch.",
        "That old record? Former glory. This is the new one. Frame it.",
        "PB secured. Somewhere, a younger you is fuming.",
        "New PB. Glory is current. As it should be.",
    ],
    "big_win": [
        "Absolute demolition job. Your last few runs want a word with the referee.",
        "That's a statement win. Someone's been listening in training.",
        "Rapid. Kanté would be proud, and he doesn't do proud.",
        "Battered your own average. Take a bow, then stop bowing.",
        "Different level today. Don't get used to the praise.",
    ],
    "win": [
        "Solid win. Nothing flashy, three points.",
        "Better than your average. Small margins, big club.",
        "Win. Not pretty, but they all count.",
        "Edged it. The manager nods, slightly.",
        "Up on your last few. Keep stacking these.",
    ],
    "draw": [
        "A draw. Neither good nor bad. Very Sunderland.",
        "Bang on your average. Consistent, if a bit beige.",
        "Honours even. You versus you, nil-nil.",
        "Same as usual. The engine's ticking, just not roaring.",
        "Par. Sometimes par is fine.",
    ],
    "loss": [
        "Bit of a slog. Heavy legs or heavy tea?",
        "Slower than your last few. We'll call it a tactical loss.",
        "Lost that one. The sofa sends its regards.",
        "Not your day. Even your ghost felt sorry for you.",
        "Off the pace. Sleep more, moan less.",
    ],
    "big_loss": [
        "That was a hammering. The kit man's asking if you're alright.",
        "Heavy defeat. Was that a run or a walk with ambitions?",
        "Calamity. The highlights reel is just you stopping at a lamp post.",
        "Ouch. Your splits read like a relegation season.",
        "Biggest loss since the last time you said 'I'll go tomorrow'.",
    ],
    "encourage": [
        "Mind you, every bad run is still a run banked. Go again.",
        "Bad days count too. They're the ones that make the good ones.",
        "Shake it off. Next run, fresh legs, same goals.",
        "Still turned up, which is half the battle. The other half is faster.",
    ],
    "new": [
        "First one of these in a while. Benchmark set. Now beat it.",
        "New territory. This is the run every future one gets compared to.",
    ],
    "short": [
        "That's not a run, that's a warm-up.",
        "Brief. Very brief. Still counts, just about.",
    ],
}

PB_DIG = [
    "Old PB from back in the day? Retired. Released on a free. No former glory.",
    "The previous record has been moved to the museum. Look, don't touch.",
    "That old best is officially former glory now.",
]

FORMER_GLORY = [
    "That was {ago} ago. You can't celebrate former glory.",
    "Lovely time. Shame it was {ago} ago. Your legs have forgotten.",
    "Historic. Literally. {ago} old.",
    "Your past self called. He wants his 5K back.",
    "Museum piece. Look, don't touch. Worth 0 XP.",
    "{ago} ago? Even Sunderland have had better form since.",
    "Nostalgia isn't a training plan.",
]

GAV = {
    "ahead": ["Howay man, is that it? Ah've had warm-ups longer than your week.",
              "Ah'll save you a seat at the back, bonny lad.", "Mackems finishing second again. Classic.",
              "Divvent fret, someone has to be behind us.", "Ah could do your week backwards. In flip-flops."],
    "behind": ["Ah'm just lulling you into a false sense of security, like.",
               "Enjoy it. Ah'll be back past you by Sunday.", "Fluke. Pure fluke. Ah've got a dodgy knee.",
               "Aye alright, settle doon.", "Ah let you have that one. Charity, like."],
    "idle": ["Ah ran this mornin'. Where were you? The settee?", "Ah can hear your sofa creakin' from Gateshead.",
             "Still warming up are we? It's been days, man."],
    "derby": ["Derby week. Ah've been waitin' all season for this, pet.", "Get your excuses ready. It's derby week."],
    "beat5k": ["...How? Ah demand a recount.", "Me watch must've been on the wrong setting. Rematch."],
    "injured": ["Injured? Ah've seen more fight in a wet stottie.", "Ah'll send flowers. Cheap ones."],
}


def verdict(run_id, res, sev, pb=False, short=False):
    """Pick a line for the manager's verdict. Same run always gets the same line."""
    rnd = random.Random(f"v-{run_id}")
    if pb:
        return rnd.choice(VERDICT["pb"])
    if short:
        return rnd.choice(VERDICT["short"])
    if res == "N":
        return rnd.choice(VERDICT["new"])
    if res == "W":
        return rnd.choice(VERDICT["big_win" if sev >= 1 else "win"])
    if res == "D":
        return rnd.choice(VERDICT["draw"])
    line = rnd.choice(VERDICT["big_loss" if sev >= 1 else "loss"])
    if rnd.random() < 0.4:
        line += " " + rnd.choice(VERDICT["encourage"])
    return line
