CREATE TABLE IF NOT EXISTS tasks(
    id VARCHAR(50) PRIMARY KEY,
    job_id INTEGER NOT NULL,
    priority INTEGER NOT NULL,
    data TEXT,
    state VARCHAR(10),
    timestamp REAL NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id)
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

CREATE TABLE IF NOT EXISTS jobs(
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    priority INTEGER NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    state VARCHAR(10)
    );
