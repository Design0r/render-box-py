UPDATE jobs
SET state = 'completed'
WHERE id = (SELECT job_id FROM tasks WHERE id = ?);
