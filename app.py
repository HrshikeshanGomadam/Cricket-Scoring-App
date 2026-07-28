import streamlit as st
import pandas as pd
import math
import json
import os

st.set_page_config(page_title="CricScore", layout="centered")

DB_FILE = "cricscore_backup.json"

# --- Persistent Storage Layer Engines ---
def save_match_state():
    """Serializes core session state keys into a local JSON file."""
    keys_to_save = [
        'step', 't1_squad', 't2_squad', 'match_log', 'commentary', 
        'over_runs', 'over_wickets', 'wicket_trigger', 'last_out_position', 
        'last_over_bowler', 'innings_1_batting', 'over_limit', 'team_1', 
        'team_2', 'num_players_1', 'num_players_2', 'batting_team', 
        'bowling_team', 'bat_squad', 'bowl_squad', 'max_wickets', 
        'score', 'wickets', 'balls_bowled', 'innings', 'striker', 
        'non_striker', 'current_bowler', 'target'
    ]
    state_data = {}
    for key in keys_to_save:
        if key in st.session_state:
            state_data[key] = st.session_state[key]
            
    with open(DB_FILE, "w") as f:
        json.dump(state_data, f, indent=4)

def load_match_state():
    """Loads backup match data into session state if it exists."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                state_data = json.load(f)
            for key, value in state_data.items():
                st.session_state[key] = value
            return True
        except Exception:
            return False
    return False

def clear_backup():
    """Deletes the backup file upon match completion or reset."""
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

# --- Initialize / Hydrate Session State ---
if 'initialized' not in st.session_state:
    has_backup = load_match_state()
    st.session_state.initialized = True
    if has_backup:
        st.toast("🔄 Recovered past match data from auto-save!", icon="ℹ️")

if 'step' not in st.session_state:
    st.session_state.step = 'setup'
if 't1_squad' not in st.session_state:
    st.session_state.t1_squad = {}
if 't2_squad' not in st.session_state:
    st.session_state.t2_squad = {}
if 'match_log' not in st.session_state:
    st.session_state.match_log = []
if 'commentary' not in st.session_state:
    st.session_state.commentary = [] 
if 'over_runs' not in st.session_state:
    st.session_state.over_runs = 0
if 'over_wickets' not in st.session_state:
    st.session_state.over_wickets = 0
if 'wicket_trigger' not in st.session_state:
    st.session_state.wicket_trigger = False
if 'last_out_position' not in st.session_state:
    st.session_state.last_out_position = None
if 'last_over_bowler' not in st.session_state:
    st.session_state.last_over_bowler = None
if 'innings_1_batting' not in st.session_state:
    st.session_state.innings_1_batting = None

# --- Custom CSS Styling ---
st.markdown(r"""
    <style>
        .block-container {
            padding-top: 1rem !important;
            padding-bottom: 1rem !important;
            padding-left: 0.5rem !important;
            padding-right: 0.5rem !important;
            max-width: 100% !important;
        }
        h1 { font-size: 1.6rem !important; margin-bottom: 0.5rem !important; text-align: center; }
        h3 { font-size: 1.3rem !important; margin: 0px !important; text-align: center; }
        .stMarkdown div p { font-size: 0.95rem !important; margin-bottom: 2px !important; }
        .stCaption { font-size: 0.85rem !important; margin-bottom: 4px !important; line-height: 1.2 !important; }
        
        [data-testid="column"] { padding: 3px !important; }
        [data-testid="stHorizontalBlock"] { gap: 6px !important; }
        
        div.stButton > button {
            padding: 10px 4px !important;
            font-size: 1.1rem !important;
            font-weight: bold !important;
            margin: 0px !important;
            height: 50px !important;
            width: 100% !important;
            border-radius: 8px !important;
        }
        
        div[data-testid="stNumberInput"] input {
            height: 50px !important;
            font-size: 1.05rem !important;
            text-align: center !important;
        }

        .commentary-ball {
            padding: 6px 10px;
            margin-bottom: 4px;
            border-radius: 4px;
            background-color: #f1f3f6;
            border-left: 4px solid #0078ff;
            font-family: monospace;
            font-size: 0.9rem;
        }
        .commentary-over-break {
            padding: 8px 12px;
            margin: 8px 0px;
            border-radius: 6px;
            background-color: #2b3e50;
            color: #ffffff;
            font-weight: bold;
            font-size: 0.95rem;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

st.title("🏏 Professional Live Cricket Scorecard")

def init_player():
    return {
        "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0, "strike_rate": "None",
        "mode_of_dismissal": "not out", "balls_bowled": 0, "wides": 0, "no_balls": 0,
        "runs_given": 0, "wickets": 0, "economy": "None", "fielding_points": 0
    }

def format_overs(balls):
    return f"{balls // 6}.{balls % 6}"

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
            save_match_state()
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
            save_match_state()
            st.rerun()

# --- 3. Toss Info ---
elif st.session_state.step == 'toss':
    st.header("Toss Details")
    with st.form("toss_form"):
        toss_victor = st.radio("Who won the toss?", [st.session_state.team_1, st.session_state.team_2])
        toss_result = st.radio("Opted to:", ["Bat", "Bowl"])
        
        if st.form_submit_button("Select Openers"):
            if (toss_victor == st.session_state.team_1 and toss_result == "Bat") or (toss_victor == st.session_state.team_2 and toss_result == "Bowl"):
                st.session_state.batting_team = st.session_state.team_1
                st.session_state.bowling_team = st.session_state.team_2
                st.session_state.bat_squad = st.session_state.t1_squad
                st.session_state.bowl_squad = st.session_state.t2_squad
                st.session_state.max_wickets = st.session_state.num_players_1 - 1
                st.session_state.innings_1_batting = st.session_state.team_1
            else:
                st.session_state.batting_team = st.session_state.team_2
                st.session_state.bowling_team = st.session_state.team_1
                st.session_state.bat_squad = st.session_state.t2_squad
                st.session_state.bowl_squad = st.session_state.t1_squad
                st.session_state.max_wickets = st.session_state.num_players_2 - 1
                st.session_state.innings_1_batting = st.session_state.team_2
            
            st.session_state.score = 0
            st.session_state.wickets = 0
            st.session_state.balls_bowled = 0
            st.session_state.innings = 1
            st.session_state.last_over_bowler = None
            st.session_state.step = 'openers'
            save_match_state()
            st.rerun()

# --- 3.5 Opening Batter Selection Flow ---
elif st.session_state.step == 'openers':
    st.header("Select Opening Batters")
    batters_list = list(st.session_state.bat_squad.keys())
    bowlers_list = list(st.session_state.bowl_squad.keys())
    
    with st.form("openers_form"):
        str_choice = st.selectbox("Select Opening Striker (*):", batters_list, index=0)
        nstr_choice = st.selectbox("Select Opening Non-Striker:", batters_list, index=1 if len(batters_list) > 1 else 0)
        bowl_choice = st.selectbox("Select First Over Bowler:", bowlers_list, index=0)
        
        if st.form_submit_button("Start Live Scoring"):
            if str_choice == nstr_choice:
                st.error("Striker and Non-Striker cannot be the same player!")
            else:
                st.session_state.striker = str_choice
                st.session_state.non_striker = nstr_choice
                st.session_state.current_bowler = bowl_choice
                st.session_state.step = 'live_match'
                save_match_state()
                st.rerun()

# --- 4. Live Match Dashboard ---
elif st.session_state.step == 'live_match':
    overs = st.session_state.balls_bowled // 6
    rem_balls = st.session_state.balls_bowled % 6
    is_all_out = st.session_state.wickets >= st.session_state.max_wickets
    available_batters = [k for k, v in st.session_state.bat_squad.items() if v["mode_of_dismissal"] == "not out" and k != st.session_state.striker and k != st.session_state.non_striker]
    fielding_team_list = list(st.session_state.bowl_squad.keys())
    
    ov_str = f"{overs}.{rem_balls}"
    st.markdown(f"### **{st.session_state.batting_team}**: `{st.session_state.score}/{st.session_state.wickets}` ({ov_str} Ov)")
    
    s_p = st.session_state.bat_squad[st.session_state.striker]
    ns_p = st.session_state.bat_squad[st.session_state.non_striker]
    b_p = st.session_state.bowl_squad[st.session_state.current_bowler]
    
    st.caption(f"🏏 **{st.session_state.striker}***: {s_p['runs']}({s_p['balls_faced']}) | {st.session_state.non_striker}: {ns_p['runs']}({ns_p['balls_faced']})")
    st.caption(f"🥎 **{st.session_state.current_bowler}**: {b_p['wickets']}-{b_p['runs_given'] + b_p['wides'] + b_p['no_balls']} ({format_overs(b_p['balls_bowled'])} Ov)")

    tab_scoring, tab_commentary, tab_scorecards, tab_mvp = st.tabs([
        "⚡ Live Scoring Control", 
        "💬 Ball-by-Ball Commentary", 
        "📋 Full Match Scorecard", 
        "🏆 MVP Leaderboard"
    ])

    def recalculate_metrics():
        for b in st.session_state.bat_squad:
            faced = st.session_state.bat_squad[b]["balls_faced"]
            if faced > 0:
                st.session_state.bat_squad[b]["strike_rate"] = round((st.session_state.bat_squad[b]["runs"] / faced) * 100, 1)
        for bowl in [st.session_state.t1_squad, st.session_state.t2_squad]:
            for p in bowl:
                b_bowled = bowl[p]["balls_bowled"]
                if b_bowled > 0:
                    total_runs_given = bowl[p]["runs_given"] + bowl[p]["wides"] + bowl[p]["no_balls"]
                    bowl[p]["economy"] = round((total_runs_given / b_bowled) * 6, 2)

    def handle_strike_rotation(runs):
        if runs % 2 != 0:
            st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker

    def check_over_completion():
        if st.session_state.balls_bowled % 6 == 0 and st.session_state.balls_bowled > 0:
            current_over_num = st.session_state.balls_bowled // 6
            summary_string = f"🛑 End of Over {current_over_num} | Runs conceded: {st.session_state.over_runs} | Wickets: {st.session_state.over_wickets}"
            st.session_state.commentary.append({"type": "over_break", "text": summary_string})
            st.session_state.over_runs = 0
            st.session_state.over_wickets = 0
            st.session_state.last_over_bowler = st.session_state.current_bowler
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
        st.session_state.over_runs += runs
        
        c_ov = format_overs(st.session_state.balls_bowled)
        desc = f"{c_ov} | {st.session_state.current_bowler} to {st.session_state.striker}: {runs} run(s)"
        st.session_state.commentary.append({"type": "ball", "text": desc})
        st.session_state.match_log.append(str(runs))
        
        handle_strike_rotation(runs)
        check_over_completion()
        recalculate_metrics()
        save_match_state()
        st.rerun()

    # --- TAB 1: SCORING CONTROLS ---
    with tab_scoring:
        max_bowler_overs = math.ceil(st.session_state.over_limit / 5)
        is_bowler_exhausted = b_p["balls_bowled"] >= (max_bowler_overs * 6)
        is_bowler_consecutive = (rem_balls == 0 and st.session_state.balls_bowled > 0 and st.session_state.current_bowler == st.session_state.last_over_bowler)
        
        if is_bowler_consecutive:
            st.error(f"⚠️ {st.session_state.current_bowler} cannot bowl consecutive overs! Change bowler below.")
        elif is_bowler_exhausted:
            st.error(f"⚠️ {st.session_state.current_bowler} reached limit ({max_bowler_overs} overs)!")

        disable_scoring = is_all_out or is_bowler_exhausted or is_bowler_consecutive

        if st.session_state.wicket_trigger and not is_all_out:
            st.error("💥 Wicket Down! Choose Incoming Batter")
            with st.form("new_batter_form"):
                incoming_choice = st.selectbox("New Batter:", available_batters)
                if st.form_submit_button("Bring Batter onto Field"):
                    if st.session_state.last_out_position == 'striker':
                        st.session_state.striker = incoming_choice
                    else:
                        st.session_state.non_striker = incoming_choice
                    st.session_state.wicket_trigger = False
                    st.session_state.last_out_position = None
                    
                    check_over_completion()
                    recalculate_metrics()
                    save_match_state()
                    st.rerun()
        else:
            r1_c1, r1_c2, r1_c3 = st.columns(3)
            r2_c1, r2_c2, r2_c3 = st.columns(3)
            r3_c1, r3_c2, r3_c3 = st.columns(3)
            
            with r1_c1: 
                if st.button("0", disabled=disable_scoring, use_container_width=True): score_normal_delivery(0)
            with r1_c2: 
                if st.button("1", disabled=disable_scoring, use_container_width=True): score_normal_delivery(1)
            with r1_c3: 
                if st.button("2", disabled=disable_scoring, use_container_width=True): score_normal_delivery(2)
                
            with r2_c1: 
                if st.button("3", disabled=disable_scoring, use_container_width=True): score_normal_delivery(3)
            with r2_c2: 
                if st.button("4", disabled=disable_scoring, use_container_width=True): score_normal_delivery(4)
            with r2_c3: 
                if st.button("6", disabled=disable_scoring, use_container_width=True): score_normal_delivery(6)

            with r3_c1:
                uncommon_val = st.number_input("Odd", min_value=0, max_value=10, value=5, step=1, label_visibility="collapsed")
            with r3_c2:
                if st.button(f"+{uncommon_val}", disabled=disable_scoring, use_container_width=True): score_normal_delivery(uncommon_val)
            with r3_c3:
                bowlers_list = list(st.session_state.bowl_squad.keys())
                chosen_bowler = st.selectbox("Bowler", bowlers_list, index=bowlers_list.index(st.session_state.current_bowler), label_visibility="collapsed")
                if chosen_bowler != st.session_state.current_bowler:
                    st.session_state.current_bowler = chosen_bowler
                    save_match_state()
                    st.rerun()

            with st.expander("➕ Extras (Wd / Nb / Byes)"):
                ex_type = st.selectbox("Select Extra Type", ["Wide", "No Ball", "Leg Byes", "Byes"])
                ex_runs = st.number_input("Additional Runs:", min_value=0, max_value=10, value=0, step=1)
                nb_scoring_mode = st.radio("Scoring Method (NB):", ["Bat", "Byes/None"], horizontal=True)
                
                if st.button("Submit Extra Delivery", disabled=disable_scoring, use_container_width=True, type="primary"):
                    c_ov = format_overs(st.session_state.balls_bowled)
                    if ex_type == "Wide":
                        st.session_state.bowl_squad[st.session_state.current_bowler]["wides"] += (ex_runs + 1)
                        st.session_state.score += (ex_runs + 1)
                        st.session_state.over_runs += (ex_runs + 1)
                        st.session_state.commentary.append({"type": "ball", "text": f"{c_ov} | {st.session_state.current_bowler}: WIDE (+{ex_runs + 1} runs)"})
                        handle_strike_rotation(ex_runs)
                    elif ex_type == "No Ball":
                        if nb_scoring_mode == "Bat":
                            st.session_state.bat_squad[st.session_state.striker]["runs"] += ex_runs
                            st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += (ex_runs + 1)
                            st.session_state.score += (ex_runs + 1)
                        else:
                            st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += 1
                            st.session_state.score += (ex_runs + 1)
                        st.session_state.over_runs += (ex_runs + 1)
                        st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                        st.session_state.commentary.append({"type": "ball", "text": f"{c_ov} | {st.session_state.current_bowler}: NO BALL (+{ex_runs + 1} runs)"})
                        handle_strike_rotation(ex_runs)
                    elif ex_type in ["Leg Byes", "Byes"]:
                        st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                        st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                        st.session_state.score += ex_runs
                        st.session_state.over_runs += ex_runs
                        st.session_state.balls_bowled += 1
                        st.session_state.commentary.append({"type": "ball", "text": f"{format_overs(st.session_state.balls_bowled)} | {st.session_state.current_bowler}: Extra ({ex_type}) +{ex_runs} runs"})
                        handle_strike_rotation(ex_runs)
                        check_over_completion()
                    recalculate_metrics()
                    save_match_state()
                    st.rerun()

            with st.expander("💥 Dismissals / Wickets"):
                w_mode = st.selectbox("Method of Dismissal", ["Bowled", "Caught", "LBW", "Stumped", "Run Out", "Hit Wicket", "Mankad"])
                delivery_context = st.radio("Context", ["Normal", "Wide", "No Ball"], horizontal=True)
                
                target_batter = st.session_state.striker
                if w_mode == "Run Out":
                    target_batter = st.selectbox("Batter Run Out", [st.session_state.striker, st.session_state.non_striker])
                    is_direct = st.radio("Was it a Direct Hit?", ["Yes", "No"], horizontal=True)
                    if is_direct == "Yes":
                        fielder_direct = st.selectbox("Select Fielder (Direct Hit):", fielding_team_list)
                    else:
                        c1, c2 = st.columns(2)
                        with c1: thrower = st.selectbox("Select Thrower:", fielding_team_list)
                        with c2: collector = st.selectbox("Select Collector:", fielding_team_list)
                    ro_runs = st.number_input("Runs Completed Before Run Out:", min_value=0, max_value=6, value=0)
                elif w_mode in ["Caught", "Stumped", "Mankad"]:
                    fielder_involved = st.selectbox("Select Fielder Responsible:", fielding_team_list)
                    if w_mode == "Mankad":
                        target_batter = st.session_state.non_striker

                if st.button("Confirm Wicket Event", type="primary", use_container_width=True, disabled=disable_scoring):
                    current_bowler_name = st.session_state.current_bowler
                    st.session_state.over_wickets += 1
                    
                    if w_mode == "Run Out":
                        if is_direct == "Yes":
                            st.session_state.bowl_squad[fielder_direct]["fielding_points"] += 8
                            label = f"runout ({fielder_direct})"
                        else:
                            st.session_state.bowl_squad[thrower]["fielding_points"] += 5
                            st.session_state.bowl_squad[collector]["fielding_points"] += 3
                            label = f"runout ({thrower})/({collector})"
                        
                        st.session_state.bat_squad[target_batter]["mode_of_dismissal"] = label
                        st.session_state.wickets += 1
                        
                        if delivery_context == "Wide":
                            st.session_state.bowl_squad[current_bowler_name]["wides"] += (ro_runs + 1)
                            st.session_state.score += (ro_runs + 1)
                            st.session_state.over_runs += (ro_runs + 1)
                        elif delivery_context == "No Ball":
                            st.session_state.bowl_squad[current_bowler_name]["no_balls"] += (ro_runs + 1)
                            st.session_state.score += (ro_runs + 1)
                            st.session_state.over_runs += (ro_runs + 1)
                            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                        else:
                            st.session_state.bowl_squad[current_bowler_name]["balls_bowled"] += 1
                            st.session_state.bowl_squad[current_bowler_name]["runs_given"] += ro_runs
                            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                            st.session_state.score += ro_runs
                            st.session_state.over_runs += ro_runs
                            st.session_state.balls_bowled += 1
                        
                        st.session_state.commentary.append({"type": "ball", "text": f"{format_overs(st.session_state.balls_bowled)} | OUT! Run Out: {target_batter} dismissed."})
                        st.session_state.last_out_position = 'striker' if target_batter == st.session_state.striker else 'non_striker'
                        st.session_state.wicket_trigger = True
                        
                        if delivery_context not in ["Wide", "No Ball"] and is_all_out:
                            check_over_completion()
                    else:
                        if w_mode == "Bowled": label = f"b ({current_bowler_name})"
                        elif w_mode == "LBW": label = f"lbw b ({current_bowler_name})"
                        elif w_mode == "Caught":
                            label = f"c ({fielder_involved}) b ({current_bowler_name})"
                            st.session_state.bowl_squad[fielder_involved]["fielding_points"] += 8
                        elif w_mode == "Stumped":
                            label = f"st ({fielder_involved}) b ({current_bowler_name})"
                            st.session_state.bowl_squad[fielder_involved]["fielding_points"] += 8
                        elif w_mode == "Mankad":
                            label = f"mankad ({fielder_involved})"
                            st.session_state.bowl_squad[fielder_involved]["fielding_points"] += 8
                        
                        st.session_state.bat_squad[target_batter]["mode_of_dismissal"] = label
                        if w_mode != "Mankad":
                            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                            st.session_state.bowl_squad[current_bowler_name]["balls_bowled"] += 1
                            st.session_state.bowl_squad[current_bowler_name]["wickets"] += 1
                            st.session_state.balls_bowled += 1
                        
                        st.session_state.wickets += 1
                        st.session_state.commentary.append({"type": "ball", "text": f"{format_overs(st.session_state.balls_bowled)} | OUT! {target_batter} dismissed via {w_mode}."})
                        st.session_state.last_out_position = 'non_striker' if w_mode == "Mankad" else 'striker'
                        st.session_state.wicket_trigger = True
                        
                        if w_mode != "Mankad" and is_all_out:
                            check_over_completion()
                        
                    recalculate_metrics()
                    save_match_state()
                    st.rerun()

            with st.expander("🔄 Setup Lineup Overrides"):
                all_active = [k for k, v in st.session_state.bat_squad.items() if v["mode_of_dismissal"] == "not out"]
                st.session_state.striker = st.selectbox("Striker Override", all_active, index=all_active.index(st.session_state.striker))
                st.session_state.non_striker = st.selectbox("Non-Striker Override", all_active, index=all_active.index(st.session_state.non_striker))

    # --- TAB 2: ESPN COMMENTARY LOG ---
    with tab_commentary:
        st.subheader("📋 Ball-by-Ball Timeline")
        if not st.session_state.commentary:
            st.write("_No deliveries bowled yet._")
        else:
            for entry in reversed(st.session_state.commentary):
                if entry["type"] == "ball":
                    st.markdown(f'<div class="commentary-ball">      {entry["text"]}</div>', unsafe_allow_html=True)
                elif entry["type"] == "over_break":
                    st.markdown(f'<div class="commentary-over-break">{entry["text"]}</div>', unsafe_allow_html=True)

    # --- TAB 3: MATCH SCORECARDS SEPARATED BY INNINGS ---
    with tab_scorecards:
        def generate_active_bowl_df(squad_dict):
            df = pd.DataFrame.from_dict(squad_dict, orient='index').copy()
            if not df.empty:
                df['Overs'] = df['balls_bowled'].apply(format_overs)
                active_df = df[(df['balls_bowled'] > 0) | (df['wides'] > 0) | (df['no_balls'] > 0)]
                if not active_df.empty:
                    return active_df[["Overs", "wides", "no_balls", "runs_given", "wickets", "economy"]]
            return pd.DataFrame(columns=["Overs", "wides", "no_balls", "runs_given", "wickets", "economy"])

        if st.session_state.innings_1_batting == st.session_state.team_1:
            inn1_bat, inn1_bowl = st.session_state.t1_squad, st.session_state.t2_squad
            inn1_bat_name, inn1_bowl_name = st.session_state.team_1, st.session_state.team_2
            inn2_bat, inn2_bowl = st.session_state.t2_squad, st.session_state.t1_squad
            inn2_bat_name, inn2_bowl_name = st.session_state.team_2, st.session_state.team_1
        else:
            inn1_bat, inn1_bowl = st.session_state.t2_squad, st.session_state.t1_squad
            inn1_bat_name, inn1_bowl_name = st.session_state.team_2, st.session_state.team_1
            inn2_bat, inn2_bowl = st.session_state.t1_squad, st.session_state.t2_squad
            inn2_bat_name, inn2_bowl_name = st.session_state.team_1, st.session_state.team_2

        st.subheader(f"1️⃣ First Innings: {inn1_bat_name} vs {inn1_bowl_name}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Batting: {inn1_bat_name}**")
            df_inn1_bat = pd.DataFrame.from_dict(inn1_bat, orient='index')
            st.dataframe(df_inn1_bat[["runs", "balls_faced", "fours", "sixes", "strike_rate", "mode_of_dismissal"]] if not df_inn1_bat.empty else df_inn1_bat, use_container_width=True)
        with c2:
            st.markdown(f"**Bowling: {inn1_bowl_name}**")
            st.dataframe(generate_active_bowl_df(inn1_bowl), use_container_width=True)

        st.write("---")
        st.subheader(f"2️⃣ Second Innings: {inn2_bat_name} vs {inn2_bowl_name}")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f"**Batting: {inn2_bat_name}**")
            df_inn2_bat = pd.DataFrame.from_dict(inn2_bat, orient='index')
            st.dataframe(df_inn2_bat[["runs", "balls_faced", "fours", "sixes", "strike_rate", "mode_of_dismissal"]] if not df_inn2_bat.empty else df_inn2_bat, use_container_width=True)
        with c4:
            st.markdown(f"**Bowling: {inn2_bowl_name}**")
            st.dataframe(generate_active_bowl_df(inn2_bowl), use_container_width=True)

    # --- TAB 4: MVP LEADERBOARD ---
    with tab_mvp:
        mvp_records = {}
        for team_squad in [st.session_state.t1_squad, st.session_state.t2_squad]:
            for player, stats in team_squad.items():
                runs = stats.get("runs", 0)
                wickets = stats.get("wickets", 0)
                f_pts = stats.get("fielding_points", 0)
                total_points = (runs * 1) + (wickets * 20) + f_pts
                mvp_records[player] = {
                    "Runs": runs,
                    "Wickets": wickets,
                    "Fielding Pts": f_pts,
                    "Total MVP Points": total_points
                }
        df_mvp = pd.DataFrame.from_dict(mvp_records, orient='index').sort_values(by="Total MVP Points", ascending=False)
        st.dataframe(df_mvp, use_container_width=True)

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
                st.session_state.match_log = []
                st.session_state.commentary = []
                st.session_state.wicket_trigger = False
                st.session_state.last_over_bowler = None
                
                st.session_state.step = 'openers'
                save_match_state()
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
                clear_backup()
                st.session_state.clear()
                st.rerun()
            font-size: 1rem !important;
            text-align: center !important;
        }

        .streamlit-expanderHeader { padding: 6px 10px !important; font-size: 0.9rem !important; }
        .streamlit-expanderContent { padding: 8px !important; }
        div[data-testid="stDataFrame"] { font-size: 0.8rem !important; }

        .commentary-ball {
            padding: 6px 10px;
            margin-bottom: 4px;
            border-radius: 4px;
            background-color: #f1f3f6;
            border-left: 4px solid #0078ff;
            font-family: monospace;
            font-size: 0.9rem;
        }
        .commentary-over-break {
            padding: 8px 12px;
            margin: 8px 0px;
            border-radius: 6px;
            background-color: #2b3e50;
            color: #ffffff;
            font-weight: bold;
            font-size: 0.95rem;
            text-align: center;
        }
    </style>
