CREATE DATABASE IF NOT EXISTS economygame;
USE economygame;

CREATE TABLE IF NOT EXISTS UserData (
    UName    VARCHAR(15) PRIMARY KEY,
    DName    VARCHAR(15) NOT NULL,
    Password VARCHAR(20) NOT NULL
);

CREATE TABLE IF NOT EXISTS PlayerData (
    UName        VARCHAR(15) PRIMARY KEY,
    DName        VARCHAR(15) NOT NULL,
    Wallet       INT         NOT NULL DEFAULT 500,
    SecurityLvl  INT         NOT NULL DEFAULT 1,
    LuckLvl      INT         NOT NULL DEFAULT 1,
    BankBal      INT         NOT NULL DEFAULT 0,
    BankCap      INT         NOT NULL DEFAULT 1000,
    Job          VARCHAR(50) NOT NULL DEFAULT 'None',
    Intelligence FLOAT       NOT NULL DEFAULT 1.0,
    FOREIGN KEY (UName) REFERENCES UserData(UName) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS NotifsData (
    ID      INT AUTO_INCREMENT PRIMARY KEY,
    UName   VARCHAR(15)  NOT NULL,
    Type    VARCHAR(20)  NOT NULL,
    Message VARCHAR(255) NOT NULL,
    Sender  VARCHAR(15)  NOT NULL,
    INDEX (UName)
);
