// Number of events that a user is associated with.

MATCH 
(user:Agent)-[:wasAssociatedWith]-(event:Activity)
WHERE 
event.`prov:type` = "commit_event" OR 
event.`prov:type` = "issue_event" OR 
event.`prov:type` = "merge_request_event"
RETURN 
user.name, COUNT(DISTINCT event) as event_count
ORDER BY event_count DESC
