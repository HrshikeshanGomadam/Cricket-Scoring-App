import streamlit as st
import pandas as pd

st.set_page_config(page_title="CricScore", layout="centered")
st.title("🏏 Professional Live Cricket Scorecard")

# --- Initialize Session State ---
if 'step' not in st.session_state:
    st.session_state.step = 'setup'
if 't1_squad' not in st.session_state:
    st.session_state.t1_squad = {}
if 't2_squad' not in st.session_state:
    st.session_state.t2_squad = {}
if 'match_log' not in st.session_state:
    st.session_state.match_log = []

def init_player():
    return {
        "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0, "strike_rate": "None",
        "mode_of_dismissal": "not out", "balls_bowled": 0, "wides": 0, "no_balls": 0,
        "runs_given": 0, "wickets": 0, "economy": "None"
    }

# --- 1. Match Setup ---
if st.session_state.step == 'setup':
    st.header("Match Setup")
    with st.form("setup_form"):
        over_limit = st.number_input("Match Overs:", min_value=1, value=20, step=1)
        col1, col2 = st.columns(2)
        with col1:
            team_1 = st.text_input("Team 1 Name:", "Team A")
            num_players_1 = st.number_input("Players on Team 1:", min_value=2, max_value=11, value=11)
        with col2:
            team_2 = st.text_input("Team 2 Name:", "Team B")
            num_players_2 = st.number_input("Players on Team 2:", min_value=2, max_value=11, value=11)
        
        if st.form_submit_button("Next: Enter Squads"):
            st.session_state.over_limit = over_limit
            st.session_state.team_1 = team_1
            st.session_state.team_2 = team_2
            st.session_state.num_players_1 = num_players_1
            st.session_state.num_players_2 = num_players_2
            st.session_state.step = 'squads'
            st.rerun()

# --- 2. Squad Setup ---
elif st.session_state.step == 'squads':
    st.header("Enter Squads")
    with st.form("squad_form"):
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(st.session_state.team_1)
            t1_names = [st.text_input(f"Player {i+1}", f"{st.session_state.team_1} P{i+1}", key=f"t1_{i}") for i in range(st.session_state.num_players_1)]
        with col2:
            st.subheader(st.session_state.team_2)
            t2_names = [st.text_input(f"Player {i+1}", f"{st.session_state.team_2} P{i+1}", key=f"t2_{i}") for i in range(st.session_state.num_players_2)]
                
        if st.form_submit_button("Next: Toss Details"):
            st.session_state.t1_squad = {name: init_player() for name in t1_names if name.strip()}
            st.session_state.t2_squad = {name: init_player() for name in t2_names if name.strip()}
            st.session_state.step = 'toss'
            st.rerun()

# --- 3. Toss Info ---
elif st.session_state.step == 'toss':
    st.header("Toss Details")
    with st.form("toss_form"):
        toss_victor = st.radio("Who won the toss?", [st.session_state.team_1, st.session_state.team_2])
        toss_result = st.radio("Opted to:", ["Bat", "Bowl"])
        
        if st.form_submit_button("Start Match"):
            if (toss_victor == st.session_state.team_1 and toss_result == "Bat") or (toss_victor == st.session_state.team_2 and toss_result == "Bowl"):
                st.session_state.batting_team = st.session_state.team_1
                st.session_state.bowling_team = st.session_state.team_2
                st.session_state.bat_squad = st.session_state.t1_squad
                st.session_state.bowl_squad = st.session_state.t2_squad
                st.session_state.max_wickets = st.session_state.num_players_1 - 1
            else:
                st.session_state.batting_team = st.session_state.team_2
                st.session_state.bowling_team = st.session_state.team_1
                st.session_state.bat_squad = st.session_state.t2_squad
                st.session_state.bowl_squad = st.session_state.t1_squad
                st.session_state.max_wickets = st.session_state.num_players_2 - 1
            
            st.session_state.score = 0
            st.session_state.wickets = 0
            st.session_state.balls_bowled = 0
            st.session_state.wide_count = 0
            st.session_state.no_ball_count = 0
            st.session_state.byes_count = 0
            st.session_state.leg_byes_count = 0
            st.session_state.innings = 1
            
            player_keys = list(st.session_state.bat_squad.keys())
            st.session_state.striker = player_keys[0]
            st.session_state.non_striker = player_keys[1] if len(player_keys) > 1 else player_keys[0]
            st.session_state.current_bowler = list(st.session_state.bowl_squad.keys())[0]
            st.session_state.step = 'live_match'
            st.rerun()

