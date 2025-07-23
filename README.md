# Reymond Bot

Reymond is a Discord bot for server management, rating systems, and a role-based banking system.  
It supports multilingual features and is highly customizable for each server.

---

## Features

- **Rating System:** Assign, remove, and view user ratings. See server leaderboards.
- **Banking System:** Virtual bank cards, balance checks, transfers, top-ups, blocking/unblocking, and more.
- **Role Management:** Define admin, banker, and citizen roles per server.
- **Multilingual:** Supports English and Russian (settable per server).
- **Embeds:** Most commands respond with rich Discord embeds.

---

## Commands

### General

| Command         | Description                                      |
|-----------------|--------------------------------------------------|
| `/echo <text>`  | Repeats your message in the channel.             |
| `/setlang <en/ru>` | Set the bot language for your server.         |

---

### Rating System

| Command                  | Description                                                        |
|--------------------------|--------------------------------------------------------------------|
| `/setuprating <role>`    | Set up the role whose members can be rated.                        |
| `/setupadmin <role>`     | Set up the admin role for managing ratings.                        |
| `/setup <rated_role> <admin_role>` | Set both rated and admin roles at once.                 |
| `/addrating <user> <amount>` | Add rating points to a user.                                  |
| `/rmrating <user> <amount>`  | Remove rating points from a user.                             |
| `/rating <user>`         | View a user's rating.                                              |
| `/top [page]`            | Show the top rated users (10 per page).                            |

**Rank-prefixed versions** (for multi-system support):  
`/rank_setuprating`, `/rank_setupadmin`, `/rank_setup`, `/rank_addrating`, `/rank_rmrating`, `/rank_rating`, `/rank_top`

---

### Banking System

| Command                                | Description                                                      |
|-----------------------------------------|------------------------------------------------------------------|
| `/bank_createcard <nickname>`           | Create a bank card (citizens only).                              |
| `/bank_mycard`                         | Show your card number and nickname.                              |
| `/bank_balance [card/nickname]`         | View your or another card's balance.                             |
| `/bank_transfer <amount> <to> [message]`| Transfer money to another card or nickname.                      |
| `/bank_topup <amount> <card/nickname>`  | Manage card finances (bankers only).                                    |
| `/bank_block <card/nickname>`           | Block a card (bankers only).                                     |
| `/bank_unlock <card/nickname>`          | Unlock a blocked card (bankers only).                            |
| `/bank_delete [card/nickname]`          | Delete a card (your own or, if banker, any card).                |
| `/bank_list`                            | List all cards (bankers only).                                   |
| `/bank_setroles <banker> <citizen>`     | Set banker and citizen roles for the banking system (admin only).|

---

## Role Setup

- **Admin Role:** Can manage ratings.
- **Banker Role:** Can manage all bank accounts.
- **Citizen Role:** Can create and use bank cards.

Set these roles using `/setupadmin`, `/setuprating`, `/setup`, or `/bank_setroles`.

---
