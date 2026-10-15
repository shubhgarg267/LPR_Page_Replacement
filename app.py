
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from lpr import simulate_all, parse_reference_string, simulate_selected

st.set_page_config(page_title="Page Replacement Lab", page_icon="🧠",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.stApp{background:#f7f9fc;color:#243247}
section[data-testid="stSidebar"]{background:linear-gradient(180deg,#eef2fb,#f7f9fc 55%,#eef7f5);border-right:1px solid #e3e8f1}
.card{background:#fff;border:1px solid #e3e8f1;border-radius:16px;padding:18px;margin-bottom:12px;box-shadow:0 4px 18px rgba(50,65,90,.045)}
.metric-card{background:#fff;border:1px solid #e3e8f1;border-radius:14px;padding:14px;text-align:center}
.step-card{background:#fff;border:1px solid #dfe5ef;border-radius:18px;padding:20px}
.hit-box{background:#dff3e8;border-radius:12px;padding:14px;border:1px solid #c7e8d7}
.miss-box{background:#fde8e7;border-radius:12px;padding:14px;border:1px solid #f3c9c7}
.small-muted{color:#6b7890;font-size:.9rem}
</style>
""", unsafe_allow_html=True)

if "step" not in st.session_state: st.session_state.step=0
if "completed" not in st.session_state: st.session_state.completed=False
if "selected_algorithm" not in st.session_state: st.session_state.selected_algorithm="LPR"

with st.sidebar:
    st.markdown("## 🧠 Page Replacement Lab")
    st.caption("Interactive Operating Systems Simulator")
    st.divider()

    page=st.radio("Navigate",["🏠 Overview","🧪 Simulator","📊 Comparison","📘 Theory"])

    st.divider()
    st.markdown("### Simulation setup")

    algorithm=st.selectbox(
        "Algorithm to simulate",
        ["FIFO","LRU","MRU","MFU","Second Chance","Optimal","LPR"],
        index=["FIFO","LRU","MRU","MFU","Second Chance","Optimal","LPR"].index(st.session_state.selected_algorithm)
    )
    st.session_state.selected_algorithm=algorithm

    frames=st.number_input("Number of frames",1,12,3,1)
    ref_text=st.text_area("Reference string","7 0 1 2 0 3 0 4 2 3 0 3 2",height=100)

    if algorithm=="LPR":
        st.caption("LPR uses adaptive LRU/MRU policy selection.")
    elif algorithm=="MFU":
        st.caption("MFU replaces the resident page with the highest access frequency.")
    elif algorithm=="Second Chance":
        st.caption("Second Chance uses FIFO order plus reference bits to give recently used pages another chance.")
    st.session_state.mode=st.radio(
        "Visualization mode",["Detailed steps","Main steps only"]
    )
    speed=st.select_slider("Animation speed",
        ["Very slow","Slow","Normal","Fast","Very fast"],"Normal")

    if st.button("↻ Reset simulation",use_container_width=True):
        st.session_state.step=0
        st.session_state.completed=False
        st.rerun()

def get_results():
    refs=parse_reference_string(ref_text)
    if not refs: return None,"Enter at least one page."
    if len(refs)>500: return None,"Keep the reference string at 500 pages or fewer."
    return simulate_all(refs,int(frames)),None

def current_algorithm_data(results):
    return results[st.session_state.selected_algorithm]

def metric_cards(summary):
    cols=st.columns(4)
    vals=[("Page Faults",summary["faults"]),("Page Hits",summary["hits"]),
          ("Miss Ratio",f'{summary["miss_ratio"]:.2%}'),
          ("Hit Ratio",f'{summary["hit_ratio"]:.2%}')]
    for c,(label,value) in zip(cols,vals):
        with c:
            st.markdown(
                f'<div class="metric-card"><div class="small-muted">{label}</div>'
                f'<h2>{value}</h2></div>',unsafe_allow_html=True)

def frame_box(frames_list):
    cols=st.columns(len(frames_list))
    for i,value in enumerate(frames_list):
        with cols[i]:
            display="—" if value is None else str(value)
            st.markdown(
                f'<div class="card" style="text-align:center">'
                f'<div class="small-muted">Frame {i+1}</div><h3>{display}</h3></div>',
                unsafe_allow_html=True)

# OVERVIEW
if page=="🏠 Overview":
    st.title("Page Replacement Lab")
    st.markdown("### Learn, simulate, visualize and compare page replacement algorithms")

    st.markdown("""
    <div class="card">
    <h3>How the simulator works</h3>
    <p><b>1. Configure:</b> Select an algorithm, enter the number of memory frames,
    and provide a page reference string.</p>
    <p><b>2. Simulate:</b> The simulator processes one page at a time. For every
    reference it shows whether the result is a <b>Hit</b> or <b>Miss / Page Fault</b>.</p>
    <p><b>3. Visualize:</b> Watch the contents of every memory frame change after
    each reference.</p>
    <p><b>4. Analyze:</b> After the complete simulation, view page faults, page hits,
    hit ratio, miss ratio and graphical results.</p>
    <p><b>5. Compare:</b> Once the selected simulation is complete, compare all
    supported algorithms using the same input.</p>
    </div>
    """,unsafe_allow_html=True)

    a,b,c,d=st.columns(4)
    a.markdown("#### ① Select"); a.write("Choose the page replacement algorithm.")
    b.markdown("#### ② Enter"); b.write("Set frames and reference string.")
    c.markdown("#### ③ Step"); c.write("Process references one at a time.")
    d.markdown("#### ④ Analyze"); d.write("Study results and comparisons.")

    st.info("Go to **Simulator** to begin. The Comparison page becomes available only after the selected simulation reaches the final reference.")

# THEORY
elif page=="📘 Theory":
    st.title("📘 Page Replacement Theory")

    st.markdown("""
## Page Replacement Algorithm — Definition

A **page replacement algorithm** is an operating-system method used to decide
which page should be removed from physical memory when a new page needs to be
loaded and all available memory frames are occupied.

The main objective is to reduce the number of **page faults** and improve memory
management performance.

## Basic Terms

### Page
A page is a fixed-size block of a process's virtual memory.

### Frame
A frame is a fixed-size block of physical memory that can hold one page.

### Page Reference String
A sequence showing the order in which pages are requested by a process.

Example:

`7 0 1 2 0 3 0 4`

### Page Hit
A **page hit** occurs when the requested page is already present in one of the
memory frames.

**Result:** No page replacement is required.

### Page Fault
A **page fault** occurs when the requested page is not present in physical memory.

If all frames are full, a replacement algorithm must select a page to remove.

### Page Fault Rate / Miss Ratio

`Miss Ratio = Number of Page Faults / Total Page References`

### Hit Ratio

`Hit Ratio = Number of Page Hits / Total Page References`

### Memory Frame
The physical-memory slot where a page is stored.

---

## Page Replacement Algorithms

### 1. FIFO — First In, First Out

FIFO removes the page that entered memory **first**.

**Rule:** The oldest loaded page is replaced first.

**Advantage:** Simple and easy to implement.

**Disadvantage:** It may remove a frequently used page.

---

### 2. LRU — Least Recently Used

LRU removes the page that has **not been used for the longest period of time**.

**Rule:** Replace the least recently accessed page.

**Example idea:**

If the pages were recently used in the order:

`2 → 4 → 1`

then page `2` is the oldest among these recent accesses and can become
the LRU candidate.

---

### 3. MRU — Most Recently Used

MRU removes the page that was **used most recently**.

**Rule:** Replace the most recently accessed page.

MRU can be useful for some access patterns where recently used pages are
unlikely to be needed again soon.

---

### 4. Optimal Page Replacement

The Optimal algorithm replaces the page whose **next use is farthest in the future**.

It provides the theoretical minimum number of page faults for a known reference
string.

**Important:** It requires knowledge of future page references, so it is mainly
used as a benchmark rather than a practical general-purpose OS algorithm.

---

### 5. MFU — Most Frequently Used

MFU replaces the resident page with the **highest access frequency**. The simulator
counts references to each page while it remains in memory; a newly loaded page starts
with a frequency of 1. If multiple pages tie for the highest frequency, the first one
in frame order is selected.

**Advantage:** Can retain pages that have been accessed less often when a workload
has a useful frequency pattern.

**Disadvantage:** A high count does not guarantee that a page will be needed again,
so MFU can evict a page that is still useful.

---

### 6. Second Chance (Clock)

Second Chance is similar to FIFO, but each page has a **reference bit**. When a page
is accessed, its bit is set to 1. On replacement, the algorithm checks the page at
the clock pointer: if its bit is 1, the bit is cleared to 0 and the page is skipped;
if its bit is 0, that page is replaced. The pointer then advances to the next frame.

**Advantage:** Recently referenced pages can avoid immediate eviction.

**Disadvantage:** It may scan several frames before finding a page with a 0 bit.

---

### 7. LPR — Learning-Based Page Replacement

LPR is an adaptive approach used in this project.

It considers **LRU and MRU as candidate replacement policies** and uses a learning
mechanism to adjust their policy weights based on observed eviction outcomes.

Conceptually:

`Reference → LRU candidate + MRU candidate → Learning → Policy selection → Victim`

The goal is to adapt the replacement decision to the observed workload instead
of always using one fixed replacement rule.

---

## Performance Measures

| Measure | Meaning |
|---|---|
| Page Faults | Number of requested pages not found in memory |
| Page Hits | Number of requested pages found in memory |
| Miss Ratio | Page Faults ÷ Total References |
| Hit Ratio | Page Hits ÷ Total References |
| Frames | Number of available physical-memory slots |
| Reference String | Order of requested pages |
""")

# SIMULATOR
elif page=="🧪 Simulator":
    st.title("🧪 Interactive Simulator")
    results,error=get_results()
    if error:
        st.error(error); st.stop()

    data=results[st.session_state.selected_algorithm]
    steps=data["steps"]
    max_step=len(steps)
    st.session_state.step=min(st.session_state.step,max_step)

    st.markdown(
        f'<div class="small-muted">Algorithm: <b>{st.session_state.selected_algorithm}</b> · '
        f'Frames: <b>{int(frames)}</b> · References: <b>{len(steps)}</b> · '
        f'Mode: <b>{st.session_state.mode}</b></div>',unsafe_allow_html=True)

    c1,c2,c3,c4=st.columns(4)
    with c1:
        if st.button("⏮ Start",use_container_width=True):
            st.session_state.step=0; st.session_state.completed=False; st.rerun()
    with c2:
        if st.button("← Previous",use_container_width=True,disabled=st.session_state.step<=0):
            st.session_state.step-=1; st.session_state.completed=False; st.rerun()
    with c3:
        if st.button("Next →",type="primary",use_container_width=True,
                     disabled=st.session_state.step>=max_step):
            st.session_state.step+=1
            st.session_state.completed=st.session_state.step>=max_step
            st.rerun()
    with c4:
        if st.button("End ⏭",use_container_width=True):
            st.session_state.step=max_step
            st.session_state.completed=True
            st.rerun()

    st.progress(st.session_state.step/max_step if max_step else 0)
    st.caption(f"Reference {st.session_state.step} of {max_step}")

    if st.session_state.step==0:
        st.markdown("""<div class="step-card"><h3>Ready to simulate</h3>
        <p>Press <b>Next →</b> to process exactly one reference.</p>
        <p>The simulator will show the current page, whether it is a Hit or Miss,
        and the current frame contents.</p></div>""",unsafe_allow_html=True)
    else:
        s=steps[st.session_state.step-1]
        cls="hit-box" if s["hit"] else "miss-box"
        status="PAGE HIT" if s["hit"] else "PAGE MISS / FAULT"
        st.markdown(
            f'<div class="{cls}"><h2>{status}</h2>'
            f'<p>Requested page: <b>{s["page"]}</b> · Step: <b>{s["step"]}</b></p></div>',
            unsafe_allow_html=True)

        if st.session_state.mode=="Detailed steps":
            if st.session_state.selected_algorithm=="LPR":
                a,b,c=st.columns(3)
                a.metric("Page",s["page"])
                b.metric("LRU candidate",s.get("lru_candidate","—"))
                c.metric("MRU candidate",s.get("mru_candidate","—"))
                st.markdown("#### LPR decision")
                st.write(s.get("explanation",""))
                a,b=st.columns(2)
                a.metric("LRU weight",f'{s.get("lru_weight",0):.4f}',
                         delta=f'{s.get("lru_weight",0)-s.get("decision_lru_weight",s.get("lru_weight",0)):+.4f}' if s.get("lru_weight",0) != s.get("decision_lru_weight",s.get("lru_weight",0)) else None)
                b.metric("MRU weight",f'{s.get("mru_weight",0):.4f}',
                         delta=f'{s.get("mru_weight",0)-s.get("decision_mru_weight",s.get("mru_weight",0)):+.4f}' if s.get("mru_weight",0) != s.get("decision_mru_weight",s.get("mru_weight",0)) else None)
                st.caption(f"Weights used for this replacement decision: LRU {s.get('decision_lru_weight', s.get('lru_weight', 0)):.4f} · MRU {s.get('decision_mru_weight', s.get('mru_weight', 0)):.4f}")
                st.markdown("#### Learning feedback")
                if s.get("learning_events"):
                    for event in s["learning_events"]:
                        st.success(event)
                else:
                    st.caption(s.get("learning_explanation", "No weight update at this step."))
            else:
                st.markdown("#### Replacement decision")
                st.write(s.get("explanation",f"{st.session_state.selected_algorithm} processes this reference."))
                if not s["hit"]:
                    st.warning(f'Victim selected: **{s.get("victim","—")}**')
                if st.session_state.selected_algorithm=="MFU":
                    st.markdown("#### Resident page frequencies")
                    st.json(s.get("frequencies",{}))
                elif st.session_state.selected_algorithm=="Second Chance":
                    st.markdown("#### Reference bits and clock pointer")
                    st.write("Reference bits (1 = recently referenced; 0 = eligible for replacement):")
                    st.json(s.get("reference_bits",{}))
                    st.write(f'Clock pointer: frame index {s.get("clock_pointer",0)}')

        st.markdown("#### Current memory frames")
        frame_box(s["frames"])

        if st.session_state.mode=="Detailed steps":
            with st.expander("Technical state"):
                st.json(s)

    if st.session_state.completed:
        st.success("Simulation completed. The Comparison page is now unlocked.")
        metric_cards(data["summary"])

# COMPARISON
elif page=="📊 Comparison":
    if not st.session_state.completed:
        st.title("📊 Comparison")
        st.warning("Complete the selected simulation first.")
        st.info("Go to Simulator → press Next through the final reference. Comparison will then unlock.")
        st.stop()

    st.title("📊 Comparison & Analysis")
    results,error=get_results()
    if error: st.error(error); st.stop()

    rows=[]
    for name,data in results.items():
        s=data["summary"]
        rows.append({"Algorithm":name,"Page Faults":s["faults"],
                     "Page Hits":s["hits"],"Miss Ratio":s["miss_ratio"],
                     "Hit Ratio":s["hit_ratio"]})
    df=pd.DataFrame(rows)

    st.markdown("### Performance table")
    display=df.copy()
    display["Miss Ratio"]=display["Miss Ratio"].map(lambda x:f"{x:.2%}")
    display["Hit Ratio"]=display["Hit Ratio"].map(lambda x:f"{x:.2%}")
    st.dataframe(display,use_container_width=True,hide_index=True)

    c1,c2=st.columns(2)
    with c1:
        fig=go.Figure()
        fig.add_bar(x=df["Algorithm"],y=df["Page Faults"])
        fig.update_layout(title="Page Faults",template="plotly_white")
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        fig=go.Figure()
        fig.add_bar(x=df["Algorithm"],y=df["Page Hits"])
        fig.update_layout(title="Page Hits",template="plotly_white")
        st.plotly_chart(fig,use_container_width=True)

    c1,c2=st.columns(2)
    with c1:
        fig=go.Figure()
        fig.add_bar(x=df["Algorithm"],y=df["Miss Ratio"])
        fig.update_layout(title="Miss Ratio",yaxis_tickformat=".0%",template="plotly_white")
        st.plotly_chart(fig,use_container_width=True)
    with c2:
        fig=go.Figure()
        fig.add_bar(x=df["Algorithm"],y=df["Hit Ratio"])
        fig.update_layout(title="Hit Ratio",yaxis_tickformat=".0%",template="plotly_white")
        st.plotly_chart(fig,use_container_width=True)

    if st.session_state.selected_algorithm=="LPR":
        lpr_df=pd.DataFrame(results["LPR"]["steps"])
        st.markdown("### LPR learning weights")
        fig=go.Figure()
        fig.add_scatter(x=lpr_df["step"],y=lpr_df["lru_weight"],
                        mode="lines+markers",name="LRU weight")
        fig.add_scatter(x=lpr_df["step"],y=lpr_df["mru_weight"],
                        mode="lines+markers",name="MRU weight")
        fig.update_layout(title="LPR Learning Weights Over Time",
                          xaxis_title="Reference step",yaxis_title="Weight",
                          template="plotly_white")
        st.plotly_chart(fig,use_container_width=True)

    st.download_button("⬇ Download comparison CSV",df.to_csv(index=False).encode(),
                       "page_replacement_comparison.csv","text/csv",use_container_width=True)
