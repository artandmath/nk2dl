Core
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 

Nuke Panel
- [ ] Have the panel always open up in same pane. Preferably the viewer
- [ ] Don't highlight blue the frames dialog unless in custom
- [ ] Populate the remainder of the gui widgets. Add the missing functionality available in nuke.submission.
  - [ ] Job Settings:
    - [ ] render_settings_from_metadata
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] submit_suspended: bool = False,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] job_dependencies: Optional[str] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] continue_on_error: bool = False,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
  - [ ] Machine Settings:
  - [ ] Extra Settings:
    - [ ] submit_script_as_auxiliary_file: Optional[bool] = None
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] submission_is_build_job: bool = False
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
     # Build job parameters
    - [ ] build_job_name: Optional[str] = None 
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] pre_build_job_script: Optional[Union[str, List[str]]] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] post_build_job_script: Optional[Union[str, List[str]]] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] build_job_as_auxiliary_file: Optional[bool] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] delete_build_job_script: Optional[bool] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    # Script copying and submission parameters
    - [ ] copy_script: Optional[bool] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] copy_script_path: Optional[Union[str, List[str], Dict[int, str]]] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] submit_copied_script: Optional[bool] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    # ScriptJob parameters
    - [ ] script_job_script_path: Optional[str] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    # Job Info parameters
    - [ ] extra_info: Optional[List[str]] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] on_job_complete: Optional[str] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] pre_job_script: Optional[str] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] post_job_script: Optional[str] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] pre_task_script: Optional[str] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] post_task_script: Optional[str] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    # Environment Variables parameters
    - [ ] use_current_environment: bool = False,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] environment_keys: Optional[List[str]] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] environment: Optional[Dict[str, str]] = None,
        - [ ] UI compelete [ ] Model complete [ ] Feature complete
    - [ ] omit_environment_keys: Optional[List[str]] = None):
        - [ ] UI compelete [ ] Model complete [ ] Feature complete

- [ ] Attached browse buttons to a UI
- [ ] Fix console font sizing (too small)
- [ ] Set internal console log level separate to external console log level
- [ ] Feature: metadata colouring in the node table
- [ ] Feature: stored cell value colouring in the node table (currently bolded)
- [ ] Feature: click node in table to jump ot node in graph
- [ ] Feature: node renaming from node table
- [ ] Feature: node re-ordering from node table
- [ ] Bug: lock the node filename
- [ ] Bug: adjust the columns dropdown menu indicator to look the same as nuke default indicator
- [ ] Bug: adjust the cell heading sort indicators to look the same as nuke default indicator
- [ ] Bug: right click to set settings to default should work anywhere in the panels
- [ ] Feature: right click to set to default should indicate what the deafult will be
- [ ] Feature: add "Extra Settings" wdigets to the node table
- [ ] Remove "group" from tooltips
- [ ] Implement the "Inside griups" feature to find write nodes inside groups
- [ ] Add an auto update option to the update button to update the cell table preriodically or when the panel becomes frontmost.
- [ ] Work on GSV feature

General
- [ ] Review what is a debug message and what is info.
- [ ] Logger always to stderr
- [ ] Use stout for any output that can be used by other software
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 

CLI
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 
- [ ] 
