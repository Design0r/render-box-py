CREATE TABLE IF NOT EXISTS tasks(
    id VARCHAR(50) PRIMARY KEY,
    priority INTEGER NOT NULL,
    data TEXT,
    state VARCHAR(10),
    timestamp REAL NOT NULL
    );

CREATE TABLE IF NOT EXISTS workers(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(50) NOT NULL,
    metadata TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    state VARCHAR(10),
    task_id INTEGER,
    FOREIGN KEY(task_id) REFERENCES tasks(id)
    );
