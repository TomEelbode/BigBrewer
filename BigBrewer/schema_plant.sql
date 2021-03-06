DROP TABLE IF EXISTS plant;
DROP TABLE IF EXISTS status;

CREATE TABLE plant (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  dev_id TEXT UNIQUE NOT NULL,
  plantname TEXT NOT NULL,
  location TEXT NOT NULL,
  color TEST UNIQUE NOT NULL
);

CREATE TABLE status (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plant_id INTEGER NOT NULL,
  received TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  date_tx DATETIME NOT NULL,
  water INTEGER NOT NULL,
  voltage INTEGER NOT NULL,
  FOREIGN KEY (plant_id) REFERENCES plant (id) ON DELETE CASCADE
);