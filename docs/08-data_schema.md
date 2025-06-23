# Daemonium Data Schema

## Postgres
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
- book_id
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

#### philosopher_books_view

#### school_books_view

#### philosopher_keywords_view

#### school_keywords_view

#### book_keywords_view

#### keywords_view

## MongoDB

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
