# nk2dl
Nuke to Deadline. A toolset for submitting nukescripts to Thinkbox Deadline in a "big studio" manner.


from nk2dl.nuke import submit_nuke_script

# Basic usage
job_id = submit_nuke_script("/path/to/script.nk")

# Advanced usage with options
job_id = submit_nuke_script(
    "/path/to/script.nk",
    frame_range="1-100",
    priority=75,
    use_nuke_x=True,
    render_threads=16,
    use_gpu=True
)