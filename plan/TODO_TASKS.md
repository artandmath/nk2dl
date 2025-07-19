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
    - [x] render_settings_from_metadata
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] submit_suspended: bool = False,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] job_dependencies: Optional[str] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] continue_on_error: bool = False,
        - [x] UI compelete [x] Model complete [ ] Feature complete
  - [ ] Machine Settings:
  - [x] Extra Settings:
    - [x] submit_script_as_auxiliary_file: Optional[bool] = None
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] submission_is_build_job: bool = False
        - [x] UI compelete [x] Model complete [ ] Feature complete
     # Build job parameters
    - [x] build_job_name: Optional[str] = None 
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] pre_build_job_script: Optional[Union[str, List[str]]] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] post_build_job_script: Optional[Union[str, List[str]]] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] build_job_as_auxiliary_file: Optional[bool] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] delete_build_job_script: Optional[bool] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    # Script copying and submission parameters
    - [x] copy_script: Optional[bool] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] copy_script_path: Optional[Union[str, List[str], Dict[int, str]]] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] submit_copied_script: Optional[bool] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    # ScriptJob parameters
    - [x] script_job_script_path: Optional[str] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    # Job Info parameters
    - [x] extra_info: Optional[List[str]] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] on_job_complete: Optional[str] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] pre_job_script: Optional[str] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] post_job_script: Optional[str] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] pre_task_script: Optional[str] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] post_task_script: Optional[str] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    # Environment Variables parameters
    - [x] use_current_environment: bool = False,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] environment_keys: Optional[List[str]] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] environment: Optional[Dict[str, str]] = None,
        - [x] UI compelete [x] Model complete [ ] Feature complete
    - [x] omit_environment_keys: Optional[List[str]] = None):
        - [x] UI compelete [x] Model complete [ ] Feature complete

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
