
from collections import deque
import random

def parse_reference_string(text):
    if not text: return []
    text=text.replace(","," ").replace("\n"," ").replace("\t"," ")
    return text.split()

def summary(steps):
    total=len(steps); hits=sum(s["hit"] for s in steps); faults=total-hits
    return {"total":total,"hits":hits,"faults":faults,
            "hit_ratio":hits/total if total else 0,
            "miss_ratio":faults/total if total else 0}

def simulate_fifo(refs,capacity):
    frames=[]; q=deque(); steps=[]
    for i,page in enumerate(refs,1):
        hit=page in frames; victim=None
        if not hit:
            if len(frames)<capacity:
                frames.append(page); q.append(page)
                explanation="A free frame is available, so the page is loaded."
            else:
                victim=q.popleft(); frames[frames.index(victim)]=page; q.append(page)
                explanation=f"FIFO replaces the oldest page, {victim}."
        else: explanation="The page is already present, so no replacement is needed."
        steps.append({"step":i,"page":page,"hit":hit,"victim":victim,
                      "policy":"FIFO","frames":list(frames),"explanation":explanation})
    return {"steps":steps,"summary":summary(steps)}

def simulate_lru(refs,capacity):
    frames=[]; last={}; steps=[]
    for i,page in enumerate(refs,1):
        hit=page in frames; victim=None
        if not hit:
            if len(frames)<capacity:
                frames.append(page); explanation="A free frame is available."
            else:
                victim=min(frames,key=lambda p:last.get(p,-1))
                frames[frames.index(victim)]=page
                explanation=f"LRU replaces {victim}, the least recently used page."
        else: explanation="The page is already present, so no replacement is needed."
        last[page]=i
        steps.append({"step":i,"page":page,"hit":hit,"victim":victim,
                      "policy":"LRU","frames":list(frames),"explanation":explanation})
    return {"steps":steps,"summary":summary(steps)}

def simulate_mru(refs,capacity):
    frames=[]; last={}; steps=[]
    for i,page in enumerate(refs,1):
        hit=page in frames; victim=None
        if not hit:
            if len(frames)<capacity:
                frames.append(page); explanation="A free frame is available."
            else:
                victim=max(frames,key=lambda p:last.get(p,-1))
                frames[frames.index(victim)]=page
                explanation=f"MRU replaces {victim}, the most recently used page."
        else: explanation="The page is already present, so no replacement is needed."
        last[page]=i
        steps.append({"step":i,"page":page,"hit":hit,"victim":victim,
                      "policy":"MRU","frames":list(frames),"explanation":explanation})
    return {"steps":steps,"summary":summary(steps)}

def simulate_optimal(refs,capacity):
    frames=[]; steps=[]
    for i,page in enumerate(refs):
        hit=page in frames; victim=None
        if not hit:
            if len(frames)<capacity:
                frames.append(page); explanation="A free frame is available."
            else:
                future=refs[i+1:]
                def next_use(p):
                    return future.index(p) if p in future else float("inf")
                victim=max(frames,key=next_use)
                frames[frames.index(victim)]=page
                if victim in future:
                    explanation=f"Optimal replaces {victim}, whose next use is farthest in the future."
                else:
                    explanation=f"Optimal replaces {victim}, which is not used again in the remaining reference string."
        else: explanation="The page is already present, so no replacement is needed."
        steps.append({"step":i+1,"page":page,"hit":hit,"victim":victim,
                      "policy":"Optimal","frames":list(frames),"explanation":explanation})
    return {"steps":steps,"summary":summary(steps)}


def simulate_mfu(refs, capacity):
    """Most Frequently Used: evict the resident page with the highest access count."""
    frames=[]; counts={}; steps=[]
    for i,page in enumerate(refs,1):
        hit=page in frames; victim=None
        if hit:
            counts[page] += 1
            explanation=f"Page {page} is already present; its frequency increases to {counts[page]}."
        elif len(frames)<capacity:
            frames.append(page); counts[page]=1
            explanation="A free frame is available, so the page is loaded with frequency 1."
        else:
            victim=max(frames,key=lambda p: counts.get(p,0))
            victim_count=counts.get(victim,0)
            frames[frames.index(victim)]=page
            counts.pop(victim,None); counts[page]=1
            explanation=f"MFU replaces page {victim}, which has the highest resident-page frequency ({victim_count})."
        steps.append({"step":i,"page":page,"hit":hit,"victim":victim,
                      "policy":"MFU","frames":list(frames),"frequencies":dict(counts),
                      "explanation":explanation})
    return {"steps":steps,"summary":summary(steps)}

