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
    frame_range="input",
    chunk_size=50,
    priority=75,
    use_nuke_x=True,
    render_threads=16,
    use_gpu=True,
    render_order_dependencies=True,
    write_nodes=["Write1","Write2","Write3","Write4","Write5"],
    use_nodes_frame_list=True,
    continue_on_error=True
)

from nk2dl.nuke import submit_nuke_script
job_id = submit_nuke_script(
    "C:/Users/Daniel/Documents/repo/nk2dl/examples/renderWithDeadline.nk",
    frame_range="input",
    chunk_size=50,
    priority=75,
    use_nuke_x=True,
    render_threads=16,
    use_gpu=True,
    render_order_dependencies=True,
    write_nodes=["Write1","Write2","Write3","Write4","Write5"],
    use_nodes_frame_list=True,
    continue_on_error=True,
    graph_scope_variables=["shotcode:ABC_0010,ABC_0020"]
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
    write_nodes=["Write1","Write2","Write3","Write4","Write5"],
    use_nodes_frame_list=True,
    continue_on_error=True,
    graph_scope_variables=["shotcode:ABC_0010,ABC_0020"]
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