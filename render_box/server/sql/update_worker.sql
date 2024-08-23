UPDATE workers
    SET 
        name = ?,
        state = ?,
        timestamp = ?,
        task_id = ?
    WHERE 
        id = ?;
