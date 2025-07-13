# bot.py
# Main script for the Ellesmere Port Snooker League Discord Bot

import discord
from discord.ext import commands
import sqlite3
import random
import asyncio
from dotenv import load_dotenv
import os
from datetime import datetime

# --- BOT SETUP ---
load_dotenv('local.env')
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
DB_FILE = 'league_database.sqlite'

# --- DATABASE HELPER FUNCTIONS ---

def db_connect():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def setup_database():
    """Initializes the database with the competition-centric schema."""
    conn = db_connect()
    cursor = conn.cursor()
    
    # Master list of all teams
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Master list of all players
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS players (
            id INTEGER PRIMARY KEY, -- Discord User ID
            name TEXT NOT NULL,
            handicap INTEGER DEFAULT 0,
            win_streak INTEGER DEFAULT 0,
            loss_streak INTEGER DEFAULT 0,
            team_id INTEGER,
            FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE SET NULL
        )
    ''')

    # For existing databases, add team_id column to players if it's missing.
    try:
        cursor.execute("PRAGMA table_info(players)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'team_id' not in columns:
            cursor.execute("ALTER TABLE players ADD COLUMN team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL")
            print("Database updated: 'team_id' column added to 'players' table.")
    except sqlite3.Error:
        # Table might not exist yet, but the CREATE statement will handle it.
        pass

    # New table to define each competition
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competitions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            type TEXT NOT NULL, -- "league" or "cup"
            affects_handicap BOOLEAN NOT NULL,
            fixtures_channel_id INTEGER,
            results_channel_id INTEGER
        )
    ''')
    
    # New table to link players/teams to specific competitions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS competition_participants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER NOT NULL,
            participant_id INTEGER NOT NULL, -- Can be a player ID or a team ID
            participant_type TEXT NOT NULL, -- "player" or "team"
            FOREIGN KEY(competition_id) REFERENCES competitions(id) ON DELETE CASCADE
        )
    ''')

    # Match History now links to a competition
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS match_history (
            match_id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER NOT NULL,
            winner_id INTEGER NOT NULL,
            loser_id INTEGER NOT NULL,
            match_date TEXT NOT NULL,
            FOREIGN KEY(competition_id) REFERENCES competitions(id),
            FOREIGN KEY(winner_id) REFERENCES players(id),
            FOREIGN KEY(loser_id) REFERENCES players(id)
        )
    ''')

    # New table to store generated fixtures
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fixtures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            competition_id INTEGER NOT NULL,
            week INTEGER, -- For leagues
            round INTEGER, -- For cups
            participant1_id INTEGER NOT NULL,
            participant2_id INTEGER, -- Can be NULL for a bye
            is_complete BOOLEAN DEFAULT 0,
            FOREIGN KEY(competition_id) REFERENCES competitions(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("Database setup complete.")

# --- BOT EVENTS ---

@bot.event
async def on_ready():
    """Event that runs when the bot has successfully connected to Discord."""
    print(f'{bot.user.name} has connected to Discord!')
    setup_database()

# --- ADMIN: MASTER LIST MANAGEMENT ---

@bot.command(name='add_team', help='Adds a team to the master list. Usage: !add_team "Team Name"')
@commands.has_role('Admin')
async def add_team(ctx, team_name: str):
    conn = db_connect()
    try:
        conn.cursor().execute("INSERT INTO teams (name) VALUES (?)", (team_name,))
        conn.commit()
        await ctx.send(f"✅ Team '{team_name}' has been added to the master list.")
    except sqlite3.IntegrityError:
        await ctx.send(f"⚠️ Error: A team with the name '{team_name}' already exists.")
    finally:
        conn.close()

@bot.command(name='del_team', help='Deletes a team from the master list. Usage: !del_team "Team Name"')
@commands.has_role('Admin')
async def del_team(ctx, team_name: str):
    conn = db_connect()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
        team = cursor.fetchone()
        if not team:
            await ctx.send(f"⚠️ Error: Team '{team_name}' not found.")
            return

        team_id = team['id']

        # Remove team from any competitions
        cursor.execute("DELETE FROM competition_participants WHERE participant_id = ? AND participant_type = 'team'", (team_id,))
        
        # Delete the team. ON DELETE SET NULL in the players table will handle un-assigning players.
        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        
        conn.commit()
        await ctx.send(f"✅ Team '{team_name}' has been deleted. Players on this team are now free agents.")
    except sqlite3.Error as e:
        conn.rollback()
        await ctx.send(f"⚠️ A database error occurred: {e}")
    finally:
        conn.close()

@bot.command(name='add_player', help='Adds a player. Usage: !add_player @user <handicap> ["Team Name"]')
@commands.has_role('Admin')
async def add_player(ctx, member: discord.Member, starting_handicap: int, *, team_name: str = None):
    conn = db_connect()
    cursor = conn.cursor()
    
    team_id = None
    if team_name:
        cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
        team = cursor.fetchone()
        if not team:
            await ctx.send(f"⚠️ Warning: Team '{team_name}' not found. Player will be added without a team.")
        else:
            team_id = team['id']
            
    try:
        cursor.execute("INSERT INTO players (id, name, handicap, team_id) VALUES (?, ?, ?, ?)", 
                       (member.id, member.display_name, starting_handicap, team_id))
        conn.commit()
        
        response = f"✅ Player '{member.display_name}' registered with handicap {starting_handicap}."
        if team_id:
            response += f" Assigned to team '{team_name}'."
        await ctx.send(response)
    except sqlite3.IntegrityError:
        await ctx.send(f"⚠️ Error: Player '{member.display_name}' is already registered.")
    finally:
        conn.close()

@bot.command(name='del_player', help='Deletes a player. Usage: !del_player @user')
@commands.has_role('Admin')
async def del_player(ctx, member: discord.Member):
    conn = db_connect()
    cursor = conn.cursor()
    try:
        # First, check if player exists
        cursor.execute("SELECT id FROM players WHERE id = ?", (member.id,))
        if not cursor.fetchone():
            await ctx.send(f"⚠️ Error: Player '{member.display_name}' is not registered.")
            return

        # Remove player from any competitions
        cursor.execute("DELETE FROM competition_participants WHERE participant_id = ? AND participant_type = 'player'", (member.id,))
        
        # Attempt to delete the player
        cursor.execute("DELETE FROM players WHERE id = ?", (member.id,))
        
        conn.commit()
        await ctx.send(f"✅ Player '{member.display_name}' has been deleted from the master list and all competitions.")
    except sqlite3.IntegrityError:
        conn.rollback()
        await ctx.send(f"⚠️ Error: Could not delete '{member.display_name}'. They likely have match history. Players with existing matches cannot be deleted to preserve data integrity.")
    except sqlite3.Error as e:
        conn.rollback()
        await ctx.send(f"⚠️ A database error occurred: {e}")
    finally:
        conn.close()

@bot.command(name='assign_team', help='Assigns one or more players to a team. Usage: !assign_team "Team Name" @player1 @player2 ...')
@commands.has_role('Admin')
async def assign_team(ctx, team_name: str, *members: discord.Member):
    if not members:
        return await ctx.send("⚠️ You must specify at least one player to assign.")

    conn = db_connect()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM teams WHERE name = ?", (team_name,))
    team = cursor.fetchone()
    if not team:
        await ctx.send(f"⚠️ Error: Team '{team_name}' not found.")
        conn.close()
        return

    team_id = team['id']
    successful_assignments = []
    failed_assignments = []

    for member in members:
        cursor.execute("UPDATE players SET team_id = ? WHERE id = ?", (team_id, member.id))
        if cursor.rowcount > 0:
            conn.commit() # Commit after each successful update
            successful_assignments.append(member.display_name)
        else:
            failed_assignments.append(member.display_name)
    
    conn.close()

    response = ""
    if successful_assignments:
        response += f"✅ Assigned players to '{team_name}': {', '.join(successful_assignments)}\n"
    if failed_assignments:
        response += f"⚠️ Could not assign or find these players (they may not be registered): {', '.join(failed_assignments)}"
    
    await ctx.send(response.strip())

# --- ADMIN: COMPETITION MANAGEMENT ---

@bot.command(name='create_comp', help='Creates a new competition. Usage: !create_comp "Comp Name" <type> <handicap_rules>')
@commands.has_role('Admin')
async def create_comp(ctx, name: str, comp_type: str, affects_handicap: str):
    comp_type = comp_type.lower()
    if comp_type not in ['league', 'cup']:
        return await ctx.send("⚠️ Invalid type. Must be `league` or `cup`.")
    
    handicap_bool = affects_handicap.lower() in ['yes', 'true', 'y', '1']
    
    conn = db_connect()
    try:
        conn.cursor().execute("INSERT INTO competitions (name, type, affects_handicap) VALUES (?, ?, ?)",
                       (name, comp_type, handicap_bool))
        conn.commit()
        await ctx.send(f"🏆 Competition '{name}' created! Type: `{comp_type}`, Affects Handicaps: `{handicap_bool}`.")
    except sqlite3.IntegrityError:
        await ctx.send(f"⚠️ Error: A competition with the name '{name}' already exists.")
    finally:
        conn.close()

@bot.command(name='comp_channel', help='Assigns a channel to a competition. Usage: !comp_channel "Comp Name" <type> <#channel>')
@commands.has_role('Admin')
async def comp_channel(ctx, name: str, channel_type: str, channel: discord.TextChannel):
    channel_type = channel_type.lower()
    if channel_type not in ['fixtures', 'results']:
        return await ctx.send("⚠️ Invalid channel type. Must be `fixtures` or `results`.")
    
    column = f"{channel_type}_channel_id"
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute(f"UPDATE competitions SET {column} = ? WHERE name = ?", (channel.id, name))
    if cursor.rowcount > 0:
        conn.commit()
        await ctx.send(f"✅ The `{channel_type}` channel for '{name}' has been set to {channel.mention}.")
    else:
        await ctx.send(f"⚠️ Error: Competition '{name}' not found.")
    conn.close()

@bot.command(name='add_participant', help='Adds one or more participants to a competition. Usage: !add_participant "Comp Name" @player1 "Team Name" @player2 ...')
@commands.has_role('Admin')
async def add_participant(ctx, comp_name: str, *participants: str):
    if not participants:
        return await ctx.send("⚠️ You must specify at least one participant to add.")

    conn = db_connect()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM competitions WHERE name = ?", (comp_name,))
    comp = cursor.fetchone()
    if not comp:
        await ctx.send(f"⚠️ Competition '{comp_name}' not found.")
        conn.close()
        return
    
    comp_id = comp['id']
    added = []
    failed = []
    already_in = []

    for p_str in participants:
        participant_id = None
        participant_type = None
        participant_name = p_str

        try:
            # Prioritize player mentions
            member = await commands.MemberConverter().convert(ctx, p_str)
            participant_id = member.id
            participant_type = 'player'
            participant_name = member.display_name
        except commands.MemberNotFound:
            # Fallback to team name
            cursor.execute("SELECT id, name FROM teams WHERE name = ?", (p_str,))
            team = cursor.fetchone()
            if team:
                participant_id = team['id']
                participant_type = 'team'
                participant_name = team['name']
            else:
                failed.append(f"'{p_str}'")
                continue
        
        if participant_id:
            try:
                cursor.execute("INSERT INTO competition_participants (competition_id, participant_id, participant_type) VALUES (?, ?, ?)",
                               (comp_id, participant_id, participant_type))
                conn.commit()
                if cursor.rowcount > 0:
                    added.append(participant_name)
                else: # Should not happen with the check above but as a safeguard
                    already_in.append(participant_name)
            except sqlite3.IntegrityError:
                 # This participant is already in the competition
                already_in.append(participant_name)
    
    conn.close()

    embed = discord.Embed(title=f"Participant Report for '{comp_name}'", color=discord.Color.blue())
    if added:
        embed.add_field(name="✅ Added", value='\n'.join(added), inline=False)
    if already_in:
        embed.add_field(name="⚠️ Already in Competition", value='\n'.join(already_in), inline=False)
    if failed:
        embed.add_field(name="❌ Not Found", value='\n'.join(failed), inline=False)

    await ctx.send(embed=embed)

@bot.command(name='list_comps', help='Lists all created competitions.')
async def list_comps(ctx):
    conn = db_connect()
    comps = conn.cursor().execute("SELECT name, type, affects_handicap FROM competitions").fetchall()
    conn.close()
    if not comps:
        return await ctx.send("No competitions have been created yet.")
    
    embed = discord.Embed(title="🏆 Registered Competitions", color=discord.Color.gold())
    for comp in comps:
        embed.add_field(name=comp['name'], value=f"Type: `{comp['type']}`\nHandicaps: `{'Yes' if comp['affects_handicap'] else 'No'}`", inline=False)
    await ctx.send(embed=embed)


# --- FIXTURE GENERATION ---

@bot.command(name='generate_fixtures', help='Generates fixtures for a competition. Usage: !generate_fixtures "Comp Name"')
@commands.has_role('Admin')
async def generate_fixtures(ctx, comp_name: str):
    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM competitions WHERE name = ?", (comp_name,))
    comp = cursor.fetchone()
    if not comp:
        conn.close()
        return await ctx.send(f"⚠️ Competition '{comp_name}' not found.")

    # Check for existing fixtures and ask for confirmation to overwrite
    cursor.execute("SELECT id FROM fixtures WHERE competition_id = ?", (comp['id'],))
    if cursor.fetchone():
        await ctx.send("⚠️ Fixtures already exist for this competition. Regenerating will delete them. **Are you sure?** (yes/no)")
        
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel and m.content.lower() in ['yes', 'no']
        
        try:
            msg = await bot.wait_for('message', timeout=30.0, check=check)
            if msg.content.lower() == 'no':
                await ctx.send("Fixture generation cancelled.")
                conn.close()
                return
        except asyncio.TimeoutError:
            await ctx.send("No response received. Aborting fixture generation.")
            conn.close()
            return
        
        # User confirmed, so delete old fixtures
        cursor.execute("DELETE FROM fixtures WHERE competition_id = ?", (comp['id'],))
        conn.commit()
        await ctx.send("Old fixtures cleared. Generating new ones...")
    
    if not comp['fixtures_channel_id']:
        conn.close()
        return await ctx.send(f"⚠️ Please set a fixtures channel for '{comp_name}' first using `!comp_channel`.")
    
    output_channel = bot.get_channel(comp['fixtures_channel_id'])
    if not output_channel:
        conn.close()
        return await ctx.send(f"⚠️ Could not find the fixtures channel. Maybe I don't have permission to see it?")

    embed = discord.Embed(title=f"🗓️ Fixtures for {comp_name}", color=discord.Color.blue())

    # --- LEAGUE LOGIC ---
    if comp['type'] == 'league':
        cursor.execute("""
            SELECT p.id, p.name FROM competition_participants cp
            JOIN teams p ON cp.participant_id = p.id
            WHERE cp.competition_id = ? AND cp.participant_type = 'team'
        """, (comp['id'],))
        teams = [dict(row) for row in cursor.fetchall()]
        
        if len(teams) < 2:
            conn.close()
            return await ctx.send(f"⚠️ Not enough teams in '{comp_name}' to generate league fixtures.")
        
        if len(teams) % 2 != 0:
            teams.append({'id': None, 'name': "BYE"})
        random.shuffle(teams)
        
        num_weeks = len(teams) - 1
        for week in range(1, num_weeks + 1):
            week_fixtures_display = []
            for i in range(len(teams) // 2):
                home = teams[i]
                away = teams[len(teams) - 1 - i]
                if i != 0 and week % 2 != 0:
                    home, away = away, home

                if "BYE" in (home['name'], away['name']):
                    bye_team = home if away['name'] == 'BYE' else away
                    cursor.execute("INSERT INTO fixtures (competition_id, week, participant1_id, is_complete) VALUES (?, ?, ?, 1)",
                                   (comp['id'], week, bye_team['id']))
                    week_fixtures_display.append((bye_team['name'], "BYE"))
                else:
                    cursor.execute("INSERT INTO fixtures (competition_id, week, participant1_id, participant2_id) VALUES (?, ?, ?, ?)",
                                   (comp['id'], week, home['id'], away['id']))
                    week_fixtures_display.append((home['name'], away['name']))
            
            week_str = ""
            for p1_name, p2_name in week_fixtures_display:
                if p2_name == "BYE":
                    week_str += f"**{p1_name}** has a BYE week.\n"
                else:
                    week_str += f"**{p1_name}** vs **{p2_name}**\n"
            embed.add_field(name=f"Week {week}", value=week_str.strip(), inline=False)
            teams.insert(1, teams.pop())

    # --- CUP LOGIC ---
    elif comp['type'] == 'cup':
        cursor.execute("""
            SELECT p.id, p.name FROM competition_participants cp
            JOIN players p ON cp.participant_id = p.id
            WHERE cp.competition_id = ? AND cp.participant_type = 'player'
        """, (comp['id'],))
        players = [dict(row) for row in cursor.fetchall()]
        
        if len(players) < 2:
            conn.close()
            return await ctx.send(f"⚠️ Not enough players in '{comp_name}' to generate cup fixtures.")
        
        random.shuffle(players)
        round_num = 1
        
        if len(players) % 2 != 0:
            bye_player = players.pop()
            cursor.execute("INSERT INTO fixtures (competition_id, round, participant1_id, is_complete) VALUES (?, ?, ?, 1)",
                           (comp['id'], round_num, bye_player['id']))
            embed.add_field(name=f"Round {round_num} Bye", value=f"{bye_player['name']} gets a bye to the next round!", inline=False)
        
        cup_str = ""
        for i in range(0, len(players), 2):
            p1, p2 = players[i], players[i+1]
            cursor.execute("INSERT INTO fixtures (competition_id, round, participant1_id, participant2_id) VALUES (?, ?, ?, ?)",
                           (comp['id'], round_num, p1['id'], p2['id']))
            cup_str += f"**{p1['name']}** vs **{p2['name']}**\n"
        embed.add_field(name=f"Round {round_num} Matches", value=cup_str.strip(), inline=False)

    conn.commit()
    conn.close()

    await output_channel.send(embed=embed)
    await ctx.send(f"✅ Fixtures generated and saved. View them in {output_channel.mention}.")


# --- PLAYER-FACING COMMANDS ---

@bot.command(name='report', help='Report a match result. Usage: !report "Comp Name" winner @winner loser @loser')
async def report(ctx, comp_name: str, winner_keyword: str, winner: discord.Member, loser_keyword: str, loser: discord.Member):
    if winner_keyword.lower() != 'winner' or loser_keyword.lower() != 'loser':
        return await ctx.send("⚠️ Invalid format. Use: `!report \"Comp Name\" winner @user loser @user`")

    conn = db_connect()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM competitions WHERE name = ?", (comp_name,))
    comp = cursor.fetchone()
    if not comp:
        return await ctx.send(f"⚠️ Competition '{comp_name}' not found.")
    
    # --- Update Fixture Status ---
    # Find the corresponding fixture and mark it as complete.
    # This logic assumes a 1v1 match in either a cup or league context for the two players involved.
    participant_ids = {winner.id, loser.id}
    fixture_query = """
        UPDATE fixtures
        SET is_complete = 1
        WHERE competition_id = ? AND is_complete = 0 AND
              ((participant1_id = ? AND participant2_id = ?) OR (participant1_id = ? AND participant2_id = ?))
    """
    cursor.execute(fixture_query, (comp['id'], winner.id, loser.id, loser.id, winner.id))

    # For team-based leagues, we might need a more complex lookup if we're only given players.
    # For now, this handles cup matches and any league matches reported between two specific players directly.

    # --- Process Handicap Logic (if applicable) ---
    handicap_change_msg = ""
    if comp['affects_handicap']:
        # Fetch winner and update
        cursor.execute("SELECT * FROM players WHERE id = ?", (winner.id,))
        w_data = cursor.fetchone()
        if w_data:
            w_h, w_ws, w_ls = w_data['handicap'], w_data['win_streak'] + 1, 0
            if w_ws >= 3:
                w_h -= 5
                w_ws = 0
                handicap_change_msg += f"🎉 **{winner.display_name}**'s handicap reduced to **{w_h}**."
            cursor.execute("UPDATE players SET handicap=?, win_streak=?, loss_streak=? WHERE id=?", (w_h, w_ws, w_ls, winner.id))

        # Fetch loser and update
        cursor.execute("SELECT * FROM players WHERE id = ?", (loser.id,))
        l_data = cursor.fetchone()
        if l_data:
            l_h, l_ws, l_ls = l_data['handicap'], 0, l_data['loss_streak'] + 1
            if l_ls >= 3:
                l_h += 5
                l_ls = 0
                handicap_change_msg += f"\n😢 **{loser.display_name}**'s handicap increased to **{l_h}**."
            cursor.execute("UPDATE players SET handicap=?, win_streak=?, loss_streak=? WHERE id=?", (l_h, l_ws, l_ls, loser.id))
        
        conn.commit()

    # --- Log Match to History ---
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("INSERT INTO match_history (competition_id, winner_id, loser_id, match_date) VALUES (?, ?, ?, ?)",
                   (comp['id'], winner.id, loser.id, current_date))
    conn.commit()
    conn.close()

    # --- Send Confirmation ---
    output_channel = bot.get_channel(comp['results_channel_id']) if comp['results_channel_id'] else ctx.channel
    embed = discord.Embed(title=f"Result Recorded for {comp_name}",
                          description=f"**Winner:** {winner.mention}\n**Loser:** {loser.mention}",
                          color=discord.Color.green())
    if handicap_change_msg:
        embed.add_field(name="Handicap Changes!", value=handicap_change_msg.strip(), inline=False)
    
    await output_channel.send(embed=embed)
    if output_channel != ctx.channel:
        await ctx.send(f"✅ Result logged in {output_channel.mention}.", delete_after=10)


@bot.command(name='handicap', help='Check a player\'s handicap and streak. Usage: !handicap @user')
async def handicap(ctx, member: discord.Member):
    conn = db_connect()
    player_data = conn.cursor().execute("SELECT * FROM players WHERE id = ?", (member.id,)).fetchone()
    conn.close()
    if player_data:
        embed = discord.Embed(title=f"📊 Status for {member.display_name}", color=member.color)
        embed.add_field(name="Current Handicap", value=f"**{player_data['handicap']}**", inline=True)
        embed.add_field(name="Win Streak", value=f"**{player_data['win_streak']}**", inline=True)
        embed.add_field(name="Loss Streak", value=f"**{player_data['loss_streak']}**", inline=True)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"⚠️ Player {member.mention} is not registered.")


@bot.command(name='h2h', help='Shows head-to-head record. Usage: !h2h @player1 @player2')
async def h2h(ctx, player1: discord.Member, player2: discord.Member):
    conn = db_connect()
    cursor = conn.cursor()
    p1_wins = cursor.execute("SELECT COUNT(*) FROM match_history WHERE winner_id = ? AND loser_id = ?", (player1.id, player2.id)).fetchone()[0]
    p2_wins = cursor.execute("SELECT COUNT(*) FROM match_history WHERE winner_id = ? AND loser_id = ?", (player2.id, player1.id)).fetchone()[0]
    conn.close()
    embed = discord.Embed(title=f"Head-to-Head: {player1.display_name} vs {player2.display_name}", color=discord.Color.purple())
    embed.add_field(name=player1.display_name, value=f"**{p1_wins}** wins", inline=True)
    embed.add_field(name=player2.display_name, value=f"**{p2_wins}** wins", inline=True)
    await ctx.send(embed=embed)

@bot.command(name='next_game', help='Shows your next opponent in a competition. Usage: !next_game "Comp Name" [@user]')
async def next_game(ctx, comp_name: str, member: discord.Member = None):
    """Shows the next upcoming, incomplete fixture for a player or team in a specific competition."""
    if member is None:
        member = ctx.author

    conn = db_connect()
    cursor = conn.cursor()

    # Find the competition
    cursor.execute("SELECT * FROM competitions WHERE name = ?", (comp_name,))
    comp = cursor.fetchone()
    if not comp:
        conn.close()
        return await ctx.send(f"⚠️ Competition '{comp_name}' not found.")

    next_fixture = None
    opponent_name = None

    if comp['type'] == 'cup': # Individual player lookup
        cursor.execute("""
            SELECT f.*, p1.name as p1_name, p2.name as p2_name
            FROM fixtures f
            LEFT JOIN players p1 ON f.participant1_id = p1.id
            LEFT JOIN players p2 ON f.participant2_id = p2.id
            WHERE f.competition_id = ? AND (f.participant1_id = ? OR f.participant2_id = ?) AND f.is_complete = 0
            ORDER BY f.round ASC
            LIMIT 1
        """, (comp['id'], member.id, member.id))
        fixture = cursor.fetchone()
        if fixture:
            opponent_id = fixture['participant2_id'] if fixture['participant1_id'] == member.id else fixture['participant1_id']
            opponent_name = fixture['p2_name'] if fixture['participant1_id'] == member.id else fixture['p1_name']
            next_fixture = f"Round {fixture['round']}: **{fixture['p1_name']}** vs **{fixture['p2_name']}**"

    elif comp['type'] == 'league': # Team-based lookup
        # First, find the user's team
        cursor.execute("SELECT team_id FROM players WHERE id = ?", (member.id,))
        player_team = cursor.fetchone()
        if not player_team or not player_team['team_id']:
            conn.close()
            return await ctx.send(f"⚠️ Player {member.display_name} is not assigned to a team.")
        
        team_id = player_team['team_id']
        cursor.execute("""
            SELECT f.*, t1.name as t1_name, t2.name as t2_name
            FROM fixtures f
            JOIN teams t1 ON f.participant1_id = t1.id
            JOIN teams t2 ON f.participant2_id = t2.id
            WHERE f.competition_id = ? AND (f.participant1_id = ? OR f.participant2_id = ?) AND f.is_complete = 0
            ORDER BY f.week ASC
            LIMIT 1
        """, (comp['id'], team_id, team_id))
        fixture = cursor.fetchone()
        if fixture:
            opponent_id = fixture['participant2_id'] if fixture['participant1_id'] == team_id else fixture['participant1_id']
            opponent_name = fixture['t2_name'] if fixture['participant1_id'] == team_id else fixture['t1_name']
            next_fixture = f"Week {fixture['week']}: **{fixture['t1_name']}** vs **{fixture['t2_name']}**"

    conn.close()

    if next_fixture:
        embed = discord.Embed(
            title=f"Next Game for {member.display_name} in {comp_name}",
            description=next_fixture,
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"✅ No upcoming games found for {member.display_name} in '{comp_name}'. All fixtures may be complete!")


# --- ERROR HANDLING ---
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send('🚫 You do not have the correct role for this command.')
    elif isinstance(error, commands.errors.MissingRequiredArgument):
        await ctx.send(f'⚠️ You are missing a required argument. Use `!help {ctx.command.name}` for more info.')
    elif isinstance(error, commands.errors.BadArgument):
        await ctx.send(f"⚠️ I couldn't understand one of your arguments. Please check the format.")
    else:
        print(f"An unhandled error occurred: {error}")
        await ctx.send("An unexpected error occurred. Please check the console for details.")

# --- RUN THE BOT ---
if __name__ == "__main__":
    if DISCORD_TOKEN:
        bot.run(DISCORD_TOKEN)
    else:
        print("Error: DISCORD_TOKEN not found. Please create a .env file and add your bot token.")
