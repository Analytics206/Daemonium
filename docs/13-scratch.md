# Daemonium Notes
- git config --global user.email "analytics206@gmail.com"
- docker-compose stop web-ui
- docker-compose up -d --build --force-recreate web-ui

- need to add keywords to all json files, keywords should include philosophical themes, ideas, and concepts
- need to create a philosophical master keyword list
- might need 2 prompts builders, started up and conversation
- start up might include random philosopher background such as country of origin, time period, age of when a book was written, or personal information about philosopher such as where they went to school, or what their main ideas were, or what their main works were, or ...
- should chat bot start the converstion with introduction to the philosopher or persona
- if startup with starting conversation, it can't be stale, not repetitive, it should be interesting and engaging
- conversation should be able to flow naturally, and be able to answer questions, and be able to provide information about the philosopher or persona
- conversation should be able to provide information about the philosopher or persona, and be able to answer questions about the philosopher or persona

- Connect firebase login to backend
- Pull firebase data into backend, store in redis and mongodb
- LoRa modelfile for chatbot 
- Change LLM input to use formatted data with System Prompt defined in modelfile
- Homepage philosophers connected to chat interface for philosopher selection
- Expand menu below Homepage Top 4 philosophers to include all Active philosophers
- User Active Philosopher selection on main page or drop down menu in chat interface
- Random option for philosopher selection
- Update System Prompt with select philosopher and related data
- Persona dataset build for selected philosopher
- Create Prompt injection for chatbot persona data
- Randomized introduction from selected philosopher to start conversation
- Topics selection drop down menu to use instead of philosophers selection drop down menu
- Topics with select a random philosopher related to topic selected
- Randomized introduction about topic from selected philosopher to start conversation