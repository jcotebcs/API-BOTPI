SELECT * FROM apis
WHERE (:cat IS NULL OR category = :cat)
AND (:auth IS NULL OR auth_type LIKE :auth)
AND (:free IS NULL OR pricing LIKE '%free%')
ORDER BY quality_score DESC, name ASC
LIMIT :limit OFFSET :offset;
