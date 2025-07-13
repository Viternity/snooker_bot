# 🧪 Snooker League Bot - Setup & Testing Guide

This document provides a step-by-step testing procedure for setting up and validating the Ellesmere Port Snooker League Discord Bot functionality.

## 📋 Prerequisites

Before starting the testing process, ensure you have:

- ✅ Discord Bot Token (from Discord Developer Portal)
- ✅ Bot added to your Discord server with Admin role
- ✅ Python 3.8+ installed
- ✅ Required packages installed (`pip install -r requirements.txt`)
- ✅ `local.env` file configured with your bot token

## 🚀 Initial Setup

### Step 1: Bot Connection Test
```bash
python bot.py
```
**Expected Result**: Bot should connect and display "Database setup complete."

### Step 2: Verify Bot Permissions
Ensure the bot has these permissions in your Discord server:
- Send Messages
- Read Message History
- Use Slash Commands
- Manage Messages (optional)

## 🏗️ Phase 1: Database & Basic Setup Testing

### Test 1.1: Create Test Teams
**Command**: `!add_team "Test Team A"`
**Expected**: ✅ Team 'Test Team A' has been added to the master list.

**Command**: `!add_team "Test Team B"`
**Expected**: ✅ Team 'Test Team B' has been added to the master list.

**Command**: `!add_team "Test Team C"`
**Expected**: ✅ Team 'Test Team C' has been added to the master list.

### Test 1.2: Create Test Players
**Command**: `!add_player @TestPlayer1 0 "Test Team A"`
**Expected**: ✅ Player 'TestPlayer1' registered with handicap 0. Assigned to team 'Test Team A'.

**Command**: `!add_player @TestPlayer2 5`
**Expected**: ✅ Player 'TestPlayer2' registered with handicap 5.

**Command**: `!add_player @TestPlayer3 -5`
**Expected**: ✅ Player 'TestPlayer3' registered with handicap -5.

### Test 1.3: Assign Players to a Team
**Command**: `!assign_team "Test Team B" @TestPlayer2 @TestPlayer3`
**Expected**: Response indicates `TestPlayer2` and `TestPlayer3` were assigned to `Test Team B`.

### Test 1.4: Verify Player Registration
**Command**: `!handicap @TestPlayer1`
**Expected**: Embed showing handicap: 0, win streak: 0, loss streak: 0.

## 🏆 Phase 2: Competition Management Testing

### Test 2.1: Create League Competition
**Command**: `!create_comp "Test League" league yes`
**Expected**: 🏆 Competition 'Test League' created! Type: `league`, Affects Handicaps: `True`

### Test 2.2: Create Cup Competition
**Command**: `!create_comp "Test Cup" cup no`
**Expected**: 🏆 Competition 'Test Cup' created! Type: `cup`, Affects Handicaps: `False`

### Test 2.3: List Competitions
**Command**: `!list_comps`
**Expected**: Embed showing both competitions with their types and handicap settings

### Test 2.4: Set Competition Channels
**Command**: `!comp_channel "Test League" fixtures #fixtures-channel`
**Expected**: ✅ The `fixtures` channel for 'Test League' has been set to #fixtures-channel.

**Command**: `!comp_channel "Test League" results #results-channel`
**Expected**: ✅ The `results` channel for 'Test League' has been set to #results-channel.

## 👥 Phase 3: Participant Management Testing

### Test 3.1: Add Multiple Participants to League
**Command**: `!add_participant "Test League" "Test Team A" "Test Team B" "Test Team C"`
**Expected**: Embed showing `Test Team A`, `Test Team B`, and `Test Team C` were successfully added.

### Test 3.2: Add Multiple Participants to Cup
**Command**: `!add_participant "Test Cup" @TestPlayer1 @TestPlayer2 @TestPlayer3`
**Expected**: Embed showing `TestPlayer1`, `TestPlayer2`, and `TestPlayer3` were successfully added.

## 🎲 Phase 4: Fixture Generation & Randomness Testing

### Test 4.1: Generate League Fixtures
**Command**: `!generate_fixtures "Test League"`
**Expected**: 
- Fixtures posted in #fixtures-channel
- 3 teams should create 2 weeks of fixtures
- Each team should play each other team once
- Random rotation should be different each time

**Validation Checklist**:
- [ ] All teams appear in fixtures
- [ ] No team plays itself
- [ ] Each team plays exactly 2 matches
- [ ] Fixtures are posted in correct channel

### Test 4.2: Test Fixture Randomness
**Command**: `!generate_fixtures "Test League"` (run multiple times)
**Expected**: Different fixture orders each time due to `random.shuffle(teams)`

### Test 4.3: Generate Cup Fixtures
**Command**: `!generate_fixtures "Test Cup"`
**Expected**:
- First round matches generated
- If odd number of players, one gets a bye
- Random pairing of players

**Validation Checklist**:
- [ ] All players appear in fixtures
- [ ] No player plays themselves
- [ ] Random pairing order
- [ ] Bye player (if odd number) clearly marked

### Test 7.4: Insufficient Participants
**Command**: `!generate_fixtures "Test League"` (after removing teams)
**Expected**: ⚠️ Not enough teams in 'Test League' to generate league fixtures.

## 📊 Phase 5: Match Reporting & Handicap System Testing

### Test 5.1: Report Match (League - Affects Handicaps)
**Command**: `!report "Test League" winner @TestPlayer1 loser @TestPlayer2`
**Expected**: 
- Result logged in #results-channel
- TestPlayer1: win streak = 1, loss streak = 0
- TestPlayer2: win streak = 0, loss streak = 1
- No handicap changes yet (need 3 wins/losses)

