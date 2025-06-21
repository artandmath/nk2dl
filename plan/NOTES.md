Missing CLI Arguments to Add:
--UseParser - Flag to use parser instead of Nuke API
--SortWritesAlphabetically - Flag to sort write nodes alphabetically
--CopyScript - Flag to enable script copying
--CopyScriptPath - Full file path template for copied script (includes directory and filename, supports multiple paths)
--SubmitCopiedScript - Flag to submit copied script instead of original
--SubmitScriptAsAuxFile - Flag to submit script as auxiliary file (correcting existing implementation)
--BuildJob - Flag to submit as a build job
--BuildJobScriptPath - Path for build job script
--Environment - Environment variables to include

-
Parameter Type Handling to Improve:
Add support for write node configuration dictionaries in CLI
Add better support for graph scope variable formats
Fix handle_submit Function:
Update to properly handle the list of job dictionaries returned from submit_nuke_script
Based on this analysis, the CLI module needs to be updated to be fully compatible with the current submission.py functionality.




# pytest
    python -m pytest nk2dl/tests/ -v


$env:PYTHONPATH = "C:/Users/Daniel/Documents/repo/nk2dl"

# other tests

$env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
$env:NK2DL_DEADLINE_HOST = "192.168.1.18"
$env:NK2DL_DEADLINE_PORT = "4434"
$env:NK2DL_DEADLINE_SSL = "True"
$env:NK2DL_DEADLINE_SSL_CERT = "C:/Users/Daniel/Documents/repo/nk2dl/.ignore/webservice_certs/ca.crt"C:/Users/Daniel/Documents/repo/nk2dl/.ignore/webservice_certs/ca.crt"

python scripts/test_deadline_connection.py



$env:NK2DL_DEADLINE_USE__WEB__SERVICE = "True"
$env:NK2DL_DEADLINE_HOST = "192.168.1.18"
$env:NK2DL_DEADLINE_PORT = "8081"
$env:NK2DL_DEADLINE_SSL = "False"

python scripts/test_deadline_connection.py


from nk2dl.nuke import submit_nuke_script
job_id = submit_nuke_script(
    "C:/Users/Daniel/Documents/repo/nk2dl/examples/renderWithDeadline.nk",
    script_path_same_as_current_nuke_session=True,
    frame_range="input",
    chunk_size=50,
    priority=75,
    render_order_dependencies=True,
    write_nodes=["Write1","Write2","Write3","Write4","Write5"],
    use_nodes_frame_list=True,
    continue_on_error=True
)

from nk2dl.nuke import submit_nuke_script
job_id = submit_nuke_script(
    "C:/Users/Daniel/Desktop/deadlineManyWriteExample.nk",
    frame_range="input",
    chunk_size=100,
    priority=75,
    use_nuke_x=True,
    use_gpu=True,
    render_order_dependencies=True,
    use_nodes_frame_list=True,
    continue_on_error=True
)

python -m nk2dl submit `
  "C:/Users/Daniel/Documents/repo/nk2dl/examples/renderWithDeadline.nk" `
  --Frames input `
  --FramesPerTask 50 `
  --Priority 75 `
  --UseNukeX `
  --RenderThreads 16 `
  --UseGPU `
  --RenderOrderDependencies `
  --WriteNodes Write1,Write2,Write3,Write4,Write5 `
  --NodeFrameRange `
  --ContinueOnError `
  --Var "shotcode:ABC_0010,ABC_0020"

from nk2dl.nuke import submit_nuke_script
job_id = submit_nuke_script(
    "C:/Users/Daniel/Documents/repo/nk2dl/examples/renderWithDeadline.nk",
    frame_range="input",
    chunk_size=50,
    priority=75,
    use_nuke_x=True,
    render_threads=16,
    use_gpu=True,
    write_nodes_as_separate_jobs=True,
    render_order_dependencies=True,
    write_nodes=["Write1","Write2","Write3","Write4","Write5","Write6"],
    use_nodes_frame_list=True,
    continue_on_error=True, 
    graph_scope_variables=["shotcode:ABC_0010,ABC_0020"]
)

from nk2dl.nuke import submit_nuke_script
job_id = submit_nuke_script(
    "X:/RUR/prd/shots/086/086_0000/cmp/RURcomp/nuke/scenes/086_0000_cmp_SequenceOverview_v001.nk",
    frame_range="input",
    concurrent_tasks=5,
    chunk_size=50,
    priority=75,
    use_nuke_x=False,
    use_gpu=False,
    write_nodes_as_separate_jobs=True,
    render_order_dependencies=True,
    use_nodes_frame_list=True,
    continue_on_error=True,
    nuke_version=15.1
)


from nk2dl.nuke import submit_nuke_script
job_id = submit_nuke_script(
    "C:/Users/Daniel/Documents/repo/nk2dl/examples/renderWithDeadline.nk",
    frame_range="1-100",
    chunk_size=50,
    priority=75,
    use_nuke_x=True,
    render_threads=16,
    use_gpu=True,
    write_nodes=["Write1","Write2","Write3"],
    write_nodes_as_tasks=True,
    use_nodes_frame_list=True
)