# 🕶️ Mafia Undercover – A Streamlit Game App

Welcome to **Mafia Undercover**, a party deception game brought to the web! Built using **Python**, **Streamlit**, and **SQLite**, this app lets friends join remotely, get assigned secret roles, and play a turn-based game of trust, deduction, and survival.

---

## 🎯 Game Objective

Players are secretly assigned roles: **Mafia**, **Doctor**, **Detective**, or **Villagers**.

- **Mafia** work together to eliminate others.
- **Doctor** can save someone each night.
- **Detective** investigates players to uncover the Mafia.
- **Villagers** try to identify and vote out the Mafia.

---

## 🚀 Features

- 🔒 Host or join games via unique Game ID  
- 👥 Real-time lobby with player list  
- 🎭 Random secret role assignment  
- 🌙 Night phase with Mafia vote, Doctor save, and Detective investigation  
- ☀️ Day phase with public discussion and majority voting  
- 🗳️ Vote handling and result resolution  
- 📦 SQLite-based persistent backend  
- 🔁 Refresh button to update state manually  

---

## 🛠️ Technologies Used

- [Streamlit](https://streamlit.io/) – for the frontend UI  
- `sqlite3` – built-in lightweight database for game persistence  
- `uuid` – to generate unique Game IDs  

---

## 🖥️ How to Run

1. **Clone the Repository**
   ```bash
   git clone https://github.com/your-username/mafia-streamlit-game.git
   cd mafia-streamlit-game
   ```

2. **Install Requirements**
   *(Only Streamlit is needed)*
   ```bash
   pip install streamlit
   ```

3. **Run the App**
   ```bash
   streamlit run mafia.py
   ```
---

## 📋 Game Flow

1. **Create or Join a Game**  
2. **Wait in Lobby until Host starts**  
3. **Secret Role Assignment**  
4. **Night Phase**:  
   - Mafia vote to kill  
   - Doctor chooses someone to save  
   - Detective investigates a player  
5. **Day Phase**:  
   - System reveals if someone died  
   - Players vote on whom to eliminate  
6. **Repeat until Mafia win or all are caught**  

---

## ⚠️ Notes

- Minimum 4 players required to start.    
- Refresh button can be used to sync state manually.  

---

## 🧠 Future Improvements

- 🎤 Chatbox / discussion simulation
- 📱 Mobile-friendly styling or PWA support  
- 🔐 User login and profiles  

---

## 📄 License

MIT License — use it freely in your own projects!


(c) Aritro 'sortira' Shome 2025 - Present 
