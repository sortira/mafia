import streamlit as st
import sqlite3
import uuid
import json
import random
import time

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect("mafia.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS games (
            id TEXT PRIMARY KEY,
            host TEXT,
            players TEXT,
            started INTEGER,
            roles TEXT,
            phase TEXT,
            votes TEXT,
            day_count INTEGER DEFAULT 1,
            night_results TEXT,
            game_over INTEGER DEFAULT 0,
            winner TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_game(game_id, game_data):
    conn = sqlite3.connect("mafia.db")
    c = conn.cursor()
    c.execute("""
        INSERT OR REPLACE INTO games (id, host, players, started, roles, phase, votes, day_count, night_results, game_over, winner)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        game_id,
        game_data["host"],
        json.dumps(game_data["players"]),
        int(game_data["started"]),
        json.dumps(game_data["roles"]),
        game_data["phase"],
        json.dumps(game_data.get("votes", {})),
        game_data.get("day_count", 1),
        json.dumps(game_data.get("night_results", {})),
        int(game_data.get("game_over", False)),
        game_data.get("winner", "")
    ))
    conn.commit()
    conn.close()

def load_game(game_id):
    conn = sqlite3.connect("mafia.db")
    c = conn.cursor()
    c.execute("SELECT host, players, started, roles, phase, votes, day_count, night_results, game_over, winner FROM games WHERE id = ?", (game_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "host": row[0],
        "players": json.loads(row[1]),
        "started": bool(row[2]),
        "roles": json.loads(row[3]),
        "phase": row[4],
        "votes": json.loads(row[5]) if row[5] else {},
        "day_count": row[6] if row[6] else 1,
        "night_results": json.loads(row[7]) if row[7] else {},
        "game_over": bool(row[8]),
        "winner": row[9] if row[9] else ""
    }

def game_exists(game_id):
    conn = sqlite3.connect("mafia.db")
    c = conn.cursor()
    c.execute("SELECT 1 FROM games WHERE id = ?", (game_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def check_win_condition(game):
    """Check if the game has ended and return the winner"""
    alive_players = game["players"]
    roles = game["roles"]
    
    # Count alive mafia and villagers
    alive_mafia = [p for p in alive_players if roles.get(p) == "mafia"]
    alive_villagers = [p for p in alive_players if roles.get(p) in ["villager", "doctor", "detective"]]
    
    if len(alive_mafia) == 0:
        return "villagers"
    elif len(alive_mafia) >= len(alive_villagers):
        return "mafia"
    
    return None

def process_night_actions(game):
    """Process all night actions and return results"""
    votes = game.get("votes", {})
    roles = game["roles"]
    results = {}
    
    # Get mafia kill votes
    mafia_votes = []
    for player, vote in votes.items():
        if roles.get(player) == "mafia" and vote.get("action") == "kill":
            mafia_votes.append(vote["target"])
    
    # Determine kill target (majority vote among mafia)
    kill_target = None
    if mafia_votes:
        kill_target = max(set(mafia_votes), key=mafia_votes.count)
    
    # Get doctor save
    save_target = None
    for player, vote in votes.items():
        if roles.get(player) == "doctor" and vote.get("action") == "save":
            save_target = vote["target"]
            break
    
    # Get detective investigation
    investigate_result = ""
    for player, vote in votes.items():
        if roles.get(player) == "detective" and vote.get("action") == "investigate":
            investigated = vote["target"]
            role_found = roles.get(investigated, "unknown")
            investigate_result = f"{investigated} is a **{role_found.upper()}**"
            break
    
    # Process kill vs save
    if kill_target:
        if kill_target == save_target:
            results["death"] = None
            results["saved"] = save_target
        else:
            results["death"] = kill_target
            # Remove killed player
            if kill_target in game["players"]:
                game["players"].remove(kill_target)
            if kill_target in game["roles"]:
                game["roles"].pop(kill_target)
    
    if investigate_result:
        results["investigation"] = investigate_result
    
    return results

init_db()
st.title("🎭 Mafia Party Game")
st.set_page_config(page_title="Mafia - The Party Game", page_icon="🕵️‍♂️")
st.markdown("Play the popular party game Mafia with your friends online, no need for one of you to sit out as Narrator! Have fun!")
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("Go to", ["Game", "Help", "About"])

if page == "Game":
    if "game_id" not in st.session_state:
        mode = st.radio("Select an option:", ["Create Game", "Join Game"])

        if mode == "Create Game":
            host_name = st.text_input("Enter your name (you will be the host):")
            if st.button("Create Game") and host_name:
                game_id = str(uuid.uuid4())[:6]
                game_data = {
                    "players": [host_name],
                    "host": host_name,
                    "started": False,
                    "roles": {},
                    "phase": "lobby",
                    "votes": {},
                    "day_count": 1,
                    "night_results": {},
                    "game_over": False,
                    "winner": ""
                }
                save_game(game_id, game_data)
                st.session_state.game_id = game_id
                st.session_state.name = host_name
                st.success(f"Game created! Share this Game ID: `{game_id}`")
                st.markdown(f"[📤 Share via WhatsApp](https://wa.me/?text=Join%20my%20Mafia%20game!%20Use%20Game%20ID%3A%20{game_id})", unsafe_allow_html=True)
                st.rerun()

        elif mode == "Join Game":
            join_name = st.text_input("Enter your name:")
            join_id = st.text_input("Enter Game ID:")
            if st.button("Join Game") and join_name and join_id:
                if game_exists(join_id):
                    game = load_game(join_id)
                    if not game["started"] and join_name not in game["players"]:
                        game["players"].append(join_name)
                        save_game(join_id, game)
                        st.session_state.game_id = join_id
                        st.session_state.name = join_name
                        st.success(f"Joined Game {join_id} as {join_name}")
                        st.rerun()
                    elif game["started"]:
                        st.error("Game has already started!")
                    elif join_name in game["players"]:
                        st.session_state.game_id = join_id
                        st.session_state.name = join_name
                        st.success(f"Rejoined Game {join_id} as {join_name}")
                        st.rerun()
                    else:
                        st.error("Cannot join game.")
                else:
                    st.error("Invalid Game ID.")

    # --- GAME UI ---
    if "game_id" in st.session_state:
        game_id = st.session_state.game_id
        name = st.session_state.name
        game = load_game(game_id)

        if not game:
            st.error("Game not found or expired.")
            st.session_state.clear()
            st.stop()

        # Check if player is still alive
        if game["started"] and name not in game["players"]:
            st.error("💀 You have been eliminated from the game!")
            st.write("You can still observe the game:")
            
        st.header(f"You are {name} in Game {game_id} - Day {game.get('day_count', 1)}")
        
        # Show game over screen
        if game.get("game_over", False):
            st.success("🎉 **GAME OVER** 🎉")
            winner = game.get("winner", "")
            if winner == "mafia":
                st.error("🔪 **MAFIA WINS!** The town has been overrun!")
            elif winner == "villagers":
                st.success("🏆 **VILLAGERS WIN!** All mafia have been eliminated!")
            
            st.subheader("Final Results:")
            for player, role in game["roles"].items():
                emoji = "💀" if player not in game["players"] else "✅"
                st.write(f"{emoji} **{player}** - {role.upper()}")
            
            if st.button("🔄 Refresh"):
                st.rerun()
            
            if st.button("🏠 Return to Lobby"):
                st.session_state.clear()
                st.rerun()
            st.stop()

        # Show current players
        st.write("**Players:**")
        for p in game["players"]:
            role_info = ""
            if game["started"] and p == name:
                role_info = f" - **{game['roles'].get(p, 'unknown').upper()}**"
            st.markdown(f"- {p}{role_info}")

        # Show eliminated players
        if game["started"]:
            all_original_players = list(game["roles"].keys())
            eliminated = [p for p in all_original_players if p not in game["players"]]
            if eliminated:
                st.write("**Eliminated:**")
                for p in eliminated:
                    st.markdown(f"- 💀 {p}")

        if st.button("🔄 Refresh"):
            st.rerun()

        # LOBBY PHASE
        if not game["started"]:
            if name == game["host"] and len(game["players"]) >= 4:
                if st.button("Start Game"):
                    players = game["players"][:]
                    random.shuffle(players)
                    roles = {}
                    num_mafia = max(1, len(players) // 3)
                    
                    # Assign roles
                    mafia = players[:num_mafia]
                    remaining = players[num_mafia:]
                    
                    # Ensure we have enough players for special roles
                    doctor = remaining[0] if len(remaining) > 0 else None
                    detective = remaining[1] if len(remaining) > 1 else None
                    
                    for p in players:
                        if p in mafia:
                            roles[p] = "mafia"
                        elif p == doctor:
                            roles[p] = "doctor"
                        elif p == detective:
                            roles[p] = "detective"
                        else:
                            roles[p] = "villager"
                    
                    game["roles"] = roles
                    game["started"] = True
                    game["phase"] = "night"
                    game["day_count"] = 1
                    save_game(game_id, game)
                    st.rerun()
            elif name == game["host"]:
                st.info("Need at least 4 players to start.")
            else:
                st.info("Waiting for host to start the game...")

        # NIGHT PHASE
        elif game["phase"] == "night":
            st.subheader(f"🌙 Night {game.get('day_count', 1)}: Take your action")
            
            # Show night results from previous night
            if game.get("night_results"):
                results = game["night_results"]
                if results.get("death"):
                    st.error(f"💀 **{results['death']}** was killed during the night!")
                elif results.get("saved"):
                    st.success(f"✨ **{results['saved']}** was saved by the Doctor!")
                else:
                    st.info("🌅 Everyone survived the night!")
            
            role = game["roles"].get(name)
            votes = game.get("votes", {})

            # Only allow alive players to vote
            if name in game["players"] and name not in votes:
                if role == "mafia":
                    other_mafia = [p for p in game["players"] if game["roles"].get(p) == "mafia" and p != name]
                    if other_mafia:
                        st.info(f"🤝 Other mafia members: {', '.join(other_mafia)}")
                    else:
                        st.info("🤝 You are the only mafia member.")
                    
                    target = st.selectbox("Choose someone to kill:", [p for p in game["players"] if p != name])
                    if st.button("Submit Kill Vote"):
                        votes[name] = {"action": "kill", "target": target}
                        game["votes"] = votes
                        save_game(game_id, game)
                        st.success("Kill vote submitted!")
                        st.rerun()

                elif role == "doctor":
                    target = st.selectbox("Choose someone to save:", game["players"])
                    if st.button("Submit Save"):
                        votes[name] = {"action": "save", "target": target}
                        game["votes"] = votes
                        save_game(game_id, game)
                        st.success("Save submitted!")
                        st.rerun()

                elif role == "detective":
                    target = st.selectbox("Investigate player:", [p for p in game["players"] if p != name])
                    if st.button("Submit Investigation"):
                        votes[name] = {"action": "investigate", "target": target}
                        game["votes"] = votes
                        save_game(game_id, game)
                        st.success("Investigation submitted!")
                        st.rerun()

                else:
                    st.info("😴 You are a villager. Sleep peacefully and wait for day.")
            
            elif name in votes:
                st.success("✅ You have submitted your night action. Waiting for others...")

            # Check if all required players have voted
            alive_roles = {p: r for p, r in game["roles"].items() if p in game["players"]}
            required_voters = [p for p, r in alive_roles.items() if r in ["mafia", "doctor", "detective"]]
            
            if required_voters and all(p in votes for p in required_voters):
                # Process night actions
                results = process_night_actions(game)
                
                # Check win condition
                winner = check_win_condition(game)
                if winner:
                    game["game_over"] = True
                    game["winner"] = winner
                    save_game(game_id, game)
                    st.rerun()
                
                # Move to day phase
                game["night_results"] = results
                game["votes"] = {}
                game["phase"] = "day"
                save_game(game_id, game)
                st.rerun()

        # DAY PHASE
        elif game["phase"] == "day":
            st.subheader(f"☀️ Day {game.get('day_count', 1)}: Village Discussion & Voting")
            
            # Show last night's results
            if game.get("night_results"):
                results = game["night_results"]
                if results.get("death"):
                    st.error(f"💀 **{results['death']}** was found dead this morning!")
                elif results.get("saved"):
                    st.success(f"✨ Someone was saved by the Doctor last night!")
                else:
                    st.info("🌅 Everyone survived the night!")
                
                # Show investigation result only to detective
                if results.get("investigation") and game["roles"].get(name) == "detective":
                    st.info(f"🕵️ **Detective Report:** {results['investigation']}")
            
            votes = game.get("votes", {})
            
            # Voting section for alive players
            if name in game["players"]:
                if name not in votes:
                    st.write("**Vote to eliminate someone:**")
                    votable_players = [p for p in game["players"] if p != name]
                    
                    if votable_players:
                        target = st.selectbox("Choose someone to eliminate:", [""] + votable_players)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("Vote to Eliminate") and target:
                                votes[name] = {"action": "eliminate", "target": target}
                                game["votes"] = votes
                                save_game(game_id, game)
                                st.success(f"Voted to eliminate {target}!")
                                st.rerun()
                        
                        with col2:
                            if st.button("Skip Vote (No Elimination)"):
                                votes[name] = {"action": "skip", "target": None}
                                game["votes"] = votes
                                save_game(game_id, game)
                                st.success("Voted to skip elimination!")
                                st.rerun()
                    else:
                        st.write("No one to vote for!")
                else:
                    user_vote = votes[name]
                    if user_vote["action"] == "skip":
                        st.success("✅ You voted to skip elimination. Waiting for others...")
                    else:
                        st.success(f"✅ You voted to eliminate {user_vote['target']}. Waiting for others...")
            
            # Show current vote status
            alive_players = game["players"]
            vote_counts = {}
            skip_count = 0
            
            for voter, vote in votes.items():
                if voter in alive_players:  # Only count votes from alive players
                    if vote["action"] == "skip":
                        skip_count += 1
                    else:
                        target = vote["target"]
                        vote_counts[target] = vote_counts.get(target, 0) + 1
            
            st.write("**Current Votes:**")
            for target, count in vote_counts.items():
                st.write(f"- {target}: {count} votes")
            if skip_count > 0:
                st.write(f"- Skip elimination: {skip_count} votes")
            
            voted_players = len([v for v in votes.values() if v])
            st.write(f"**{voted_players}/{len(alive_players)} players have voted**")
            
            # Process votes when everyone has voted
            if voted_players == len(alive_players):
                # Determine elimination target
                if vote_counts:
                    max_votes = max(vote_counts.values())
                    
                    # Check for ties
                    tied_players = [p for p, v in vote_counts.items() if v == max_votes]
                    
                    if len(tied_players) == 1 and max_votes > skip_count:
                        # Clear winner
                        eliminated = tied_players[0]
                        st.error(f"🗳️ **{eliminated}** has been eliminated by majority vote!")
                        
                        # Remove eliminated player
                        if eliminated in game["players"]:
                            game["players"].remove(eliminated)
                        
                        # Reveal their role
                        eliminated_role = game["roles"].get(eliminated, "unknown")
                        st.info(f"💀 **{eliminated}** was a **{eliminated_role.upper()}**")
                        
                    else:
                        # Tie or skip wins
                        st.info("🤝 No elimination today due to tie vote or majority skip!")
                else:
                    st.info("🤝 No elimination today - everyone voted to skip!")
                
                # Check win condition
                winner = check_win_condition(game)
                if winner:
                    game["game_over"] = True
                    game["winner"] = winner
                    save_game(game_id, game)
                    st.rerun()
                
                # Move to next night
                game["votes"] = {}
                game["phase"] = "night"
                game["day_count"] = game.get("day_count", 1) + 1
                game["night_results"] = {}  # Clear previous night results
                save_game(game_id, game)
                
                st.info("🌙 Moving to night phase...")
                time.sleep(2)  # Brief pause before refresh
                st.rerun()

        # Reset game button for host
        if name == game["host"]:
            st.markdown("---")
            if st.button("🔄 Reset Game (Host Only)", type="secondary"):
                # Reset game to lobby state
                game["started"] = False
                game["phase"] = "lobby"
                game["roles"] = {}
                game["votes"] = {}
                game["day_count"] = 1
                game["night_results"] = {}
                game["game_over"] = False
                game["winner"] = ""
                save_game(game_id, game)
                st.success("Game reset to lobby!")
                st.rerun()
elif page == "Help":
    st.header("🆘 Help - How to Play")
    st.markdown("""
    **Mafia** is a social deduction game. The game consists of two main phases:

    - **Night Phase**: 
        - Mafia choose someone to kill.
        - Doctor can save a player.
        - Detective can investigate a player's role.

    - **Day Phase**:
        - All players discuss and vote to eliminate a suspicious player.

    **Roles:**
    - 🔪 Mafia: Work together to eliminate everyone else.
    - 🕵️ Detective: Can investigate one player per night.
    - 💉 Doctor: Can save one player per night.
    - 🧑 Villager: No special powers, just logic and deduction.

    The game continues until:
    - All Mafia are eliminated (Villagers win)
    - Mafia equal or outnumber others (Mafia wins)
    """)

elif page == "About":
    st.header("📖 About This Game")
    st.markdown("""
    This is a web version of the popular party game **Mafia**, built with [Streamlit](https://streamlit.io) and [SQLite].

    - Created by Aritro Shome
    - Multiplayer-ready, lobby-based
    - Simple UI, no logins required
                
    The inspiration behind this was one of my friends at another uni mentioned playing this game with their friends in their hostel and when I checked out the rules, I was sad that one of the people had to sit out as the narrator, which prompted me to build this so as to bypass the need for a narrator.
    Source code available on Github
    """)