""", unsafe_allow_html=True)

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
if 'commentary' not in st.session_state:
    st.session_state.commentary = [] 
if 'over_runs' not in st.session_state:
    st.session_state.over_runs = 0
if 'over_wickets' not in st.session_state:
    st.session_state.over_wickets = 0
if 'wicket_trigger' not in st.session_state:
    st.session_state.wicket_trigger = False
if 'last_out_position' not in st.session_state:
    st.session_state.last_out_position = None
if 'last_over_bowler' not in st.session_state:
    st.session_state.last_over_bowler = None
if 'innings_1_batting' not in st.session_state:
    st.session_state.innings_1_batting = None

def init_player():
    return {
        "runs": 0, "balls_faced": 0, "fours": 0, "sixes": 0, "strike_rate": "None",
        "mode_of_dismissal": "not out", "balls_bowled": 0, "wides": 0, "no_balls": 0,
        "runs_given": 0, "wickets": 0, "economy": "None", "fielding_points": 0
    }

def format_overs(balls):
    return f"{balls // 6}.{balls % 6}"

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
        
        if st.form_submit_button("Select Openers"):
            if (toss_victor == st.session_state.team_1 and toss_result == "Bat") or (toss_victor == st.session_state.team_2 and toss_result == "Bowl"):
                st.session_state.batting_team = st.session_state.team_1
                st.session_state.bowling_team = st.session_state.team_2
                st.session_state.bat_squad = st.session_state.t1_squad
                st.session_state.bowl_squad = st.session_state.t2_squad
                st.session_state.max_wickets = st.session_state.num_players_1 - 1
                st.session_state.innings_1_batting = st.session_state.team_1
            else:
                st.session_state.batting_team = st.session_state.team_2
                st.session_state.bowling_team = st.session_state.team_1
                st.session_state.bat_squad = st.session_state.t2_squad
                st.session_state.bowl_squad = st.session_state.t1_squad
                st.session_state.max_wickets = st.session_state.num_players_2 - 1
                st.session_state.innings_1_batting = st.session_state.team_2
            
            st.session_state.score = 0
            st.session_state.wickets = 0
            st.session_state.balls_bowled = 0
            st.session_state.innings = 1
            st.session_state.last_over_bowler = None
            st.session_state.step = 'openers'
            st.rerun()

# --- 3.5 Opening Batter Selection Flow ---
elif st.session_state.step == 'openers':
    st.header("Select Opening Batters")
    batters_list = list(st.session_state.bat_squad.keys())
    bowlers_list = list(st.session_state.bowl_squad.keys())
    
    with st.form("openers_form"):
        str_choice = st.selectbox("Select Opening Striker (*):", batters_list, index=0)
        nstr_choice = st.selectbox("Select Opening Non-Striker:", batters_list, index=1 if len(batters_list) > 1 else 0)
        bowl_choice = st.selectbox("Select First Over Bowler:", bowlers_list, index=0)
        
        if st.form_submit_button("Start Live Scoring"):
            if str_choice == nstr_choice:
                st.error("Striker and Non-Striker cannot be the same player!")
            else:
                st.session_state.striker = str_choice
                st.session_state.non_striker = nstr_choice
                st.session_state.current_bowler = bowl_choice
                st.session_state.step = 'live_match'
                st.rerun()

# --- 4. Live Match Interface ---
elif st.session_state.step == 'live_match':
    overs = st.session_state.balls_bowled // 6
    rem_balls = st.session_state.balls_bowled % 6
    is_all_out = st.session_state.wickets >= st.session_state.max_wickets
    available_batters = [k for k, v in st.session_state.bat_squad.items() if v["mode_of_dismissal"] == "not out" and k != st.session_state.striker and k != st.session_state.non_striker]
    fielding_team_list = list(st.session_state.bowl_squad.keys())
    
    ov_str = f"{overs}.{rem_balls}"
    st.markdown(f"### **{st.session_state.batting_team}**: `{st.session_state.score}/{st.session_state.wickets}` ({ov_str} Ov)")
    
    s_p = st.session_state.bat_squad[st.session_state.striker]
    ns_p = st.session_state.bat_squad[st.session_state.non_striker]
    b_p = st.session_state.bowl_squad[st.session_state.current_bowler]
    
    st.caption(f"🏏 **{st.session_state.striker}***: {s_p['runs']}({s_p['balls_faced']}) | {st.session_state.non_striker}: {ns_p['runs']}({ns_p['balls_faced']})")
    st.caption(f"🥎 **{st.session_state.current_bowler}**: {b_p['wickets']}-{b_p['runs_given'] + b_p['wides'] + b_p['no_balls']} ({format_overs(b_p['balls_bowled'])} Ov)")

    tab_scoring, tab_commentary, tab_scorecards, tab_mvp = st.tabs([
        "⚡ Live Scoring Control", 
        "💬 Ball-by-Ball Commentary", 
        "📋 Full Match Scorecard", 
        "🏆 MVP Leaderboard"
    ])

    def recalculate_metrics():
        for b in st.session_state.bat_squad:
            faced = st.session_state.bat_squad[b]["balls_faced"]
            if faced > 0:
                st.session_state.bat_squad[b]["strike_rate"] = round((st.session_state.bat_squad[b]["runs"] / faced) * 100, 1)
        for bowl in [st.session_state.t1_squad, st.session_state.t2_squad]:
            for p in bowl:
                b_bowled = bowl[p]["balls_bowled"]
                if b_bowled > 0:
                    total_runs_given = bowl[p]["runs_given"] + bowl[p]["wides"] + bowl[p]["no_balls"]
                    bowl[p]["economy"] = round((total_runs_given / b_bowled) * 6, 2)

    def handle_strike_rotation(runs):
        if runs % 2 != 0:
            st.session_state.striker, st.session_state.non_striker = st.session_state.non_striker, st.session_state.striker

    def check_over_completion():
        if st.session_state.balls_bowled % 6 == 0 and st.session_state.balls_bowled > 0:
            current_over_num = st.session_state.balls_bowled // 6
            summary_string = f"🛑 End of Over {current_over_num} | Runs conceded: {st.session_state.over_runs} | Wickets: {st.session_state.over_wickets}"
            st.session_state.commentary.append({"type": "over_break", "text": summary_string})
            st.session_state.over_runs = 0
            st.session_state.over_wickets = 0
            st.session_state.last_over_bowler = st.session_state.current_bowler
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
        st.session_state.over_runs += runs
        
        c_ov = format_overs(st.session_state.balls_bowled)
        desc = f"{c_ov} | {st.session_state.current_bowler} to {st.session_state.striker}: {runs} run(s)"
        st.session_state.commentary.append({"type": "ball", "text": desc})
        st.session_state.match_log.append(str(runs))
        
        handle_strike_rotation(runs)
        check_over_completion()
        recalculate_metrics()
        st.rerun()

    # --- TAB 1: SCORING CONTROLS ---
    with tab_scoring:
        max_bowler_overs = math.ceil(st.session_state.over_limit / 5)
        is_bowler_exhausted = b_p["balls_bowled"] >= (max_bowler_overs * 6)
        is_bowler_consecutive = (rem_balls == 0 and st.session_state.balls_bowled > 0 and st.session_state.current_bowler == st.session_state.last_over_bowler)
        
        if is_bowler_consecutive:
            st.error(f"⚠️ {st.session_state.current_bowler} cannot bowl consecutive overs! Change bowler below.")
        elif is_bowler_exhausted:
            st.error(f"⚠️ {st.session_state.current_bowler} reached limit ({max_bowler_overs} overs)!")

        disable_scoring = is_all_out or is_bowler_exhausted or is_bowler_consecutive

        if st.session_state.wicket_trigger and not is_all_out:
            st.error("💥 Wicket Down! Choose Incoming Batter")
            with st.form("new_batter_form"):
                incoming_choice = st.selectbox("New Batter:", available_batters)
                if st.form_submit_button("Bring Batter onto Field"):
                    if st.session_state.last_out_position == 'striker':
                        st.session_state.striker = incoming_choice
                    else:
                        st.session_state.non_striker = incoming_choice
                    st.session_state.wicket_trigger = False
                    st.session_state.last_out_position = None
                    
                    # Check over completion safely here AFTER the new batter is settled
                    check_over_completion()
                    recalculate_metrics()
                    st.rerun()
        else:
            r1_c1, r1_c2, r1_c3 = st.columns(3)
            r2_c1, r2_c2, r2_c3 = st.columns(3)
            r3_c1, r3_c2, r3_c3 = st.columns(3)
            
            with r1_c1: 
                if st.button("0", disabled=disable_scoring, use_container_width=True): score_normal_delivery(0)
            with r1_c2: 
                if st.button("1", disabled=disable_scoring, use_container_width=True): score_normal_delivery(1)
            with r1_c3: 
                if st.button("2", disabled=disable_scoring, use_container_width=True): score_normal_delivery(2)
                
            with r2_c1: 
                if st.button("3", disabled=disable_scoring, use_container_width=True): score_normal_delivery(3)
            with r2_c2: 
                if st.button("4", disabled=disable_scoring, use_container_width=True): score_normal_delivery(4)
            with r2_c3: 
                if st.button("6", disabled=disable_scoring, use_container_width=True): score_normal_delivery(6)

            with r3_c1:
                uncommon_val = st.number_input("Odd", min_value=0, max_value=10, value=5, step=1, label_visibility="collapsed")
            with r3_c2:
                if st.button(f"+{uncommon_val}", disabled=disable_scoring, use_container_width=True): score_normal_delivery(uncommon_val)
            with r3_c3:
                bowlers_list = list(st.session_state.bowl_squad.keys())
                chosen_bowler = st.selectbox("Bowler", bowlers_list, index=bowlers_list.index(st.session_state.current_bowler), label_visibility="collapsed")
                if chosen_bowler != st.session_state.current_bowler:
                    st.session_state.current_bowler = chosen_bowler
                    st.rerun()

            with st.expander("➕ Extras (Wd / Nb / Byes)"):
                ex_type = st.selectbox("Select Extra Type", ["Wide", "No Ball", "Leg Byes", "Byes"])
                ex_runs = st.number_input("Additional Runs:", min_value=0, max_value=10, value=0, step=1)
                nb_scoring_mode = st.radio("Scoring Method (NB):", ["Bat", "Byes/None"], horizontal=True)
                
                if st.button("Submit Extra Delivery", disabled=disable_scoring, use_container_width=True, type="primary"):
                    c_ov = format_overs(st.session_state.balls_bowled)
                    if ex_type == "Wide":
                        st.session_state.bowl_squad[st.session_state.current_bowler]["wides"] += (ex_runs + 1)
                        st.session_state.score += (ex_runs + 1)
                        st.session_state.over_runs += (ex_runs + 1)
                        st.session_state.commentary.append({"type": "ball", "text": f"{c_ov} | {st.session_state.current_bowler}: WIDE (+{ex_runs + 1} runs)"})
                        handle_strike_rotation(ex_runs)
                    elif ex_type == "No Ball":
                        if nb_scoring_mode == "Bat":
                            st.session_state.bat_squad[st.session_state.striker]["runs"] += ex_runs
                            st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += (ex_runs + 1)
                            st.session_state.score += (ex_runs + 1)
                        else:
                            st.session_state.bowl_squad[st.session_state.current_bowler]["no_balls"] += 1
                            st.session_state.score += (ex_runs + 1)
                        st.session_state.over_runs += (ex_runs + 1)
                        st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                        st.session_state.commentary.append({"type": "ball", "text": f"{c_ov} | {st.session_state.current_bowler}: NO BALL (+{ex_runs + 1} runs)"})
                        handle_strike_rotation(ex_runs)
                    elif ex_type in ["Leg Byes", "Byes"]:
                        st.session_state.bowl_squad[st.session_state.current_bowler]["balls_bowled"] += 1
                        st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                        st.session_state.score += ex_runs
                        st.session_state.over_runs += ex_runs
                        st.session_state.balls_bowled += 1
                        st.session_state.commentary.append({"type": "ball", "text": f"{format_overs(st.session_state.balls_bowled)} | {st.session_state.current_bowler}: Extra ({ex_type}) +{ex_runs} runs"})
                        handle_strike_rotation(ex_runs)
                        check_over_completion()
                    recalculate_metrics()
                    st.rerun()

            with st.expander("💥 Dismissals / Wickets"):
                w_mode = st.selectbox("Method of Dismissal", ["Bowled", "Caught", "LBW", "Stumped", "Run Out", "Hit Wicket", "Mankad"])
                delivery_context = st.radio("Context", ["Normal", "Wide", "No Ball"], horizontal=True)
                
                target_batter = st.session_state.striker
                if w_mode == "Run Out":
                    target_batter = st.selectbox("Batter Run Out", [st.session_state.striker, st.session_state.non_striker])
                    is_direct = st.radio("Was it a Direct Hit?", ["Yes", "No"], horizontal=True)
                    if is_direct == "Yes":
                        fielder_direct = st.selectbox("Select Fielder (Direct Hit):", fielding_team_list)
                    else:
                        c1, c2 = st.columns(2)
                        with c1: thrower = st.selectbox("Select Thrower:", fielding_team_list)
                        with c2: collector = st.selectbox("Select Collector:", fielding_team_list)
                    ro_runs = st.number_input("Runs Completed Before Run Out:", min_value=0, max_value=6, value=0)
                elif w_mode in ["Caught", "Stumped", "Mankad"]:
                    fielder_involved = st.selectbox("Select Fielder Responsible:", fielding_team_list)
                    if w_mode == "Mankad":
                        target_batter = st.session_state.non_striker

                if st.button("Confirm Wicket Event", type="primary", use_container_width=True, disabled=disable_scoring):
                    current_bowler_name = st.session_state.current_bowler
                    st.session_state.over_wickets += 1
                    
                    if w_mode == "Run Out":
                        if is_direct == "Yes":
                            st.session_state.bowl_squad[fielder_direct]["fielding_points"] += 8
                            label = f"runout ({fielder_direct})"
                        else:
                            st.session_state.bowl_squad[thrower]["fielding_points"] += 5
                            st.session_state.bowl_squad[collector]["fielding_points"] += 3
                            label = f"runout ({thrower})/({collector})"
                        
                        st.session_state.bat_squad[target_batter]["mode_of_dismissal"] = label
                        st.session_state.wickets += 1
                        
                        if delivery_context == "Wide":
                            st.session_state.bowl_squad[current_bowler_name]["wides"] += (ro_runs + 1)
                            st.session_state.score += (ro_runs + 1)
                            st.session_state.over_runs += (ro_runs + 1)
                        elif delivery_context == "No Ball":
                            st.session_state.bowl_squad[current_bowler_name]["no_balls"] += (ro_runs + 1)
                            st.session_state.score += (ro_runs + 1)
                            st.session_state.over_runs += (ro_runs + 1)
                            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                        else:
                            st.session_state.bowl_squad[current_bowler_name]["balls_bowled"] += 1
                            st.session_state.bowl_squad[current_bowler_name]["runs_given"] += ro_runs
                            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                            st.session_state.score += ro_runs
                            st.session_state.over_runs += ro_runs
                            st.session_state.balls_bowled += 1
                        
                        st.session_state.commentary.append({"type": "ball", "text": f"{format_overs(st.session_state.balls_bowled)} | OUT! Run Out: {target_batter} dismissed."})
                        st.session_state.last_out_position = 'striker' if target_batter == st.session_state.striker else 'non_striker'
                        st.session_state.wicket_trigger = True
                        
                        # Delayed checking for over breaks on legal ball run-outs
                        if delivery_context not in ["Wide", "No Ball"] and is_all_out:
                            check_over_completion()
                    else:
                        if w_mode == "Bowled": label = f"b ({current_bowler_name})"
                        elif w_mode == "LBW": label = f"lbw b ({current_bowler_name})"
                        elif w_mode == "Caught":
                            label = f"c ({fielder_involved}) b ({current_bowler_name})"
                            st.session_state.bowl_squad[fielder_involved]["fielding_points"] += 8
                        elif w_mode == "Stumped":
                            label = f"st ({fielder_involved}) b ({current_bowler_name})"
                            st.session_state.bowl_squad[fielder_involved]["fielding_points"] += 8
                        elif w_mode == "Mankad":
                            label = f"mankad ({fielder_involved})"
                            st.session_state.bowl_squad[fielder_involved]["fielding_points"] += 8
                        
                        st.session_state.bat_squad[target_batter]["mode_of_dismissal"] = label
                        if w_mode != "Mankad":
                            st.session_state.bat_squad[st.session_state.striker]["balls_faced"] += 1
                            st.session_state.bowl_squad[current_bowler_name]["balls_bowled"] += 1
                            st.session_state.bowl_squad[current_bowler_name]["wickets"] += 1
                            st.session_state.balls_bowled += 1
                        
                        st.session_state.wickets += 1
                        st.session_state.commentary.append({"type": "ball", "text": f"{format_overs(st.session_state.balls_bowled)} | OUT! {target_batter} dismissed via {w_mode}."})
                        st.session_state.last_out_position = 'non_striker' if w_mode == "Mankad" else 'striker'
                        st.session_state.wicket_trigger = True
                        
                        # Delayed checking for over breaks if the team is completely all out
                        if w_mode != "Mankad" and is_all_out:
                            check_over_completion()
                        
                    recalculate_metrics()
                    st.rerun()

            with st.expander("🔄 Setup Lineup Overrides"):
                all_active = [k for k, v in st.session_state.bat_squad.items() if v["mode_of_dismissal"] == "not out"]
                st.session_state.striker = st.selectbox("Striker Override", all_active, index=all_active.index(st.session_state.striker))
                st.session_state.non_striker = st.selectbox("Non-Striker Override", all_active, index=all_active.index(st.session_state.non_striker))

    # --- TAB 2: ESPN COMMENTARY LOG ---
    with tab_commentary:
        st.subheader("📋 Ball-by-Ball Timeline")
        if not st.session_state.commentary:
            st.write("_No deliveries bowled yet._")
        else:
            for entry in reversed(st.session_state.commentary):
                if entry["type"] == "ball":
                    st.markdown(f'<div class="commentary-ball">🏏 {entry["text"]}</div>', unsafe_allow_html=True)
                elif entry["type"] == "over_break":
                    st.markdown(f'<div class="commentary-over-break">{entry["text"]}</div>', unsafe_allow_html=True)

    # --- TAB 3: MATCH SCORECARDS SEPARATED BY INNINGS ---
    with tab_scorecards:
        def generate_active_bowl_df(squad_dict):
            df = pd.DataFrame.from_dict(squad_dict, orient='index').copy()
            if not df.empty:
                df['Overs'] = df['balls_bowled'].apply(format_overs)
                active_df = df[(df['balls_bowled'] > 0) | (df['wides'] > 0) | (df['no_balls'] > 0)]
                if not active_df.empty:
                    return active_df[["Overs", "wides", "no_balls", "runs_given", "wickets", "economy"]]
            return pd.DataFrame(columns=["Overs", "wides", "no_balls", "runs_given", "wickets", "economy"])

        if st.session_state.innings_1_batting == st.session_state.team_1:
            inn1_bat, inn1_bowl = st.session_state.t1_squad, st.session_state.t2_squad
            inn1_bat_name, inn1_bowl_name = st.session_state.team_1, st.session_state.team_2
            inn2_bat, inn2_bowl = st.session_state.t2_squad, st.session_state.t1_squad
            inn2_bat_name, inn2_bowl_name = st.session_state.team_2, st.session_state.team_1
        else:
            inn1_bat, inn1_bowl = st.session_state.t2_squad, st.session_state.t1_squad
            inn1_bat_name, inn1_bowl_name = st.session_state.team_2, st.session_state.team_1
            inn2_bat, inn2_bowl = st.session_state.t1_squad, st.session_state.t2_squad
            inn2_bat_name, inn2_bowl_name = st.session_state.team_1, st.session_state.team_2

        st.subheader(f"1️⃣ First Innings: {inn1_bat_name} vs {inn1_bowl_name}")
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Batting: {inn1_bat_name}**")
            df_inn1_bat = pd.DataFrame.from_dict(inn1_bat, orient='index')
            st.dataframe(df_inn1_bat[["runs", "balls_faced", "fours", "sixes", "strike_rate", "mode_of_dismissal"]] if not df_inn1_bat.empty else df_inn1_bat, use_container_width=True)
        with c2:
            st.markdown(f"**Bowling: {inn1_bowl_name}**")
            st.dataframe(generate_active_bowl_df(inn1_bowl), use_container_width=True)

        st.write("---")
        st.subheader(f"2️⃣ Second Innings: {inn2_bat_name} vs {inn2_bowl_name}")
        c3, c4 = st.columns(2)
        with c3:
            st.markdown(f"**Batting: {inn2_bat_name}**")
            df_inn2_bat = pd.DataFrame.from_dict(inn2_bat, orient='index')
            st.dataframe(df_inn2_bat[["runs", "balls_faced", "fours", "sixes", "strike_rate", "mode_of_dismissal"]] if not df_inn2_bat.empty else df_inn2_bat, use_container_width=True)
        with c4:
            st.markdown(f"**Bowling: {inn2_bowl_name}**")
            st.dataframe(generate_active_bowl_df(inn2_bowl), use_container_width=True)

    # --- TAB 4: MVP LEADERBOARD ---
    with tab_mvp:
        mvp_records = {}
        for team_squad in [st.session_state.t1_squad, st.session_state.t2_squad]:
            for player, stats in team_squad.items():
                runs = stats.get("runs", 0)
                wickets = stats.get("wickets", 0)
                f_pts = stats.get("fielding_points", 0)
                total_points = (runs * 1) + (wickets * 20) + f_pts
                mvp_records[player] = {
                    "Runs": runs,
                    "Wickets": wickets,
                    "Fielding Pts": f_pts,
                    "Total MVP Points": total_points
                }
        df_mvp = pd.DataFrame.from_dict(mvp_records, orient='index').sort_values(by="Total MVP Points", ascending=False)
        st.dataframe(df_mvp, use_container_width=True)

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
                st.session_state.match_log = []
                st.session_state.commentary = []
                st.session_state.wicket_trigger = False
                st.session_state.last_over_bowler = None
                
                st.session_state.step = 'openers'
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
