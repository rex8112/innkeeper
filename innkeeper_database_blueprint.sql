/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8 */;
/*!50503 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

CREATE DATABASE IF NOT EXISTS `innkeeper` /*!40100 DEFAULT CHARACTER SET utf8mb3 */;
USE `innkeeper`;

CREATE TABLE IF NOT EXISTS `adventurers` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `userID` int(11) NOT NULL,
  `name` tinytext DEFAULT NULL,
  `level` tinyint(4) NOT NULL DEFAULT 1,
  `xp` int(11) NOT NULL DEFAULT 0,
  `class` tinytext DEFAULT NULL,
  `race` tinytext DEFAULT NULL,
  `attributes` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`attributes`)),
  `skills` text NOT NULL,
  `equipment` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`equipment`)),
  `inventory` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`inventory`)),
  `available` tinyint(4) NOT NULL DEFAULT 0,
  `health` int(11) NOT NULL DEFAULT 0,
  `home` int(11) NOT NULL DEFAULT 0,
  PRIMARY KEY (`index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `equipment` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `blueprint` int(11) NOT NULL DEFAULT 0,
  `level` int(11) NOT NULL DEFAULT 1,
  `startingMods` text NOT NULL,
  `randomMods` text DEFAULT NULL,
  PRIMARY KEY (`index`),
  KEY `blueprint` (`blueprint`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `quests` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `adventurer` int(11) NOT NULL,
  `active` tinyint(4) NOT NULL DEFAULT 1,
  `stage` int(11) NOT NULL DEFAULT 1,
  `stages` int(11) NOT NULL,
  `enemies` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`enemies`)),
  `loot` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`loot`)),
  `time` datetime NOT NULL,
  `xp` int(11) NOT NULL DEFAULT 1,
  `combatInfo` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`index`),
  KEY `adventurer` (`adventurer`),
  CONSTRAINT `adventurer` FOREIGN KEY (`adventurer`) REFERENCES `adventurers` (`index`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `raid` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `adventurers` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`adventurers`)),
  `boss` int(11) NOT NULL DEFAULT 0,
  `loot` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`loot`)),
  `completed` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `raidchannels` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `channelID` int(11) NOT NULL,
  `guildID` int(11) NOT NULL,
  `adventurers` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`adventurers`)),
  PRIMARY KEY (`index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `servers` (
  `index` int(11) NOT NULL,
  `name` varchar(50) DEFAULT '',
  `owner` int(11) NOT NULL,
  `type` varchar(50) DEFAULT NULL,
  `category` int(11) DEFAULT NULL,
  `announcement` int(11) DEFAULT NULL,
  `general` int(11) DEFAULT NULL,
  `command` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`command`)),
  `adventureRole` int(11) DEFAULT NULL,
  `travelRole` int(11) DEFAULT NULL,
  `onjoin` tinyint(4) NOT NULL DEFAULT 0,
  PRIMARY KEY (`index`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `shop` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `adventurer` int(11) NOT NULL,
  `inventory` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`inventory`)),
  `buyback` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`buyback`)),
  `refresh` datetime NOT NULL,
  PRIMARY KEY (`index`),
  KEY `adventurer` (`adventurer`),
  CONSTRAINT `FK_shop_adventurers` FOREIGN KEY (`adventurer`) REFERENCES `adventurers` (`index`) ON DELETE NO ACTION ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `storage` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `adventurer` int(11) NOT NULL,
  `slots` int(11) NOT NULL DEFAULT 10,
  `inventory` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`inventory`)),
  PRIMARY KEY (`index`),
  KEY `adventurer` (`adventurer`),
  CONSTRAINT `FK__adventurers` FOREIGN KEY (`adventurer`) REFERENCES `adventurers` (`index`) ON DELETE CASCADE ON UPDATE NO ACTION
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

CREATE TABLE IF NOT EXISTS `trade` (
  `index` int(11) NOT NULL AUTO_INCREMENT,
  `adventurer1` int(11) NOT NULL,
  `adventurer2` int(11) NOT NULL,
  `money1` int(11) NOT NULL DEFAULT 0,
  `money2` int(11) NOT NULL DEFAULT 0,
  `inventory1` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`inventory1`)),
  `inventory2` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin NOT NULL CHECK (json_valid(`inventory2`)),
  `confirm1` tinyint(4) NOT NULL DEFAULT 0,
  `confirm2` tinyint(4) NOT NULL DEFAULT 0,
  `waitingOn` tinyint(4) NOT NULL DEFAULT 1,
  `active` tinyint(4) NOT NULL DEFAULT 1,
  PRIMARY KEY (`index`),
  KEY `adventurers1` (`adventurer1`),
  KEY `adventurers2` (`adventurer2`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb3;

/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
