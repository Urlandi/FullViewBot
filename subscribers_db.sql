--
-- File generated with SQLiteStudio v3.0.2 on Ср май 3 00:10:52 2023
--
-- Text encoding used: UTF-8
--
PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: prefixes
DROP TABLE IF EXISTS prefixes;
CREATE TABLE prefixes (DUMP_TIME INTEGER (8) NOT NULL UNIQUE PRIMARY KEY, IPV4 TEXT (1024) NOT NULL, IPV6 TEXT (1024) NOT NULL)

-- Table: ases
DROP TABLE IF EXISTS ases;
CREATE TABLE ases (DUMP_TIME INTEGER (8) PRIMARY KEY UNIQUE NOT NULL, ASNV4 INTEGER (8), ASNV6 INTEGER (8), ASNV4_ONLY INTEGER (8), ASNV6_ONLY INTEGER (8), ASNV4_32 INTEGER (8), ASNV6_32 INTEGER (8), ASNV4_PREF TEXT (8192), ASNV6_PREF TEXT (8192))

-- Table: status
DROP TABLE IF EXISTS status;
CREATE TABLE status (DUMP_TIME INTEGER (8) UNIQUE NOT NULL PRIMARY KEY, IPV4_TEXT TEXT (1024) NOT NULL, IPV6_TEXT TEXT (1024) NOT NULL)

-- Table: subscribers
DROP TABLE IF EXISTS subscribers;
CREATE TABLE subscribers (subscriber_id DECIMAL (32) PRIMARY KEY UNIQUE NOT NULL, IPV4 BOOLEAN NOT NULL DEFAULT (1), IPV6 BOOLEAN DEFAULT (1) NOT NULL)

COMMIT TRANSACTION;
