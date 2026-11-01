CREATE TABLE audit (
	id INTEGER NOT NULL, 
	actor VARCHAR(100) NOT NULL, 
	action VARCHAR(60) NOT NULL, 
	target VARCHAR(100) NOT NULL, 
	ip VARCHAR(80) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE leagues (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	code VARCHAR(12) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	UNIQUE (code)
);

CREATE TABLE rate_buckets (
	"key" VARCHAR(100) NOT NULL, 
	count INTEGER NOT NULL, 
	started DATETIME NOT NULL, 
	PRIMARY KEY ("key")
);

CREATE TABLE settings (
	"key" VARCHAR(60) NOT NULL, 
	value TEXT NOT NULL, 
	PRIMARY KEY ("key")
);

CREATE TABLE users (
	id INTEGER NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	username VARCHAR(30) NOT NULL, 
	password_hash VARCHAR(100) NOT NULL, 
	role VARCHAR(10) NOT NULL, 
	suspended BOOLEAN NOT NULL, 
	must_change BOOLEAN NOT NULL, 
	version INTEGER NOT NULL, 
	locked_until DATETIME, 
	failed INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	last_active DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (role IN ('ADMIN','USER')), 
	UNIQUE (email), 
	UNIQUE (username)
);

CREATE TABLE resets (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	digest VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	used BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	UNIQUE (digest)
);

CREATE TABLE sessions (
	id VARCHAR(64) NOT NULL, 
	user_id INTEGER NOT NULL, 
	csrf VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	revoked BOOLEAN NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

CREATE TABLE teams (
	id INTEGER NOT NULL, 
	name VARCHAR(100) NOT NULL, 
	league_id INTEGER NOT NULL, 
	external_id INTEGER, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(league_id) REFERENCES leagues (id) ON DELETE RESTRICT, 
	UNIQUE (external_id)
);

CREATE TABLE favorites (
	user_id INTEGER NOT NULL, 
	team_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, team_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(team_id) REFERENCES teams (id) ON DELETE CASCADE
);

CREATE TABLE matches (
	id INTEGER NOT NULL, 
	external_id INTEGER, 
	league_id INTEGER NOT NULL, 
	home_id INTEGER NOT NULL, 
	away_id INTEGER NOT NULL, 
	kickoff DATETIME NOT NULL, 
	status VARCHAR(16) NOT NULL, 
	home_goals INTEGER, 
	away_goals INTEGER, 
	source VARCHAR(20) NOT NULL, 
	PRIMARY KEY (id), 
	CHECK (home_id != away_id), 
	CHECK (status IN ('SCHEDULED','FINISHED','POSTPONED','CANCELLED')), 
	UNIQUE (external_id), 
	FOREIGN KEY(league_id) REFERENCES leagues (id) ON DELETE RESTRICT, 
	FOREIGN KEY(home_id) REFERENCES teams (id) ON DELETE RESTRICT, 
	FOREIGN KEY(away_id) REFERENCES teams (id) ON DELETE RESTRICT
);

CREATE TABLE follows (
	user_id INTEGER NOT NULL, 
	match_id INTEGER NOT NULL, 
	PRIMARY KEY (user_id, match_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE
);

CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	match_id INTEGER NOT NULL, 
	text VARCHAR(300) NOT NULL, 
	read BOOLEAN NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, match_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE
);

CREATE TABLE picks (
	id INTEGER NOT NULL, 
	user_id INTEGER NOT NULL, 
	match_id INTEGER NOT NULL, 
	outcome VARCHAR(4) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, match_id), 
	CHECK (outcome IN ('Home','Draw','Away')), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE
);

CREATE TABLE predictions (
	id INTEGER NOT NULL, 
	match_id INTEGER NOT NULL, 
	payload TEXT NOT NULL, 
	created_at DATETIME NOT NULL, 
	model_version VARCHAR(80) NOT NULL, 
	eligible BOOLEAN NOT NULL, 
	correct BOOLEAN, 
	brier FLOAT, 
	PRIMARY KEY (id), 
	UNIQUE (match_id), 
	FOREIGN KEY(match_id) REFERENCES matches (id) ON DELETE CASCADE
);
