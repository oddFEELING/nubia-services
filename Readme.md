### Details of What I Did

- I created a directory called writer under src/agents dirctory for the story writing agent.
  
- base.py and types.py files were created for the story writing agent in the writer directory.
  
- I assumed the agent will need project_id and writer_id as dependencies, that can be found in types.py file.
  
- I also assumed that the agent will perform analysis and use the findings for story generation, most tools were adapted from AnalyserAgent.
  
- Check the base.py file for the correct database table and attributes that were used in set_loading_state and save_message methods.

- I added a section called "writer" to the prompts.toml file, this template is used by the story writing agent.
  
- Most of the code was adapted from AnalyserAgent.

Thank You
  