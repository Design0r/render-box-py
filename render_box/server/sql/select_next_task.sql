WITH selected_job AS (
    SELECT id
    FROM jobs
    WHERE priority = (
        SELECT MAX(priority)
        FROM jobs
        WHERE state IN ('progress','waiting')
    )
    AND state IN ('progress', 'waiting')
    ORDER BY timestamp ASC
    LIMIT 1
),
selected_task AS (
    SELECT id, job_id
    FROM tasks
    WHERE priority = (
        SELECT MAX(priority)
        FROM tasks
        WHERE state = 'waiting'
    )
    AND state = 'waiting'
    AND job_id = (SELECT id FROM selected_job)
    ORDER BY timestamp ASC
    LIMIT 1
)
UPDATE tasks
SET state = 'progress'
WHERE id = (SELECT id FROM selected_task)
RETURNING id, job_id, priority, data, state, timestamp;


