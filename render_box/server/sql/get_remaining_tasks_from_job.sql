SELECT COUNT(*) AS remaining_count
FROM tasks
WHERE job_id = (SELECT job_id FROM tasks WHERE id = ?)
AND state = 'waiting';
