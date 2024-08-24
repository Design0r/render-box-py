SELECT * 
FROM jobs 
WHERE id = (SELECT job_id FROM tasks WHERE id = ?);
