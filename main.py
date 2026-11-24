"""Multinomy - a multiplayer economy based CLI game (port of main.cpp)."""

import sys

from commands import (
    cmd_beg, cmd_deposit, cmd_fish, cmd_help,
    cmd_rob, cmd_stats, cmd_withdraw,
)
from utility import (
    BOLD, CYAN, GREEN, RED, RESET, YELLOW,
    Player, check_notifications, connect_db,
)


def auth_menu(conn):
    """Loops until the user logs in or registers. Returns the Player."""
    while True:
        print(f"{CYAN}\n================================")
        print(" MULTINOMY GAME")
        print(f"================================{RESET}")
        print(" [1] Login")
        print(" [2] Register")
        print(" [3] Exit")

        try:
            choice = int(input("\nChoice: ").strip())
        except ValueError:
            print(f"{RED}Invalid choice.{RESET}")
            continue

        if choice == 1:
            uname = input("Username : ")
            password = input("Password : ")

            if Player.login(conn, uname, password):
                p = Player(conn, uname)
                print(f"{GREEN}\nWelcome back, {p.dname}!{RESET}")
                return p
            print(f"{RED}Incorrect username or password.{RESET}")

        elif choice == 2:
            uname = input("Username (max 15 chars, no spaces) : ")
            if not uname or len(uname) > 15:
                print(f"{RED}Invalid username.{RESET}")
                continue
            if " " in uname:
                print(f"{RED}No spaces in username.{RESET}")
                continue
            if Player.exists(conn, uname):
                print(f"{RED}Username already taken.{RESET}")
                continue

            dname = input("Display Name (max 15 chars) : ")
            if not dname or len(dname) > 15:
                print(f"{RED}Invalid display name.{RESET}")
                continue

            password = input("Password (max 20 chars) : ")
            if not password or len(password) > 20:
                print(f"{RED}Invalid password.{RESET}")
                continue

            if Player.register_player(conn, uname, dname, password):
                print(f"{GREEN}\nAccount created! You start with $500.\nWelcome, {dname}!{RESET}")
                return Player(conn, uname)
            print(f"{RED}Registration failed.{RESET}")

        elif choice == 3:
            print(f"{YELLOW}Goodbye!{RESET}")
            conn.close()
            sys.exit(0)

        else:
            print(f"{RED}Invalid choice.{RESET}")


def main():
    conn = connect_db()
    if conn is None:
        return 1

    try:
        player = auth_menu(conn)
        print(f"Type {BOLD}help{RESET} to see all commands.")

        while True:
            print(f"{CYAN}\n> {RESET}", end="", flush=True)
            line = input()
            tokens = line.split()
            if not tokens:
                continue

            cmd = tokens[0]
            arg = tokens[1] if len(tokens) > 1 else ""

            if cmd == "help":
                cmd_help()
            elif cmd == "stats":
                cmd_stats(conn, player, arg)
            elif cmd == "beg":
                cmd_beg(conn, player)
            elif cmd == "fish":
                cmd_fish(conn, player)
            elif cmd == "rob":
                cmd_rob(conn, player, arg)
            elif cmd == "deposit":
                cmd_deposit(conn, player, arg)
            elif cmd == "withdraw":
                cmd_withdraw(conn, player, arg)
            elif cmd == "logout":
                print(f"{YELLOW}Logged out.{RESET}")
                player = auth_menu(conn)
                print(f"Type {BOLD}help{RESET} to see all commands.")
            elif cmd in ("exit", "quit"):
                print(f"{YELLOW}Goodbye!{RESET}")
                break
            else:
                print(f"{RED}Unknown command '{cmd}'. Type 'help'.{RESET}")

            check_notifications(conn, player.uname)

    except (EOFError, KeyboardInterrupt):
        print(f"\n{YELLOW}Goodbye!{RESET}")
    finally:
        conn.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
