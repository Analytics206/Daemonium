# Daemonium Data Schema

## Postgresql
### Tables

#### tags
- id
- name

#### books
- id
- title
- author
- year
- publisher
- isbn
- summary
- content
- created_at
- updated_at

#### philosophers
- id
- name
- summary
- content
- dob
- dod
- school_id
- tag_id
- created_at
- updated_at

#### schools
- id
- name
- tag_id

#### philosopher_books
- id
- philosopher_id
- book_id
- tag_id

#### school_books
- id
- school_id
- book_id
- tag_id

#### philosopher_keywords
- id
- philosopher_id
- keyword_id

#### school_keywords
- id
- school_id
- keyword_id

#### book_keywords
- id
- book_id
- keyword_id

#### keywords
- id
- name
- tag_id

#### philosophers_keywords
- id
- philosopher_id
- keyword_id

#### schools_keywords
- id
- school_id
- keyword_id
### Views

#### qdrant_tags
- id
- name
- 

-----

## MongoDB

### Collections

#### aphorisms

#### bibliography

#### book_summary

#### books

#### chat_blueprint

#### conversation_logic

#### discussion_hook

#### idea_summary

#### modern_adaptation

#### persona_core

#### philosopher_bio

#### philosopher_bot

#### philosopher_summary

#### philosophers

#### philosophy_keywords

#### philosophy_school

#### philosophy_themes

#### top_10_ideas

------

## Neo4j

### Nodes

#### books

#### philosophers

#### schools

### Relationships

#### philosopher_books

#### school_books

#### philosopher_keywords

#### school_keywords

#### book_keywords

#### keywords
------
## Qdrant

### Collections

#### books

#### philosophers

#### schools

#### philosopher_books

#### school_books

#### philosopher_keywords

#### school_keywords

#### book_keywords

#### keywords   
