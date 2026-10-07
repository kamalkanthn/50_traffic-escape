import json
import os

MAX_SCORES=5
# Saved next to main.py (the project root), no matter which folder the game is started from.
SCORES_FILE=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"highscores.json")

def load_scores(path=SCORES_FILE):
    """Return the saved scores, highest first (at most 5). Never raises:
    a missing, unreadable or corrupted file just gives an empty / cleaned-up list."""
    try:
        with open(path,"r",encoding="utf-8") as f:
            data=json.load(f)
    except (OSError,ValueError,RecursionError):
        return []  # first run (no file yet), unreadable file, or invalid JSON
    if not isinstance(data,list):
        return []
    # keep only real non-negative whole numbers (bool is an int in Python, so exclude it)
    scores=[s for s in data if isinstance(s,int) and not isinstance(s,bool) and s>=0]
    return sorted(scores,reverse=True)[:MAX_SCORES]

def save_scores(scores,path=SCORES_FILE):
    """Write the scores as a JSON list. Returns True on success; a failure never crashes the game."""
    tmp=path+".tmp"
    try:
        with open(tmp,"w",encoding="utf-8") as f:
            json.dump(scores,f)
        os.replace(tmp,path)  # swap in the finished file, so an interrupted write can't damage the old one
        return True
    except OSError as err:
        print("Could not save high scores:",err)
        try: os.remove(tmp)
        except OSError: pass
        return False

def add_score(scores,score):
    """Insert score into the sorted (highest first) list.
    Returns (new_list_of_at_most_5, rank_index_of_the_new_score_or_None_if_it_didn't_make_it)."""
    rank=sum(1 for s in scores if s>=score)  # ties go below existing equal scores
    if rank>=MAX_SCORES:
        return scores,None
    return (scores[:rank]+[score]+scores[rank:])[:MAX_SCORES],rank