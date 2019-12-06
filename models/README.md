# PROV Models

## Commit Model
#### Commit Model - Add File
A commit adding a new file.  
![Adding Files](./pngs/commit_model_add.png)

#### Commit Model - Modify File
A commit modifying an existing file.  
![Commit modifying a file](./pngs/commit_model_modify.png)

#### Commit Model - Delete File
A commit deleting an existing file.  
![Commit deleting a file](./pngs/commit_model_delete.png)

#### Commit Model - Create Event
For each commit, create a commit entity to keep track of events that occur on commits.  
![Commit entity creation](./pngs/commit_model_event_create.png)

#### Commit Model - Update Event
Model for an event occuring on a commit entity.  
Events can be comments, reactions (AwardEmojis), label events, discussions, merge requests, etc.  
A list of events with their respective description will be added soon.
![Event on commit entity](./pngs/commit_model_event_update.png)