# --- 4. COMPACT Live Match Interface ---
elif st.session_state.step == 'live_match':
    overs = st.session_state.balls_bowled // 6
    rem_balls = st.session_state.balls_bowled % 6
    is_all_out = st.session_state.wickets >= st.session_state.max_wickets
    
    # Header Broadcast Strip (Takes up minimal space)
    ov_str = f"{overs}.{rem_balls}"
    st.markdown(f"### **{st.session_state.batting_team}**: `{st.session_state.score}/{st.session_state.wickets}` ({ov_str} Ov)")
    
    # Mini Active State Monitor
    s_p = st.session_state.bat_squad[st.session_state.striker]
    ns_p = st.session_state.bat_squad[st.session_state.non_striker]
    b_p = st.session_state.bowl_squad[st.session_state.current_bowler]
    
    st.caption(f"🏏 **{st.session_state.striker}***: {s_p['runs']}({s_p['balls_faced']}) | {st.session_state.non_striker}: {ns_p['runs']}({ns_p['balls_faced']})")
    st.caption(f"🥎 **{st.session_state.current_bowler}**: {b_p['wickets']}-{b_p['runs_given'] + b_p['wides'] + b_p['no_balls']} ({b_p['balls_bowled']//6}.{b_p['balls_bowled']%6} Ov)")

    # Callbacks & Mathematical Engines
    def recalculate_metrics():
        for b in st.session_state.bat_squad:
            faced = st.session_state.bat_squad[b]["balls_faced"]
            if faced > 0:
                st.session_state.bat_squad[b]["strike_rate"] = round((st.session_state.bat_squad[b]["runs"] / faced) * 100, 1)
        for bowl in st.session_state.bowl_squad:
            b_bowled = st.session_state.bowl_squad[bowl]["balls_bowled"]
            if b_bowled > 0:
                total_runs_given = (st.session_state.bowl_squad[bowl]["runs_given"] + 
                                    st.session_state.bowl_squad[bowl]["wides"] + 
                                    st.session_state.bowl_squad[bowl]["no_balls"])
                st.session_state.bowl_squad[bowl]["economy"] = round((total_runs_given / b_bowled) * 6, 2)

    def handle_strike_rotation(runs):
        if runs % 2 != 0:
            st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker

    def check_over_completion():
        if st.session_state.balls_bowled % 6 == 0 and st.session_state.balls_bowled > 0:
            st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker

    def score_normal_delivery(runs):
        st.session_state.bat_squad[st.session_state.striker]["runs"] += runs
        st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
        if runs == 4: st.session_state.bat_squad[st.session_state.striker]["fours"] += 1
        if runs == 6: st.session_state.bat_squad[st.session_state.striker]["sixes"] += 1
        
        st.session_state.bowl_squad[st.session_state.current_bowler]["runs_given"] += runs
        st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
        st.session_state.score += runs
        st.session_state.balls_bowled += 1
        st.session_state.match_log.append(str(runs))
        handle_strike_rotation(runs)
        check_over_completion()
        recalculate_metrics()
        st.rerun()

    # Matrix Scoring Box (CricClubs Style Grid Layout)
    st.write("---")
    r1_c1, r1_c2, r1_c3 = st.columns(3)
    r2_c1, r2_c2, r2_c3 = st.columns(3)
    r3_c1, r3_c2, r3_c3 = st.columns(3)
    
    with r1_c1: 
        if st.button("0", disabled=is_all_out, use_container_width=True): score_normal_delivery(0)
    with r1_c2: 
        if st.button("1", disabled=is_all_out, use_container_width=True): score_normal_delivery(1)
    with r1_c3: 
        if st.button("2", disabled=is_all_out, use_container_width=True): score_normal_delivery(2)
        
    with r2_c1: 
        if st.button("3", disabled=is_all_out, use_container_width=True): score_normal_delivery(3)
    with r2_c2: 
        if st.button("4", disabled=is_all_out, use_container_width=True): score_normal_delivery(4)
    with r2_c3: 
        if st.button("6", disabled=is_all_out, use_container_width=True): score_normal_delivery(6)

    # Uncommon runs selection & immediate line-up override dropdowns inside row 3
    with r3_c1:
        uncommon_val = st.number_input("Odd", min_value=0, max_value=10, value=5, step=1, label_visibility="collapsed")
    with r3_c2:
        if st.button(f"+{uncommon_val}", disabled=is_all_out, use_container_width=True): score_normal_delivery(uncommon_val)
    with r3_c3:
        available_batters = [k for k, v in st.session_state.bat_squad.items() if v["mode_of_dismissal"] == "not out"]
        st.session_state.striker = st.selectbox("Striker", available_batters, index=available_batters.index(st.session_state.striker), label_visibility="collapsed")

    # --- Collapsible Advanced Expanders (Keeps screen perfectly clean) ---
    st.write(" ")
    with st.expander("➕ Extras (Wd / Nb / Byes)"):
        ex_type = st.selectbox("Select Extra Type", ["Wide", "No Ball", "Leg Byes", "Byes"])
        ex_runs = st.number_input("Additional Runs off Delivery:", min_value=0, max_value=10, value=0, step=1)
        nb_scoring_mode = st.radio("Scoring Method (No Balls Only):", ["Bat", "Byes/None"], horizontal=True)
        
        if st.button("Submit Extra Delivery", disabled=is_all_out, use_container_width=True, type="primary"):
            if ex_type == "Wide":
                st.session_state.bowl_squad[st.session_state.current_bowler]["wides"] += (ex_runs + 1)
                st.session_state.wide_count += (ex_runs + 1)
                st.session_state.score += (ex_runs + 1)
                st.session_state.match_log.append("Wd")
                handle_strike_rotation(ex_runs)
            elif ex_type == "No Ball":
                st.session_state.no_ball_count += 1
                if nb_scoring_mode == "Bat":
                    st.session_state.bat_squad[st.session_state.striker]["runs"] += ex_runs
                    st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += (ex_runs + 1)
                    st.session_state.score += (ex_runs + 1)
                else:
                    st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += 1
                    st.session_state.score += (ex_runs + 1)
                st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                st.session_state.match_log.append("Nb")
                handle_strike_rotation(ex_runs)
            elif ex_type == "Leg Byes":
                st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                st.session_state.leg_byes_count += ex_runs
                st.session_state.score += ex_runs
                st.session_state.balls_bowled += 1
                st.session_state.match_log.append("Lb")
                handle_strike_rotation(ex_runs)
                check_over_completion()
            elif ex_type == "Byes":
                st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                st.session_state.byes_count += ex_runs
                st.session_state.score += ex_runs
                st.session_state.balls_bowled += 1
                st.session_state.match_log.append("B")
                handle_strike_rotation(ex_runs)
                check_over_completion()
            recalculate_metrics()
            st.rerun()

    with st.expander("💥 Dismissals / Wickets"):
        w_mode = st.selectbox("Method of Dismissal", ["Bowled", "Caught", "LBW", "Stumped", "Run Out", "Hit Wicket", "Mankad"])
        delivery_context = st.radio("Delivery Context", ["Normal", "Wide", "No Ball"], horizontal=True)
        
        if delivery_context in ["Wide", "No Ball"] and w_mode not in ["Run Out", "Mankad", "Stumped"]:
            st.warning(f"⚠️ A batter cannot be dismissed via '{w_mode}' on a {delivery_context}.")
        else:
            if w_mode == "Run Out":
                target_batter = st.selectbox("Batter Run Out", [st.session_state.striker, st.session_state.non_striker])
                target_end = st.selectbox("Run Out End", ["Keeper", "Bowler"])
                ro_runs = st.number_input("Runs Completed Prior to Out:", min_value=0, max_value=6, value=0)
                
                if st.button("Confirm Run Out Wicket", type="primary", use_container_width=True):
                    st.session_state.bat_squad[target_batter]["mode_of_dismissal"] = "run out"
                    if delivery_context == "Wide":
                        st.session_state.bowl_squad[st.session_state.current_bowler]["wides"] += (ro_runs + 1)
                        st.session_state.score += (ro_runs + 1)
                    elif delivery_context == "No Ball":
                        st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += (ro_runs + 1)
                        st.session_state.score += (ro_runs + 1)
                    else:
                        st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                        st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                        st.session_state.bowl_squad[st.session_state.current_bowler]["runs_given"] += ro_runs
                        st.session_state.score += ro_runs
                        st.session_state.balls_bowled += 1
                    
                    if target_batter == st.session_state.striker and target_end != "Keeper":
                        st.session_state.striker = st.session_state.non_striker
                    elif target_batter != st.session_state.striker and target_end == "Keeper":
                        st.session_state.non_striker = st.session_state.striker

                    st.session_state.wickets += 1
                    st.session_state.match_log.append("W")
                    if delivery_context not in ["Wide", "No Ball"]:
                        check_over_completion()
                    recalculate_metrics()
                    st.rerun()
            else:
                if st.button("Confirm Wicket", type="primary", use_container_width=True):
                    out_p = st.session_state.non_striker if w_mode == "Mankad" else st.session_state.striker
                    st.session_state.bat_squad[out_p]["mode_of_dismissal"] = w_mode
                    if w_mode != "Mankad":
                        st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                        st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                        st.session_state.bowl_squad[st.session_state.current_bowler]["wickets"] += 1
                        st.session_state.balls_bowled += 1
                    st.session_state.wickets += 1
                    st.session_state.match_log.append("W")
                    if w_mode != "Mankad":
                        check_over_completion()
                    recalculate_metrics()
                    st.rerun()

    with st.expander("🔄 Setup Lineup Overrides"):
        bowlers = list(st.session_state.bowl_squad.keys())
        st.session_state.non_striker = st.selectbox("Non-Striker Override", available_batters, index=available_batters.index(st.session_state.non_striker))
        st.session_state.current_bowler = st.selectbox("Bowler Override", bowlers, index=bowlers.index(st.session_state.current_bowler))

    # Real-time Match Stream Log
    if st.session_state.match_log:
        st.caption(f"**Recent:** {' | '.join(st.session_state.match_log[-8:])}")

    # --- Full Cards Display Tables (Tucked out of primary mobile view) ---
    st.write("---")
    df_bat = pd.DataFrame.from_dict(st.session_state.bat_squad, orient='index')[["runs", "balls_faced", "fours", "sixes", "strike_rate", "mode_of_dismissal"]]
    df_bowl = pd.DataFrame.from_dict(st.session_state.bowl_squad, orient='index')[["balls_bowled", "wides", "no_balls", "runs_given", "wickets", "economy"]]
    
    t1, t2 = st.tabs(["Batting", "Bowling"])
    with t1: st.dataframe(df_bat, use_container_width=True)
    with t2: st.dataframe(df_bowl, use_container_width=True)

    # Innings Transitions Boundary Handlers
    total_allowed_balls = st.session_state.over_limit * 6
    target_met = (st.session_state.innings == 2 and st.session_state.score >= st.session_state.target)
    
    if st.session_state.balls_bowled >= total_allowed_balls or is_all_out or target_met:
        st.write("---")
        if st.session_state.innings == 1:
            st.warning("First Innings Completed!")
            if st.button("Switch to Second Innings", use_container_width=True, type="primary"):
                st.session_state.innings = 2
                st.session_state.target = st.session_state.score + 1
                st.session_state.batting_team, st.session_state.bowling_team = st.session_state.bowling_team, st.session_state.batting_team
                st.session_state.bat_squad, st.session_state.bowl_squad = st.session_state.bowl_squad, st.session_state.bat_squad
                st.session_state.max_wickets = st.session_state.num_players_2 - 1 if st.session_state.batting_team == st.session_state.team_2 else st.session_state.num_players_1 - 1
                
                st.session_state.score = 0
                st.session_state.wickets = 0
                st.session_state.balls_bowled = 0
                st.session_state.wide_count = 0
                st.session_state.no_ball_count = 0
                st.session_state.byes_count = 0
                st.session_state.leg_byes_count = 0
                st.session_state.match_log = []
                
                player_keys = list(st.session_state.bat_squad.keys())
                st.session_state.striker = player_keys[0]
                st.session_state.non_striker = player_keys[1] if len(player_keys) > 1 else player_keys[0]
                st.session_state.current_bowler = list(st.session_state.bowl_squad.keys())[0]
                st.rerun()
        else:
            st.success("🎉 Match Finished!")
            if st.session_state.score >= st.session_state.target:
                st.write(f"### **{st.session_state.batting_team} won the match!**")
            elif st.session_state.score == st.session_state.target - 1:
                st.write("### **Match ended in a Tie!**")
            else:
                st.write(f"### **{st.session_state.bowling_team} won by {st.session_state.target - 1 - st.session_state.score} runs!**")
            
            if st.button("Reset Configuration", use_container_width=True):
                st.session_state.clear()
                st.rerun()
