# Ellesmere Port Snooker League Bot

A custom Discord bot designed to manage and automate the Ellesmere Port Snooker League. This bot ensures fair, transparent, and efficient league operations by providing randomized fixture generation and fully automated handicap calculations.

## 🌟 Core Features

The bot is built to handle all key aspects of running the league:

- **🎲 Randomized Fixture Generation**: Creates a provably random and fair home-and-away schedule for the entire season with a single command.
- **🤖 Automated Handicap System**: Automatically tracks player win/loss streaks and adjusts handicaps based on a "3-in-a-row" rule, removing any possibility of manual error or bias.
- **📊 Persistent Match History**: Every reported singles match is logged, allowing for detailed data analysis and player statistics.
- **🔒 Admin Controls**: League administrators have full control over managing teams, players, and bot settings through role-restricted commands.
- **📈 Player Statistics**: Players can check their own stats, their match history, and even see their head-to-head record against any other player in the league.
- **📢 Organized Channel Management**: Admins can designate specific channels for bot commands and result announcements, keeping the server tidy.

## 📖 How to Use the Bot

The bot is controlled via simple commands in your Discord server.

### For All Players & Captains

These are the commands everyone can use to interact with the league.

| Command | Description | Example |
|---------|-------------|---------|
| `!report` | (Captains) Report the result of a singles match. Must be in the format `winner @user loser @user`. | `!report "Summer Cup" winner @JohnHiggins loser @RonnieOSullivan` |
| `!handicap` | Check the current handicap and win/loss streak for any player. | `!handicap @JuddTrump` |
| `!history` | View the last 10 match results for any player. | `!history @MarkSelby` |
| `!h2h` | See the head-to-head lifetime score between two players. | `!h2h @NeilRobertson @ShaunMurphy` |
| `!list_comps`| Lists all created competitions. | `!list_comps` |
| `!help` | Shows a list of all available commands. | `!help` or `!help report` |

### For League Admins (Admin Role Required)

These commands are used to set up and manage the league and its competitions.

| Command | Description | Example |
|---------|-------------|---------|
| `!add_team` | Adds a new team to the league roster. | `!add_team "The Potters"` |
| `!del_team` | Deletes a team. Players on the team become free agents. | `!del_team "The Potters"` |
| `!add_player` | Registers a player, optionally assigning them to a team. | `!add_player @Newbie -10 "The Potters"` |
| `!del_player` | Deletes a player. Fails if they have match history. | `!del_player @OldPlayer` |
| `!assign_team`| Assigns one or more players to a team. | `!assign_team "The Potters" @Player1 @Player2`|
| `!create_comp`| Creates a new competition (`league` or `cup`). | `!create_comp "Summer Cup" cup yes` |
| `!comp_channel`| Sets the channels for fixtures or results for a competition. | `!comp_channel "Summer Cup" results #match-results` |
| `!add_participant`| Adds one or more participants to a competition. | `!add_participant "Summer Cup" @Player1 "Team B"` |
| `!generate_fixtures` | (Use with care!) Generates fixtures for a competition. | `!generate_fixtures "Summer Cup"` |

## 🛠️ Installation & Hosting (For Developers)

This section details how to host and run the bot yourself.

### Prerequisites

- Python 3.8+
- Git
- A Discord Bot Token (from the Discord Developer Portal)

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/snooker-bot.git
cd snooker-bot
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

Create a file named `local.env` in the root directory and add your Discord bot token:

```
DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE"
```

### 4. Run the Bot

```bash
python bot.py
```

The bot should now be online and connected to your server.

## 🚀 Deployment with Docker (Recommended)

Using Docker is the recommended way to deploy the bot for 24/7 uptime on a server.

1. **Build the Docker image:**

```bash
docker build -t snooker-bot .
```

2. **Run the Docker container:**

Make sure to pass your bot token as an environment variable.

```bash
docker run -d --name snooker-league-bot -e DISCORD_TOKEN="YOUR_BOT_TOKEN_HERE" snooker-bot
```

The bot will now be running in a detached container on your server.

## 🏛️ Database

The bot uses a simple and lightweight SQLite database (`league_database.sqlite`) which is created automatically when the bot first starts. It contains the following tables:

- **teams**: Stores team names.
- **players**: Stores player Discord IDs, names, handicaps, streaks, and team affiliation (`team_id`).
- **competitions**: Defines each league or cup event.
- **competition_participants**: Links players/teams to the competitions they are in.
- **match_history**: Logs every completed match for statistical analysis.

## 🔮 Future Plans

This project is designed to be extensible. The next major planned phase is:

**Phase 2: Web Portal**: Develop a public-facing website that connects to the bot's database to display interactive league tables, player profiles, and detailed statistics in a more visual format.