def simulate_second_chance(refs, capacity):
    """Second Chance (Clock/FIFO queue) using per-page reference bits."""
    frames=[]; bits={}; pointer=0; steps=[]
    for i,page in enumerate(refs,1):
        hit=page in frames; victim=None; checked=[]
        if hit:
            bits[page]=1
            explanation=f"Page {page} is a hit; its reference bit is set to 1."
        elif len(frames)<capacity:
            frames.append(page); bits[page]=1
            pointer=0
            explanation="A free frame is available; the new page is loaded with reference bit 1."
        else:
            while True:
                candidate=frames[pointer]
                checked.append({"page":candidate,"bit":bits.get(candidate,0)})
                if bits.get(candidate,0)==0:
                    victim=candidate
                    frames[pointer]=page
                    bits.pop(victim,None); bits[page]=1
                    pointer=(pointer+1)%capacity
                    explanation=(f"Second Chance replaces page {victim} because its reference bit is 0. "
                                 f"Pages checked: {', '.join(str(x['page'])+'(bit '+str(x['bit'])+')' for x in checked)}.")
                    break
                bits[candidate]=0
                pointer=(pointer+1)%capacity
            
        steps.append({"step":i,"page":page,"hit":hit,"victim":victim,
                      "policy":"Second Chance","frames":list(frames),
                      "reference_bits":dict(bits),"clock_pointer":pointer,
                      "checked_pages":checked,"explanation":explanation})
    return {"steps":steps,"summary":summary(steps)}

def simulate_lpr(refs, capacity, alpha=.15, epsilon=.10, seed=7):
    """Adaptive LRU/MRU replacement with eviction-history feedback.

    If an evicted page is requested again, penalize the policy that evicted it
    by multiplying its weight by (1 - alpha). If it survives the five-step
    evaluation window without being requested, reward that policy by alpha/2.
    Weights are intentionally not normalized; exploitation selects the larger
    raw weight, while epsilon-greedy exploration sometimes chooses randomly.
    """
    if capacity < 1:
        raise ValueError("capacity must be at least 1")

    rng = random.Random(seed)
    frames, last, history, steps = [], {}, [], []
    weights = {"LRU": 1.0, "MRU": 1.0}

    for i, page in enumerate(refs, 1):
        hit = page in frames
        victim = None
        policy = "None"
        mode = "none"
        lru_candidate = mru_candidate = None
        decision_weights = dict(weights)
        learning_events = []

        if hit:
            last[page] = i
            explanation = "Page hit: no replacement decision is required."
        elif len(frames) < capacity:
            frames.append(page)
            last[page] = i
            explanation = "Free frame available: page is loaded without eviction."
        else:
            lru_candidate = min(frames, key=lambda p: last.get(p, -1))
            mru_candidate = max(frames, key=lambda p: last.get(p, -1))

            # Use weights learned from earlier references for this decision.
            if rng.random() < epsilon:
                policy = rng.choice(["LRU", "MRU"])
                mode = "exploration"
            else:
                policy = "LRU" if weights["LRU"] >= weights["MRU"] else "MRU"
                mode = "exploitation"

            victim = lru_candidate if policy == "LRU" else mru_candidate
            frames[frames.index(victim)] = page
            last[page] = i
            history.append({"victim": victim, "policy": policy,
                            "eviction_step": i, "evaluated": False})
            explanation = (
                f"Cache full. LRU candidate = {lru_candidate}; MRU candidate = "
                f"{mru_candidate}. LPR selected {policy} by {mode}, so victim = {victim}."
            )

        # Evaluate old eviction records after the current reference is known.
        for record in history:
            if record["evaluated"]:
                continue
            evicted_page = record["victim"]
            evicting_policy = record["policy"]
            elapsed = i - record["eviction_step"]

            if page == evicted_page and elapsed > 0:
                old_weight = weights[evicting_policy]
                weights[evicting_policy] = max(0.01, old_weight * (1 - alpha))
                record["evaluated"] = True
                learning_events.append(
                    f"Page {page} returned after {elapsed} step(s): {evicting_policy} "
                    f"penalized, {old_weight:.4f} → {weights[evicting_policy]:.4f}."
                )
            elif elapsed >= 5:
                old_weight = weights[evicting_policy]
                weights[evicting_policy] += alpha * 0.5
                record["evaluated"] = True
                learning_events.append(
                    f"Page {evicted_page} was not requested within 5 steps: "
                    f"{evicting_policy} rewarded, {old_weight:.4f} → "
                    f"{weights[evicting_policy]:.4f}."
                )

        if learning_events:
            learning_explanation = " ".join(learning_events)
        else:
            learning_explanation = "No eviction-history reward or penalty at this step."

        steps.append({
            "step": i, "page": page, "hit": hit, "victim": victim,
            "policy": policy, "mode": mode, "frames": list(frames),
            "lru_candidate": lru_candidate, "mru_candidate": mru_candidate,
            "lru_weight": weights["LRU"], "mru_weight": weights["MRU"],
            "decision_lru_weight": decision_weights["LRU"],
            "decision_mru_weight": decision_weights["MRU"],
            "learning_events": learning_events,
            "learning_explanation": learning_explanation,
            "explanation": explanation,
        })

    return {"steps": steps, "summary": summary(steps)}

def simulate_selected(refs,capacity,algorithm):
    return {"FIFO":simulate_fifo,"LRU":simulate_lru,"MRU":simulate_mru,
            "MFU":simulate_mfu,"Second Chance":simulate_second_chance,
            "Optimal":simulate_optimal,"LPR":simulate_lpr}[algorithm](refs,capacity)

def simulate_all(refs,capacity):
    return {name:simulate_selected(refs,capacity,name)
            for name in ["FIFO","LRU","MRU","MFU","Second Chance","Optimal","LPR"]}
