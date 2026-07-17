import streamlit as st
import pandas as pd
import math

st.set_page_config(page_title="Live Cricket Scorecard", layout="wide")
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

# --- 4. Live Match Dashboard ---
elif st.session_state.step == 'live_match':
    overs = st.session_state.balls_bowled // 6
    rem_balls = st.session_state.balls_bowled % 6
    is_all_out = st.session_state.wickets >= st.session_state.max_wickets
    
    st.header(f"Innings {st.session_state.innings}: {st.session_state.batting_team} Batting")
    if is_all_out:
        st.error(f"🔴 Score: {st.session_state.score}/All Out ({overs}.{rem_balls} Overs)")
    else:
        st.subheader(f"Score: {st.session_state.score}/{st.session_state.wickets} ({overs}.{rem_balls} Overs)")
    
    # Selection Lists for Active Lineups
    c1, c2, c3 = st.columns(3)
    with c1:
        available_batters = [k for k, v in st.session_state.bat_squad.items() if v["mode_of_dismissal"] == "not out"]
        if st.session_state.striker in available_batters:
            st.session_state.striker = st.selectbox("Striker (*)", available_batters, index=available_batters.index(st.session_state.striker))
        else:
            st.session_state.striker = st.selectbox("Striker (*)", available_batters, index=0 if available_batters else None)
    with c2:
        if st.session_state.non_striker in available_batters:
            st.session_state.non_striker = st.selectbox("Non-Striker", available_batters, index=available_batters.index(st.session_state.non_striker))
        else:
            st.session_state.non_striker = st.selectbox("Non-Striker", available_batters, index=min(1, len(available_batters)-1) if available_batters else None)
    with c3:
        bowlers = list(st.session_state.bowl_squad.keys())
        st.session_state.current_bowler = st.selectbox("Current Bowler", bowlers, index=bowlers.index(st.session_state.current_bowler))

    # Dynamic Math Metric Engine
    def recalculate_metrics():
        for b in st.session_state.bat_squad:
            faced = st.session_state.bat_squad[b]["balls_faced"]
            if faced > 0:
                st.session_state.bat_squad[b]["strike_rate"] = round((st.session_state.bat_squad[b]["runs"] / faced) * 100, 2)
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
            st.info("🔄 Over complete! Change the bowler or continue.")

    # Core Scoring Actions
    def score_normal_delivery(runs):
        st.session_state.bat_squad[st.session_state.striker]["runs"] += runs
        st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
        if runs == 4: st.session_state.bat_squad[st.session_state.striker]["fours"] += 1
        if runs == 6: st.session_state.bat_squad[st.session_state.striker]["sixes"] += 1
        
        st.session_state.bowl_squad[st.session_state.current_bowler]["runs_given"] += runs
        st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
        st.session_state.score += runs
        st.session_state.balls_bowled += 1
        st.session_state.match_log.append(f"{runs} Run(s)")
        handle_strike_rotation(runs)
        check_over_completion()
        recalculate_metrics()
        st.rerun()

    def score_extra_delivery(extra_type, runs_off_delivery, mode_of_scoring):
        if extra_type == "Wide":
            st.session_state.bowl_squad[st.session_state.current_bowler]["wides"] += (runs_off_delivery + 1)
            st.session_state.wide_count += (runs_off_delivery + 1)
            st.session_state.score += (runs_off_delivery + 1)
            st.session_state.match_log.append(f"Wide + {runs_off_delivery} Extra Run(s)")
            handle_strike_rotation(runs_off_delivery)
        elif extra_type == "No Ball":
            st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += 1
            st.session_state.no_ball_count += 1
            if mode_of_scoring == "Bat":
                st.session_state.bat_squad[st.session_state.striker]["runs"] += runs_off_delivery
                st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += runs_off_delivery
                st.session_state.score += (runs_off_delivery + 1)
            else:
                st.session_state.score += (runs_off_delivery + 1)
            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
            st.session_state.match_log.append(f"No Ball + {runs_off_delivery} Run(s)")
            handle_strike_rotation(runs_off_delivery)
        elif extra_type == "Leg Byes":
            st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
            st.session_state.leg_byes_count += runs_off_delivery
            st.session_state.score += runs_off_delivery
            st.session_state.balls_bowled += 1
            st.session_state.match_log.append(f"{runs_off_delivery} Leg Bye(s)")
            handle_strike_rotation(runs_off_delivery)
            check_over_completion()
        elif extra_type == "Byes":
            st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
            st.session_state.byes_count += runs_off_delivery
            st.session_state.score += runs_off_delivery
            st.session_state.balls_bowled += 1
            st.session_state.match_log.append(f"{runs_off_delivery} Bye(s)")
            handle_strike_rotation(runs_off_delivery)
            check_over_completion()
        recalculate_metrics()
        st.rerun()

    def score_wicket(dismissal, chosen_batter, run_out_end, runs_scored, nb_wide_context="Normal"):
        # Process Run Out Cross-Over Adjustments
        if dismissal == "Run Out":
            st.session_state.bat_squad[chosen_batter]["mode_of_dismissal"] = "run out"
            if nb_wide_context == "Wide":
                st.session_state.bowl_squad[st.session_state.current_bowler]["wides"] += (runs_scored + 1)
                st.session_state.score += (runs_scored + 1)
            elif nb_wide_context == "No Ball":
                st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += (runs_scored + 1)
                st.session_state.score += (runs_scored + 1)
            else:
                st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                st.session_state.bowl_squad[st.session_state.current_bowler]["runs_given"] += runs_scored
                st.session_state.score += runs_scored
                st.session_state.balls_bowled += 1
            
            # Complex Crossover Configuration based on Python source code
            if chosen_batter == st.session_state.striker:
                if run_out_end != "Keeper":
                    st.session_state.striker = st.session_state.non_striker
            else:
                if run_out_end == "Keeper":
                    st.session_state.non_striker = st.session_state.striker

            st.session_state.wickets += 1
            st.session_state.match_log.append(f"WICKET: Run Out ({chosen_batter})")
            if nb_wide_context not in ["Wide", "No Ball"]:
                check_over_completion()

        elif dismissal == "Mankad":
            st.session_state.bat_squad[st.session_state.non_striker]["mode_of_dismissal"] = "Mankad"
            st.session_state.wickets += 1
            st.session_state.match_log.append(f"WICKET: Mankad ({st.session_state.non_striker})")

        else: # Standard Dismissal (Bowled, Caught, LBW, Stumped, etc.)
            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
            st.session_state.bat_squad[st.session_state.striker]["mode_of_dismissal"] = dismissal
            st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
            st.session_state.bowl_squad[st.session_state.current_bowler]["wickets"] += 1
            st.session_state.wickets += 1
            st.session_state.balls_bowled += 1
            st.session_state.match_log.append(f"WICKET: {dismissal} ({st.session_state.striker})")
            check_over_completion()

        recalculate_metrics()
        st.rerun()

    # --- UI Layout Design ---
    st.write("---")
    tab_normal, tab_extras, tab_wickets = st.tabs(["🏏 Standard Scoring", "➕ Extras System", "💥 Dismissals / Wickets"])

    with tab_normal:
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("0 (Dot Ball)", disabled=is_all_out, use_container_width=True): score_normal_delivery(0)
            if st.button("1 Run", disabled=is_all_out, use_container_width=True): score_normal_delivery(1)
        with col2:
            if st.button("2 Runs", disabled=is_all_out, use_container_width=True): score_normal_delivery(2)
            if st.button("3 Runs", disabled=is_all_out, use_container_width=True): score_normal_delivery(3)
        with col3:
            if st.button("4 (Boundary)", disabled=is_all_out, use_container_width=True): score_normal_delivery(4)
            if st.button("6 (Maximum)", disabled=is_all_out, use_container_width=True): score_normal_delivery(6)
        
        st.write("**Uncommon Runs Dashboard**")
        uc_col1, uc_col2 = st.columns([1, 3])
        with uc_col1: uncommon_val = st.number_input("Value:", min_value=0, max_value=10, value=5, step=1, key="uc_val")
        with uc_col2: 
            st.write("##")
            if st.button("Register Uncommon Score", disabled=is_all_out): score_normal_delivery(uncommon_val)

    with tab_extras:
        ex_type = st.selectbox("Select Extra Type", ["Wide", "No Ball", "Leg Byes", "Byes"])
        ex_col1, ex_col2 = st.columns(2)
        with ex_col1:
            ex_runs = st.number_input("Additional Runs off Delivery:", min_value=0, max_value=10, value=0, step=1)
        with ex_col2:
            nb_scoring_mode = st.radio("Scoring Method (Only for No Balls):", ["Bat", "Byes/None"], horizontal=True)
        
        if st.button("Submit Extra Delivery", disabled=is_all_out, type="primary"):
            score_extra_delivery(ex_type, ex_runs, nb_scoring_mode)

    with tab_wickets:
        w_mode = st.selectbox("Method of Dismissal", ["Bowled", "Caught", "LBW", "Stumped", "Run Out", "Hit Wicket", "Mankad"])
        delivery_context = st.radio("Delivery Context", ["Normal", "Wide", "No Ball"], help="Wides and No Balls restrict standard dismissals to specialized outs like Run Outs.")
        
        # Guard clause implementing regular restriction rules on Extras
        if delivery_context in ["Wide", "No Ball"] and w_mode not in ["Run Out", "Mankad", "Stumped"]:
            st.warning(f"⚠️ A batter cannot be dismissed via '{w_mode}' on a {delivery_context} according to international regulations.")
        else:
            if w_mode == "Run Out":
                ro1, ro2, ro3 = st.columns(3)
                with ro1: target_batter = st.selectbox("Batter Run Out", [st.session_state.striker, st.session_state.non_striker])
                with ro2: target_end = st.selectbox("Run Out End", ["Keeper", "Bowler"])
                with ro3: ro_runs = st.number_input("Runs Completed Prior to Out:", min_value=0, max_value=6, value=0)
                
                if st.button("Confirm Run Out Wicket", type="primary"):
                    score_wicket("Run Out", target_batter, target_end, ro_runs, nb_wide_context=delivery_context)
            else:
                if st.button("Confirm Wicket", type="primary"):
                    score_wicket(w_mode, st.session_state.striker, "Keeper", 0, nb_wide_context=delivery_context)

    # --- Match Cards Tables ---
    st.write("---")
    st.subheader("📊 Live Match Scorecards")
    df_bat = pd.DataFrame.from_dict(st.session_state.bat_squad, orient='index')[["runs", "balls_faced", "fours", "sixes", "strike_rate", "mode_of_dismissal"]]
    df_bowl = pd.DataFrame.from_dict(st.session_state.bowl_squad, orient='index')[["balls_bowled", "wides", "no_balls", "runs_given", "wickets", "economy"]]
    
    t1, t2 = st.tabs(["Batting Statistics", "Bowling Statistics"])
    with t1: st.dataframe(df_bat, use_container_width=True)
    with t2: st.dataframe(df_bowl, use_container_width=True)

    # Innings / Transition Handling Boundaries
    total_allowed_balls = st.session_state.over_limit * 6
    target_met = (st.session_state.innings == 2 and st.session_state.score >= st.session_state.target)
    
    if st.session_state.balls_bowled >= total_allowed_balls or is_all_out or target_met:
        if st.session_state.innings == 1:
            st.warning("First Innings Completed!")
            if st.button("Switch to Second Innings"):
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
            
            if st.button("Reset Configuration"):
                st.session_state.clear()
                st.rerun()

    if st.session_state.match_log:
        st.write("---")
        st.write("**Recent Over Events:** " + " | ".join(st.session_state.match_log[-12:]))