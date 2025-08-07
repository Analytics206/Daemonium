# Orchestrator Dev Notes
- Creating master orchestrator dataset from all philosophers in node.js docker instance
- Storing data in redis as master_orchestrator and master_orchestrator_active for use of all philosopher chat bot instances
- Philosophers dataset is master join for all philosophers by "author", except except philosophy_school join by school_id from philosophers 
- All philosophers should be pulled but 'is_active_chat' should be checked for active chat philosophers
- Data should be stacked
- Datasets 
    - philosophers
    - aphorisms
        '''json
        {
            "success": true,
            "message": "string",
            "timestamp": "2025-08-07T18:42:42.919Z",
            "data": {
                "_id": "string",
                "author": "string",
                "category": "string",
                "text": "string",
                "aphorisms": {
                "additionalProp1": [
                    "string"
                ],
                "additionalProp2": [
                    "string"
                ],
                "additionalProp3": [
                    "string"
                ]
                },
                "source": "string",
                "context": "string",
                "themes": [
                "string"
                ],
                "interpretation": "string"
            },
            "total_count": 0
        }
        '''
    - bibliography
        '''json

        '''
    - book_summary
    - conversation_logic
    - discussion_hook
    - idea_summary
    - modern_adaptation
    - persona_core
    - philosopher_summary
    - philosophy_school
    - philosophy_themes
    - top_10_ideas

Dev Steps:
- [ ] pulling required API endpoints
- [ ] combine required data for master_orchestrator dataset
- [ ] data should be stacked using philosophers dataset as master
- [ ] if dataset is not availble for data joined to philosophers, use nulls
- [ ] data should be combined for two master_orchestrator datasets, is_active_chat = 0 or is_active_chat = 1
- [ ] 2 datasets named master_orchestrator and master_orchestrator_active
- [ ] master_orchestrator and master_orchestrator_active dataset:
    - philosophers
    - aphorisms
    - bibliography
    - book_summary
    - chat_blueprint - is a single dataset that is not joined by key, should be joined to each philosopher
    - conversation_logic
    - discussion_hook
    - idea_summary
    - modern_adaptation
    - persona_core
    - philosopher_summary
    - philosophy_school
    - philosophy_themes
    - top_10_ideas
- [ ] if dataset is not availble for data joined to philosophers, use nulls
- [ ] create step to optional write data as json to file for dev review
- [ ] store data in redis as master_orchestrator and master_orchestrator_active for use of all philosopher chat bot instances
- [ ] create chat_blueprint_master dataset from:
    - chat_blueprint - master chat_blueprint collection is master dataset for all philosophers, doesn't join by any key
    - philosophers
    persona_core
- [ ] pull redis file for selected philosopher and create chat_orchestrator dataset
- [ ] chat_orchestrator dataset should include:
- [ ] store chat_orchestrator in redis for use of selected philosopher chat bot instance
- [ ] create step to optional write data as json to file for dev review
- [ ] create chat_orchestrator instance for selected philosopher in-memory
- [ ] create step to optional write data as json to file for dev review

## Chat Bot Notes
- [ ] chat should be able to use both Ollama local and OpenAI API. Easy to switch between them.
- [ ] Token use calculation should be implemented
- [ ] Token use should be stored in redis for each chat session and postgres for history

