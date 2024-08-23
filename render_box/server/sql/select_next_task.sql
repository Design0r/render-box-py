WITH selected_task AS (
    SELECT id, priority, data, state, timestamp
    FROM tasks
    WHERE priority = (
        SELECT MAX(priority)
        FROM tasks
        WHERE state = 'waiting'
    )
    AND state = 'waiting'
    ORDER BY timestamp ASC
    LIMIT 1
  )
UPDATE tasks
SET state = 'progress'
WHERE id = (SELECT id FROM selected_task)
RETURNING id, priority, data, 'progress', timestamp;            
