UPDATE jobs
  SET 
      priority = ?,
      name = ?,
      state = ?,
      timestamp = ?
  WHERE 
      id = ?;
