## Initializing the database
CREATE DATABASE IF NOT EXISTS knowledge_base;
CREATE DATABASE IF NOT EXISTS incident;

## Uncomment and run if you want to drop tables
#DROP TABLE knowledge_base.kb;
#DROP TABLE incident.incidents;

CREATE TABLE IF NOT EXISTS knowledge_base.kb (
	number VARCHAR(20),
	version VARCHAR(10),
	short_description VARCHAR(255),
	author VARCHAR(100),
	category VARCHAR(100),
	workflow VARCHAR(20),
	updated DATETIME,
	PRIMARY KEY (number,updated)
);

CREATE TABLE IF NOT EXISTS incident.incidents (
	number VARCHAR(20),
	opened DATETIME,
	short_description VARCHAR(255),
	description TEXT,
	resolution_code VARCHAR(50) NULL,
	resolution_notes VARCHAR(255)NULL,
	state ENUM(
		'New',
		'Closed',
		'In Progress',
		'On Hold'
	),
	assigned_to VARCHAR(50) NULL,
	PRIMARY KEY (number,opened)
);

## Importing excel files(knowledge)
LOAD DATA INFILE '/var/lib/mysql-files/published_kb_knowledge.csv'
INTO TABLE knowledge_base.kb
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS 
(number,version,short_description,author,category,workflow,updated);

## Importing excel files(incident)
LOAD DATA INFILE '/var/lib/mysql-files/incident.csv'
INTO TABLE incident.incidents
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS 
(number,opened,short_description,description,resolution_code,resolution_notes,state,assigned_to);