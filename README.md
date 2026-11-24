# Multinomy (Python port)

A multiplayer economy based CLI-game, ported from C++ to Python.

## Setup

1. Install MySQL Server and create the tables:
   ```
   mysql -u root -p < schema.sql
   ```
2. Install the dependency:
   ```
   pip install -r requirements.txt
   ```
3. Edit `database.txt` (one value per line: host, port, user, password, database name).
4. Run:
   ```
   python main.py
   ```

## Commands

`help`, `stats [user]`, `beg`, `fish`, `rob <user>`, `deposit <amt>`, `withdraw <amt>`, `logout`, `exit`
