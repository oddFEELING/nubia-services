### Details of What I Did

- I created a directory called writer under src/agents dirctory for the story writing agent.
  
- base.py and types.py files were created for the story writing agent in the writer directory.
  
- The agent will need analysis_id and story_id as dependencies, that can be found in types.py file.
  
- New files get_analysis_messages.py, file_parser.py, and story_details.py have been created in the tools directory, it contains function to fetch analysis messages, extract text from pdf files and fetch story details from the database respectively.
  
- Tools get_project_files, extract_text_from_pdf, get_csv_summary and get_analysis_conversation_summary() have been made available to the story agent.
  
- I added a section called "writer" to the prompts.toml file, this template is used by the story writing agent.
  
- A new route /story/chat has been added to the agent_router.py file to serve as an API endpoint for the story writing agent.

- Concise system and user prompts have been used in the implementation.

Thank You
  