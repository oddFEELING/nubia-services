### Details of What I Did

- I created a directory called writer under src/agents dirctory for the story writing agent.
  
- base.py and types.py files were created for the story writing agent in the writer directory.
  
- The agent will need analysis_id and story_id as dependencies, that can be found in types.py file.
  
- New files get_analysis_messages.py, file_parser.py, and story_details.py have been created in the tools directory, it contains function to fetch analysis messages, extract text from pdf files and fetch story details from the database respectively.
  
- Tools get_project_files, extract_text_from_pdf, get_csv_summary and get_analysis_conversation_summary() have been made available to the story agent.
  
- I added a section called "writer" to the prompts.toml file, this template is used by the story writing agent.
  
- A new route /story/chat has been added to the agent_router.py file to serve as an API endpoint for the story writing agent.

- Concise system and user prompts have been used in the implementation.

### Mock Testing Details

- I first installed the pytest, pytest-mock, and pytest-asyncio packages to manage the testing process.
  
- I created pytest.ini file to setup some configurations for the testing environment
  
- All test files can be found in src/tests directory
  
- I run pytest -vs test_file_name.py command in the test directory to execute the tests
  
- I could have implemented a comprehensive testing but due to the project structure and the way dependencies were tightly shared it was difficult for me to run some tests. In the process of executing the test, I get errors that will require me to make changes to certain aspects of the code that were not implemented by me.
  
- You can replicate the errors by running test_agent_api.py and test_story_agent.py
  
- But I learned something new, testing with Pytest and the inbuilt unittest package.

### Live Demo

- To run a live demo, you will need to build with command: docker compose build and docker compose up
  
- Visit localhost:8000/docs for API documentation

Thank You
  