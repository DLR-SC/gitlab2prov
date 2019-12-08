# PROV Models

## Commit Model
#### Commit Model - Add File
A commit adding a new file.  
![Adding Files](./pngs/commit_model_add_file.png)

#### Commit Model - Modify File
A commit modifying an existing file.  
![Commit modifying a file](./pngs/commit_model_modify_file.png)

#### Commit Model - Delete File
A commit deleting an existing file.  
The commit only marks an existing file version entity as Invalidated.
It does not add an own file version entity.
![Commit deleting a file](./pngs/commit_model_delete_file.png)

#### Commit Model - New Commit
A commit entity and its creation relations.
![Commit entity creation](./pngs/commit_model_new_commit.png)

#### Commit Model - New Commit Event
A commit event occuring on a commit entity.
Events can be comments, reactions (AwardEmojis), label events, discussions, merge requests, etc.  
A list of events with their respective description will be added soon.
![Event on commit entity](./pngs/commit_model_new_commit_event.png)


## Issue Model
#### Issue Model - New Issue
A new Issue.
![A new Issue](./pngs/issue_model_new_issue.png)

#### Issue Model - New Issue Event
An issue event occuring on an issue entity.
![A new Issue Event](./pngs/issue_model_new_issue_event.png)

#### Issue Model - Issue Marked as Duplicate
An issue that got marked as a duplicate. 
Combined Model from New Issue Event and Issue Marked as Duplicate.
![Issue that got marked as a duplicate](./pngs/issue_model_marked_as_duplicate.png)
