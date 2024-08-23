UPDATE tasks
  SET 
      priority = ?,
      data = ?,
      state = ?,
      timestamp = ?
  WHERE 
      id = ?;
