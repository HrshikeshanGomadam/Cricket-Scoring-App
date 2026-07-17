import streamlit as st
import pandas as pd

st.set_page_config(page_title="CricScore", layout="centered")

# --- Initialize Session State ---
if 'step' not in st.session_state: st.session_state.step = 'setup'
if 'match_log' not in st.session_state: st.session_state.match_log = []

def init_p(): return {"runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0, "strike_rate": "0.0", "mode_of_dismissal": "not out", "balls_bowled": 0, "wides": 0, "no_balls": 0, "runs_given": 0, "wickets": 0, "economy": "0.0"}

# --- 1 & 2. Setup Loop (Unified for Speed) ---
if st.session_state.step == 'setup':
    with st.form("setup"):
        ov = st.number_input("Overs:", min_value=1, value=20)
        t1 = st.text_input("Team 1:", "Team A")
        t2 = st.text_input("Team 2:", "Team B")
        p_cnt = st.number_input("Players:", min_value=2, max_value=11, value=11)
        if st.form_submit_button("Start"):
            st.session_state.update({"over_limit": ov, "team_1": t1, "team_2": t2, "p_count": p_cnt, "batting_team": t1, "bowling_team": t2, "score": 0, "wickets": 0, "balls_bowled": 0, "wide_count": 0, "no_ball_count": 0, "byes_count": 0, "leg_byes_count": 0, "innings": 1, "max_wickets": p_cnt - 1})
            st.session_state.bat_squad = {f"{t1} P{i+1}": init_p() for i in range(p_cnt)}
            st.session_state.bowl_squad = {f"{t2} P{i+1}": init_p() for i in range(p_cnt)}
            st.session_state.striker, st.session_state.non_striker = list(st.session_state.bat_squad.keys())[:2]
            st.session_state.current_bowler = list(st.session_state.bowl_squad.keys())[0]
            st.session_state.step = 'live'
            st.rerun()

# --- 3. Compact Live Interface ---
elif st.session_state.step == 'live':
    is_all_out = st.session_state.wickets >= st.session_state.max_wickets
    
    # Header Broadcast Strip
    ov_str = f"{st.session_state.balls_bowled // 6}.{st.session_state.balls_bowled % 6}"
    st.markdown(f"### **{st.session_state.batting_team}**: `{st.session_state.score}/{st.session_state.wickets}` ({ov_str} Ov)")
    
    # Mini Active State Monitor
    s_p = st.session_state.bat_squad[st.session_state.striker]
    ns_p = st.session_state.bat_squad[st.session_state.non_striker]
    b_p = st.session_state.bowl_squad[st.session_state.current_bowler]
    
    st.caption(f"🏏 **{st.session_state.striker}***: {s_p['runs']}({s_p['balls_faced']}) | {st.session_state.non_striker}: {ns_p['runs']}({ns_p['balls_faced']})")
    st.caption(f"🥎 **{st.session_state.current_bowler}**: {b_p['wickets']}-{b_p['runs_given'] + b_p['wides'] + b_p['no_balls']} ({b_p['balls_bowled']//6}.{b_p['balls_bowled']%6} Ov)")

    # Callbacks & Logic Engines
    def recalc():
        for k, v in st.session_state.bat_squad.items():
            if v["balls_faced"] > 0: v["strike_rate"] = round((v["runs"]/v["balls_faced"])*100, 1)
        for k, v in st.session_state.bowl_squad.items():
            tb = v["balls_bowled"]
            if tb > 0: v["economy"] = round(((v["runs_given"] + v["wides"] + v["no_balls"])/tb)*6, 2)

    def next_b(r):
        st.session_state.bat_squad[st.session_state.striker].update({"runs": s_p["runs"]+r, "balls_faced": s_p["balls_faced"]+1})
        if r in [4, 6]: st.session_state.bat_squad[st.session_state.striker][f"fours" if r==4 else "sixes"] += 1
        st.session_state.bowl_squad[st.session_state.current_bowler]["runs_given"] += r
        st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
        st.session_state.score += r
        st.session_state.balls_bowled += 1
        st.session_state.match_log.append(str(r))
        if r % 2 != 0: st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker
        if st.session_state.balls_bowled % 6 == 0: st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker
        recalc(); st.rerun()

    # Matrix Scoring Box (CricClubs Style 3x3 Grid Layout)
    st.write("---")
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    r3_c1, r3_c2, r3_c3 = st.columns(3)
    
    with r1_c1: 
        if st.button("0", disabled=is_all_out, use_container_width=True): next_b(0)
    with r1_c2: 
        if st.button("1", disabled=is_all_out, use_container_width=True): next_b(1)
    with r1_c3: 
        if st.button("2", disabled=is_all_out, use_container_width=True): next_b(2)
        
    with r2_c1: 
        if st.button("3", disabled=is_all_out, use_container_width=True): next_b(3)
    with r2_c2: 
        if st.button("4", disabled=is_all_out, use_container_width=True): next_b(4)
    with r2_c3: 
        if st.button("6", disabled=is_all_out, use_container_width=True): next_b(6)

    # Uncommon runs & management tools integrated seamlessly inside the grid row
    with r3_c1:
        uc_val = st.number_input("Odd", min_value=0, max_value=10, value=5, label_visibility="collapsed")
    with r3_c2:
        if st.button(f"+{uc_val}", disabled=is_all_out, use_container_width=True, help="Register custom runs"): next_b(uc_val)
    with r3_c3:
        # Fast access lineup dropdown modifiers
        avail = [k for k, v in st.session_state.bat_squad.items() if v["mode_of_dismissal"] == "not out"]
        st.session_state.striker = st.selectbox("Str", avail, index=avail.index(st.session_state.striker), label_visibility="collapsed")

    # --- Collapsible Advanced Panels (Keeps phone clean) ---
    st.write(" ")
    with st.expander("➕ Extras (Wd / Nb / Byes)"):
        ex_t = st.selectbox("Type", ["Wide", "No Ball", "Leg Byes", "Byes"])
        ex_r = st.number_input("Runs off delivery", min_value=0, max_value=6, value=0)
        if st.button("Submit Extra", use_container_width=True):
            if ex_t == "Wide":
                st.session_state.bowl_squad[st.session_state.current_bowler]["wides"] += (ex_r + 1)
                st.session_state.score += (ex_r + 1)
                if ex_r % 2 != 0: st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker
            elif ex_t == "No Ball":
                st.session_state.bat_squad[st.session_state.striker]["runs"] += ex_r
                st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += (ex_r + 1)
                st.session_state.score += (ex_r + 1)
                if ex_r % 2 != 0: st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker
            elif ex_t in ["Leg Byes", "Byes"]:
                st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                st.session_state.score += ex_r
                st.session_state.balls_bowled += 1
                if ex_r % 2 != 0: st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker
                if st.session_state.balls_bowled % 6 == 0: st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker
            st.session_state.match_log.append(f"{ex_t[0] if ex_t != 'Leg Byes' else 'LB'}{ex_r if ex_r>0 else ''}")
            recalc(); st.rerun()

    with st.expander("💥 Dismissal Menu"):
        w_mode = st.selectbox("Dismissal Mode", ["Bowled", "Caught", "LBW", "Stumped", "Run Out", "Mankad"])
        ctx = st.radio("Context", ["Normal", "Wide", "No Ball"], horizontal=True)
        
        if w_mode == "Run Out":
            tgt = st.selectbox("Who Out?", [st.session_state.striker, st.session_state.non_striker])
            end = st.selectbox("End", ["Keeper", "Bowler"])
            ro_r = st.number_input("Runs completed", min_value=0, max_value=4, value=0)
            if st.button("Execute Run Out", type="primary", use_container_width=True):
                st.session_state.bat_squad[tgt]["mode_of_dismissal"] = "run out"
                if ctx == "Wide": st.session_state.score += (ro_r + 1); st.session_state.bowl_squad[st.session_state.current_bowler]["wides"] += (ro_r + 1)
                elif ctx == "No Ball": st.session_state.score += (ro_r + 1); st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += (ro_r + 1)
                else:
                    st.session_state.score += ro_r; st.session_state.balls_bowled += 1
                    st.session_state.bowl_squad[st.session_state.current_bowler]["runs_given"] += ro_r
                    st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                    st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                if tgt == st.session_state.striker and end != "Keeper": st.session_state.striker = st.session_state.non_striker
                elif tgt != st.session_state.striker and end == "Keeper": st.session_state.non_striker = st.session_state.striker
                st.session_state.wickets += 1; st.session_state.match_log.append("W")
                if ctx not in ["Wide", "No Ball"] and st.session_state.balls_bowled % 6 == 0: st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker
                recalc(); st.rerun()
        else:
            if ctx in ["Wide", "No Ball"] and w_mode not in ["Mankad", "Stumped"]:
                st.error("Illegal dismissal choice on an extra!")
            elif st.button("Trigger Wicket", type="primary", use_container_width=True):
                out_p = st.session_state.non_striker if w_mode == "Mankad" else st.session_state.striker
                st.session_state.bat_squad[out_p]["mode_of_dismissal"] = w_mode
                if w_mode != "Mankad":
                    st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                    st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                    st.session_state.bowl_squad[st.session_state.current_bowler]["wickets"] += 1
                    st.session_state.balls_bowled += 1
                st.session_state.wickets += 1; st.session_state.match_log.append("W")
                if w_mode != "Mankad" and st.session_state.balls_bowled % 6 == 0: st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker
                recalc(); st.rerun()

    with st.expander("🔄 Setup Lineup Overrides"):
        all_b = list(st.session_state.bowl_squad.keys())
        st.session_state.non_striker = st.selectbox("Non-Str Override", avail, index=avail.index(st.session_state.non_striker))
        st.session_state.current_bowler = st.selectbox("Bowler Select", all_b, index=all_b.index(st.session_state.current_bowler))

    # Real-time Match Stream Log
    if st.session_state.match_log:
        st.caption(f"**Recent:** {' | '.join(st.session_state.match_log[-8:])}")

    # Innings / Match Complete Controls
    tot_b = st.session_state.over_limit * 6
    t_met = (st.session_state.innings == 2 and st.session_state.score >= st.session_state.target)
    if st.session_state.balls_bowled >= tot_b or is_all_out or t_met:
        st.write("---")
        if st.session_state.innings == 1:
            if st.button("Proceed to 2nd Innings", use_container_width=True, type="primary"):
                st.session_state.update({"innings": 2, "target": st.session_state.score + 1, "batting_team": st.session_state.bowling_team, "bowling_team": st.session_state.batting_team, "bat_squad": st.session_state.bowl_squad, "bowl_squad": st.session_state.bat_squad, "score": 0, "wickets": 0, "balls_bowled": 0, "max_wickets": st.session_state.p_count - 1, "match_log": []})
                st.session_state.striker, st.session_state.non_striker = list(st.session_state.bat_squad.keys())[:2]
                st.session_state.current_bowler = list(st.session_state.bowl_squad.keys())[0]
                st.rerun()
        else:
            if st.session_state.score >= st.session_state.target: st.success(f"🎉 {st.session_state.batting_team} Won!")
            elif st.session_state.score == st.session_state.target - 1: st.info("Tie Match!")
            else: st.error(f"🎉 {st.session_state.bowling_team} Won!")
            if st.button("Reset Scorecard", use_container_width=True): st.session_state.clear(); st.rerun()
