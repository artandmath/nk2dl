- [X] Build Job features
    - [X] Check for pre/post script in the same location as the running file
    - [X] Fall back to submitted
- [ ] Support other kinds of writes: deepwrites, writegeo, precomp?
- [ ] Meta data upstream overrides
- [ ] Meta data config override
- [x] Implement ScriptJob feature
- [X] Simplify tokens
- [X] Reduce instances of name/path down to path: copyscript, job_build, others
- [ ] Create an installer for cli
- [ ] Realign feature set on CLI to NukeSubmission class
        Missing CLI Arguments to Add:
        [x] --UseParser - Flag to use parser instead of Nuke API
        [x] --SortWritesAlphabetically - Flag to sort write nodes alphabetically
        [x] --ScriptJob
        [x] --ScriptJopName
        [X] --CopyScript - Flag to enable script copying
        [X] --CopyScriptPath - Full file path template for copied script (includes directory and filename, supports multiple paths)
        [X] --SubmitCopiedScript - Flag to submit copied script instead of original
        [X] --SubmitScriptAsAuxFile - Flag to submit script as auxiliary file (correcting existing implementation)
        [x] --BuildJob - Flag to submit as a build job
        [x] --BuildJobScriptPath - Path for build job script
        --Environment - Environment variables to include
        Parameter Type Handling to Improve:
            Add support for write node configuration dictionaries in CLI
            Add better support for graph scope variable formats
            Fix handle_submit Function:
            Update to properly handle the list of job dictionaries returned from submit_nuke_script
            Based on this analysis, the CLI module needs to be updated to be fully compatible with the current submission.py functionality.
