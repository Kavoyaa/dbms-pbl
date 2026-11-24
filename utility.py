"""Database connection, notifications and the Player model (port of utility.cpp / utility.h)."""

import os
import re
import sys

import mysql.connector
from mysql.connector import Error as MySQLError

# --------------------------------------------------------------------------
# ANSI colours
# --------------------------------------------------------------------------
RESET = "\033[0m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"

if os.name == "nt":
    os.system("")  # enables ANSI escape processing in the Windows console

# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------
_INT_RE = re.compile(r"\s*([+-]?\d+)")
_INT_MIN, _INT_MAX = -(2**31), 2**31 - 1


def stoi(text):
    """Behaves like C++ std::stoi: parses a leading integer, raises ValueError otherwise."""
    m = _INT_RE.match(text)
    if not m:
        raise ValueError(f"invalid integer: {text!r}")
    value = int(m.group(1))
    if not _INT_MIN <= value <= _INT_MAX:
        raise ValueError("integer out of range")
    return value


def _safe_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _fetch_all(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        return cur.fetchall()
    finally:
        cur.close()


def _execute(conn, sql, params=()):
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
    finally:
        cur.close()


# --------------------------------------------------------------------------
# Connect
# --------------------------------------------------------------------------
def connect_db(path="database.txt"):
    """Reads host / port / user / password / dbname (one per line) and connects."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.rstrip("\r\n") for line in f.readlines()]
    except OSError:
        print(f"{RED}Could not open {path}{RESET}", file=sys.stderr)
        return None

    lines += [""] * (5 - len(lines))
    host, port_str, user, password, dbname = lines[:5]

    if not (host and port_str and user and password and dbname):
        print(f"{RED}{path} is missing one or more fields.{RESET}", file=sys.stderr)
        return None

    try:
        port = stoi(port_str)
    except ValueError:
        print(f"{RED}Invalid port in {path}{RESET}", file=sys.stderr)
        return None

    try:
        conn = mysql.connector.connect(
            host=host, port=port, user=user, password=password, database=dbname
        )
    except MySQLError as e:
        print(f"{RED}Connection failed: {e}{RESET}", file=sys.stderr)
        return None

    conn.autocommit = True
    return conn


# --------------------------------------------------------------------------
# Notifications
# --------------------------------------------------------------------------
def send_notification(conn, to_user, ntype, message, sender):
    try:
        _execute(
            conn,
            "INSERT INTO NotifsData (UName, Type, Message, Sender) VALUES (%s, %s, %s, %s)",
            (to_user, ntype, message, sender),
        )
    except MySQLError:
        pass


def check_notifications(conn, uname):
    try:
        rows = _fetch_all(
            conn, "SELECT Type, Message FROM NotifsData WHERE UName = %s", (uname,)
        )
    except MySQLError:
        return

    if not rows:
        return

    print(f"{YELLOW}\n[!] You have unread notifications:{RESET}")
    for ntype, message in rows:
        print(f"{YELLOW}  [{ntype if ntype else '?'}] {message if message else ''}{RESET}")
    print()

    try:
        _execute(conn, "DELETE FROM NotifsData WHERE UName = %s", (uname,))
    except MySQLError:
        pass


# --------------------------------------------------------------------------
# Player
# --------------------------------------------------------------------------
class Player:
    def __init__(self, conn=None, uname=None):
        self.uname = ""
        self.dname = ""
        self.wallet = 0
        self.security_lvl = 1
        self.luck_lvl = 1
        self.bank_bal = 0
        self.bank_cap = 1000
        self.job = ""
        self.intelligence = 1.0
        self.valid = False

        if conn is not None and uname is not None:
            self._load(conn, uname)

    def _load(self, conn, uname):
        try:
            rows = _fetch_all(
                conn,
                "SELECT UName, DName, Wallet, SecurityLvl, LuckLvl, BankBal, BankCap, Job, Intelligence "
                "FROM PlayerData WHERE UName = %s",
                (uname,),
            )
        except MySQLError:
            return

        if rows:
            row = rows[0]
            self.uname = row[0] or ""
            self.dname = row[1] or ""
            self.wallet = _safe_int(row[2])
            self.security_lvl = _safe_int(row[3], 1)
            self.luck_lvl = _safe_int(row[4], 1)
            self.bank_bal = _safe_int(row[5])
            self.bank_cap = _safe_int(row[6], 1000)
            self.job = row[7] or "None"
            self.intelligence = _safe_float(row[8], 1.0)
            self.valid = True

    # ---- money ----------------------------------------------------------
    def add_money(self, conn, amount):
        try:
            _execute(
                conn,
                "UPDATE PlayerData SET Wallet = Wallet + %s WHERE UName = %s",
                (amount, self.uname),
            )
        except MySQLError as e:
            print(f"{RED}addMoney failed: {e}{RESET}", file=sys.stderr)
            return False
        self.wallet += amount
        return True

    def remove_money(self, conn, amount):
        try:
            _execute(
                conn,
                "UPDATE PlayerData SET Wallet = Wallet - %s WHERE UName = %s",
                (amount, self.uname),
            )
        except MySQLError as e:
            print(f"{RED}removeMoney failed: {e}{RESET}", file=sys.stderr)
            return False
        self.wallet -= amount
        return True

    def deposit(self, conn, amount):
        if amount > self.wallet:
            print(f"{RED}You don't have ${amount} in your wallet.{RESET}")
            return False

        space = self.bank_cap - self.bank_bal
        if space <= 0:
            print(f"{RED}Your bank is full! (Capacity: ${self.bank_cap}){RESET}")
            return False

        if amount > space:
            print(f"{YELLOW}Only ${space} space left. Depositing ${space} instead.{RESET}")
            amount = space

        try:
            _execute(
                conn,
                "UPDATE PlayerData SET Wallet = Wallet - %s, BankBal = BankBal + %s WHERE UName = %s",
                (amount, amount, self.uname),
            )
        except MySQLError as e:
            print(f"{RED}Deposit failed: {e}{RESET}", file=sys.stderr)
            return False

        self.wallet -= amount
        self.bank_bal += amount
        return True

    def withdraw(self, conn, amount):
        if amount > self.bank_bal:
            print(f"{RED}You only have ${self.bank_bal} in your bank.{RESET}")
            return False

        try:
            _execute(
                conn,
                "UPDATE PlayerData SET BankBal = BankBal - %s, Wallet = Wallet + %s WHERE UName = %s",
                (amount, amount, self.uname),
            )
        except MySQLError as e:
            print(f"{RED}Withdraw failed: {e}{RESET}", file=sys.stderr)
            return False

        self.bank_bal -= amount
        self.wallet += amount
        return True

    # ---- display --------------------------------------------------------
    def display(self, is_self):
        print(f"{CYAN}\n=== {self.dname}'s Stats ==={RESET}")
        print(f" Username     : {self.uname}")
        print(f" Display Name : {self.dname}")
        print(f" Job          : {self.job}")
        print(f"{GREEN} Wallet       : ${self.wallet}{RESET}")
        if is_self:
            print(f"{GREEN} Bank         : ${self.bank_bal} / ${self.bank_cap}{RESET}")
        print(f" Security Lvl : {self.security_lvl}")
        print(f" Luck Lvl     : {self.luck_lvl}")
        print(f" Intelligence : {self.intelligence:.1f}\n")

    # ---- auth (static) --------------------------------------------------
    @staticmethod
    def exists(conn, uname):
        try:
            return bool(
                _fetch_all(conn, "SELECT UName FROM UserData WHERE UName = %s", (uname,))
            )
        except MySQLError:
            return False

    @staticmethod
    def login(conn, uname, password):
        try:
            return bool(
                _fetch_all(
                    conn,
                    "SELECT UName FROM UserData WHERE UName = %s AND Password = %s",
                    (uname, password),
                )
            )
        except MySQLError:
            return False

    @staticmethod
    def register_player(conn, uname, dname, password):
        try:
            _execute(
                conn,
                "INSERT INTO UserData (UName, DName, Password) VALUES (%s, %s, %s)",
                (uname, dname, password),
            )
        except MySQLError as e:
            print(f"{RED}Register failed: {e}{RESET}", file=sys.stderr)
            return False

        try:
            _execute(
                conn,
                "INSERT INTO PlayerData "
                "(UName, DName, Wallet, SecurityLvl, LuckLvl, BankBal, BankCap, Job, Intelligence) "
                "VALUES (%s, %s, 500, 1, 1, 0, 1000, 'None', 1.0)",
                (uname, dname),
            )
        except MySQLError as e:
            print(f"{RED}PlayerData init failed: {e}{RESET}", file=sys.stderr)
            # don't leave a half-created account behind
            try:
                _execute(conn, "DELETE FROM UserData WHERE UName = %s", (uname,))
            except MySQLError:
                pass
            return False

        return True
