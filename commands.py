"""In-game commands (port of commands.cpp / commands.h)."""

import random

from utility import (
    CYAN, GREEN, RED, RESET, YELLOW,
    Player, send_notification, stoi,
)


def cmd_help():
    print(f"{CYAN}\n=== ECONOMY GAME - COMMANDS ==={RESET}")
    print(" help              - Show this help menu")
    print(" stats             - View your own stats")
    print(" stats <user>      - View another player's stats")
    print(" beg               - Beg for a small amount of money")
    print(" fish              - Go fishing to earn money")
    print(" rob <user>        - Attempt to rob another player")
    print(" deposit <amount>  - Deposit money into your bank")
    print(" withdraw <amount> - Withdraw money from your bank")
    print(" logout            - Log out")
    print(" exit              - Quit the game\n")


def cmd_stats(conn, current_player, target_user=""):
    is_self = target_user == "" or target_user == current_player.uname
    if is_self:
        current_player.display(True)
        return

    if not Player.exists(conn, target_user):
        print(f"{RED}Player '{target_user}' not found.{RESET}")
        return

    target = Player(conn, target_user)
    if not target.valid:
        print(f"{RED}Could not retrieve stats.{RESET}")
        return
    target.display(False)


def cmd_beg(conn, current_player):
    amount = random.randint(10, 100)
    lines = [
        "A kind stranger tossed you",
        "You sat on the sidewalk and earned",
        "Someone felt sorry for you and gave you",
        "A tourist dropped",
        "You held up a sign and collected",
    ]
    current_player.add_money(conn, amount)
    print(f"{GREEN}{random.choice(lines)} ${amount}!{RESET}")


def cmd_fish(conn, current_player):
    print("You cast your line into the water...")

    if random.randrange(100) < 40:
        fails = [
            "You caught an old boot. Not worth much.",
            "The fish outsmarted you. Nothing caught.",
            "Your line snapped. Better luck next time!",
            "You caught a plastic bag. Disappointing.",
        ]
        print(f"{YELLOW}{random.choice(fails)}{RESET}")
        return

    amount = random.randint(50, 300)
    catches = [
        "a fat salmon", "a massive tuna", "a rare golden carp",
        "a bunch of small trout", "a surprisingly meaty bass",
    ]
    current_player.add_money(conn, amount)
    print(f"{GREEN}You caught {random.choice(catches)} and sold it for ${amount}!{RESET}")


def cmd_rob(conn, current_player, target_user=""):
    if not target_user:
        print(f"{RED}Usage: rob <username>{RESET}")
        return
    if target_user == current_player.uname:
        print(f"{RED}You can't rob yourself!{RESET}")
        return
    if not Player.exists(conn, target_user):
        print(f"{RED}Player '{target_user}' not found.{RESET}")
        return

    target = Player(conn, target_user)
    if not target.valid:
        print(f"{RED}Something went wrong.{RESET}")
        return

    if target.wallet <= 0:
        print(f"{YELLOW}{target.dname}'s wallet is empty. Nothing to steal!{RESET}")
        return

    success_chance = max(10, 65 - target.security_lvl * 10)

    print(f"You sneak towards {target.dname}'s wallet...")

    if random.randrange(100) < success_chance:
        stolen = (target.wallet * random.randint(20, 50)) // 100
        if stolen < 1:
            stolen = 1

        target.remove_money(conn, stolen)
        current_player.add_money(conn, stolen)

        print(f"{GREEN}Success! You robbed {target.dname} and got away with ${stolen}!{RESET}")

        send_notification(
            conn, target_user, "ROB",
            f"{current_player.dname} robbed you and stole ${stolen} from your wallet!",
            current_player.uname,
        )
    else:
        penalty = random.randint(25, 100)
        if penalty > current_player.wallet:
            penalty = current_player.wallet

        print(f"{RED}You got caught! {target.dname}'s security spotted you!{RESET}")

        if penalty > 0:
            current_player.remove_money(conn, penalty)
            print(f"{RED}You were fined ${penalty} as punishment.{RESET}")
        else:
            print(f"{RED}Luckily you had no money to be fined.{RESET}")

        send_notification(
            conn, target_user, "ROB",
            f"{current_player.dname} tried to rob you but got caught! Your security held up.",
            current_player.uname,
        )


def _parse_amount(amount_str, usage):
    """Shared validation for deposit/withdraw. Returns an int or None."""
    if not amount_str:
        print(f"{RED}Usage: {usage}{RESET}")
        return None
    try:
        amount = stoi(amount_str)
    except ValueError:
        print(f"{RED}Invalid amount.{RESET}")
        return None
    if amount <= 0:
        print(f"{RED}Amount must be greater than 0.{RESET}")
        return None
    return amount


def _print_balances(p):
    print(f" Wallet : ${p.wallet}")
    print(f" Bank   : ${p.bank_bal} / ${p.bank_cap}")


def cmd_deposit(conn, current_player, amount_str=""):
    amount = _parse_amount(amount_str, "deposit <amount>")
    if amount is None:
        return
    if current_player.deposit(conn, amount):
        print(f"{GREEN}Deposited into your bank.{RESET}")
        _print_balances(current_player)


def cmd_withdraw(conn, current_player, amount_str=""):
    amount = _parse_amount(amount_str, "withdraw <amount>")
    if amount is None:
        return
    if current_player.withdraw(conn, amount):
        print(f"{GREEN}Withdrew from your bank.{RESET}")
        _print_balances(current_player)