### Test 5.2: Report Multiple Wins (Test Handicap Reduction)
**Command**: `!report "Test League" winner @TestPlayer1 loser @TestPlayer3`
**Expected**: TestPlayer1 win streak = 2

**Command**: `!report "Test League" winner @TestPlayer1 loser @TestPlayer2`
**Expected**: 
- TestPlayer1 handicap reduced by 5 (from 0 to -5)
- Win streak reset to 0
- Message: "🎉 **TestPlayer1**'s handicap reduced to **-5**."

### Test 5.3: Report Multiple Losses (Test Handicap Increase)
**Command**: `!report "Test League" winner @TestPlayer3 loser @TestPlayer2`
**Expected**: TestPlayer2 loss streak = 2

**Command**: `!report "Test League" winner @TestPlayer1 loser @TestPlayer2`
**Expected**: 
- TestPlayer2 handicap increased by 5 (from 5 to 10)
- Loss streak reset to 0
- Message: "😢 **TestPlayer2**'s handicap increased to **10**."

### Test 5.4: Report Match (Cup - No Handicap Changes)
**Command**: `!report "Test Cup" winner @TestPlayer3 loser @TestPlayer1`
**Expected**: 
- Result logged in current channel (no results channel set)
- No handicap changes (competition doesn't affect handicaps)

## 📈 Phase 6: Statistics & Data Validation

### Test 6.1: Check Player Statistics
**Command**: `!handicap @TestPlayer1`
**Expected**: Embed showing updated handicap and streaks

**Command**: `!handicap @TestPlayer2`
**Expected**: Embed showing updated handicap and streaks

### Test 6.2: Test Head-to-Head Records
**Command**: `!h2h @TestPlayer1 @TestPlayer2`
**Expected**: Embed showing 2-1 record (TestPlayer1 has 2 wins, TestPlayer2 has 1 win)

**Command**: `!h2h @TestPlayer1 @TestPlayer3`
**Expected**: Embed showing 1-0 record

## 🔄 Phase 7: Error Handling & Edge Cases

### Test 7.1: Duplicate Entries
**Command**: `!add_team "Test Team A"`
**Expected**: ⚠️ Error: A team with the name 'Test Team A' already exists.

**Command**: `!add_player @TestPlayer1 10`
**Expected**: ⚠️ Error: Player 'TestPlayer1' is already registered.

### Test 7.2: Invalid Competition Types
**Command**: `!create_comp "Invalid Comp" tournament yes`
**Expected**: ⚠️ Invalid type. Must be `league` or `cup`.

### Test 7.3: Missing Channels
**Command**: `!generate_fixtures "Test Cup"`
**Expected**: ⚠️ Please set a fixtures channel for 'Test Cup' first using `!comp_channel`.

## 🧹 Phase 8: Deletion and Cleanup Testing

### Test 8.1: Delete Player with Match History (Expected Fail)
**Command**: `!report "Test League" winner @TestPlayer1 loser @TestPlayer2` (Ensure there's match history)
**Command**: `!del_player @TestPlayer1`
**Expected**: ⚠️ Error indicating the player has match history and cannot be deleted.

### Test 8.2: Delete Player without Match History
**Command**: `!add_player @TempPlayer 0`
**Command**: `!del_player @TempPlayer`
**Expected**: ✅ Player 'TempPlayer' has been deleted.

### Test 8.3: Delete Team
**Command**: `!del_team "Test Team C"`
**Expected**: ✅ Team 'Test Team C' has been deleted. Players on this team are now free agents.

### Test 8.4: Verify Database Integrity
After all tests, check that:
- [ ] All matches are recorded in `match_history`.
- [ ] Handicaps are correctly updated
- [ ] Win/loss streaks are accurate
- [ ] Competition participants are properly linked.

### Test 8.5: Test Bot Restart
1. Stop the bot (Ctrl+C)
2. Restart: `python bot.py`
3. Verify all data persists:
   - `!list_comps` should show competitions
   - `!handicap @TestPlayer1` should show updated stats
   - `!h2h @TestPlayer1 @TestPlayer2` should show match history

## ✅ Success Criteria

The bot is working correctly if:

1. **Database Operations**: All CRUD operations work without errors
2. **Fixture Generation**: 
   - League fixtures are fair and complete
   - Cup fixtures are properly randomized
   - BYE weeks are handled correctly
3. **Handicap System**: 
   - 3-win streaks reduce handicap by 5
   - 3-loss streaks increase handicap by 5
   - Streaks reset after changes
4. **Match Reporting**: 
   - Results are logged correctly
   - Handicap changes are applied appropriately
   - Output goes to correct channels
5. **Statistics**: 
   - Player stats are accurate
   - Head-to-head records are correct
   - Data persists across restarts

## 🐛 Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid bot token | Regenerate token in Discord Developer Portal |
| Missing permissions | Bot lacks required permissions | Add bot to server with proper permissions |
| Database errors | Corrupted database file | Delete `league_database.sqlite` and restart |
| Channel not found | Bot can't see channel | Check bot permissions for that channel |
| Role errors | User lacks Admin role | Assign Admin role to user |

## 📝 Testing Notes

- **Randomness**: Run fixture generation multiple times to verify randomness
- **Data Persistence**: Always test restart functionality
- **Error Messages**: Verify all error conditions show appropriate messages
- **Channel Management**: Test both fixtures and results channels
- **Handicap Logic**: Test both positive and negative handicap scenarios

---

**Test Completed By**: _________________  
**Date**: _________________  
**Bot Version**: 2.0  
**All Tests Passed**: ☐ Yes ☐ No 