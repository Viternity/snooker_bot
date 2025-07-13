# Snooker Bot Architecture Refactor Proposal

## 1. Introduction

This document outlines a proposal for a foundational refactoring of the snooker bot's architecture. The current system was built quickly and effectively, but some core ambiguities in the requirements have led to a design that will be difficult to maintain and extend.

The goal of this refactor is to create a more robust, flexible, and unambiguous system by addressing two key areas:
1.  **Unifying Competition Formats:** Merging the distinct "league" and "cup" concepts into a single, flexible system.
2.  **Clarifying Participant Roles:** Redefining the relationship between "players" and "teams" to more accurately reflect how snooker matches are played.

By making these changes now, we will create a solid foundation that is easier to build upon and less prone to bugs or confusion in the future.

---

## 2. Problem Statement: Current Ambiguities

### 2.1. "League" vs. "Cup" Distinction

The bot currently treats "leagues" and "cups" as fundamentally different entities.

-   **The Problem:** This has forced us to write separate logic paths (large `if/elif` blocks) for almost every feature, including fixture generation, participant management, and reporting. If the client uses these terms interchangeably, the bot's rigid structure will not match their mental model.
-   **The Risk:** This leads to code duplication and makes adding new competition formats (e.g., double-elimination) extremely difficult, as it would require adding yet another major logic path throughout the codebase.

### 2.2. "Team" vs. "Player" Participants

The bot assumes that `teams` participate in leagues and `players` participate in cups.

-   **The Problem:** In reality, teams themselves don't play; *players on those teams* play matches. The current system cannot model a "team fixture" (e.g., Team A vs. Team B) as a collection of individual player-vs-player games.
-   **The Risk:** This is a critical misunderstanding of how a real-world snooker league operates. We cannot, for example, generate a fixture that says "Player 1 (Team A) vs. Player 3 (Team B)" and "Player 2 (Team A) vs. Player 4 (Team B)".

---

## 3. Proposed Architectural Changes

### 3.1. Unify Competition Formats

-   **Proposal:** We will eliminate the `type` ('league'/'cup') field from the `competitions` table.
-   **New Implementation:** We will replace it with a `format` field. This text field will describe the fixture generation method (e.g., `'round-robin'`, `'knockout'`). This makes the system data-driven and flexible.

### 3.2. Clarify Participant Roles & Fixtures

This is the most significant change, designed to accurately model how matches are played.

-   **Players and Teams:** The `players` table (with handicaps) and `teams` table will remain the master lists. The `players.team_id` link remains the source of truth for team affiliation.
-   **Competition Participants:** The `competition_participants` table will **always link to a Team ID**.
    -   For a team-based league, you add the teams as participants.
    -   For a singles/knockout cup, we will treat each player as a **"team of one"**. This may happen automatically behind the scenes to keep the data model consistent.
-   **New Fixture Structure:** The fixture system will be split into two levels: the high-level fixture and the individual games within it.
    1.  **`fixtures` Table:** This will represent the high-level pairing.
        -   `id`, `competition_id`, `stage_number` (e.g., 1, 2, 3), `team1_id`, `team2_id`, `is_complete`.
    2.  **NEW `fixture_matches` Table:** This will store the actual player-vs-player games that make up a single fixture from the table above.
        -   `id`, `fixture_id` (links to `fixtures.id`), `player1_id`, `player2_id`, `winner_id`.

This two-tiered system means a "fixture" between two teams can contain any number of individual "matches." For a singles cup, a fixture will simply contain one match.

---

## 4. Key Questions for the Client

Before we proceed with this refactoring, we need clear answers to the following questions to ensure the new architecture meets the exact requirements.

**Question 1: How are team-vs-team matches decided?**
> For a single fixture (e.g., "The Ship" vs "The Legion"), is the winner decided by one single frame, or is it a collection of individual player games (e.g., 3 players from each team play each other)? If it's the latter, how many players are in a standard match?

**Question 2: How should results be reported?**
> Should a user report the result for the entire team fixture (`!report winner "The Ship"`) or should they report the result of each individual player-vs-player game within that fixture (`!report winner @Player1 loser @Player3`)? The latter is more flexible but requires more input from users.

**Question 3: Is our "team of one" assumption for singles events correct?**
> For a knockout competition, is it correct to assume a participant is always a single, registered player? Is it acceptable to treat them as a "team of one" in the database to keep the system consistent?

**Question 4: How are handicaps applied in team matches?**
> Handicaps are currently attached to individual players. In a team match that consists of several player games, should the handicaps be applied to each game individually? Or is there a concept of a "team handicap"?

We await your feedback before proceeding with the implementation.
