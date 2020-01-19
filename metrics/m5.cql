// Number of files that a user edited.

MATCH 
	(user:Agent)-[:wasAttributedTo]-(fileVersion:Entity),
	(fileVersion:Entity)-[:specializationOf]->(file:Entity)
WHERE 
	fileVersion.`prov:type` = "file_version" AND 
	file.`prov:type` = "file"
RETURN 
	user.name, COUNT(DISTINCT file) AS file_count
ORDER BY 
	file_count DESC
