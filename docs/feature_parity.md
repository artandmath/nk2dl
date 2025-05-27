`nk2dl` uses the Thinkbox Deadline Nuke plugin on the server side.

On the client side it replaces the Thinkbox Deadline Nuke Submitter.

## Feature Parity Table
`Plugin` and `Job Info` columns are the backend/server-side variables. `Thinkbox` and `nk2dl` columns are the frontend/client-side variables.

| Plugin Info | Job Info | Thinkbox | nk2dl | nk2dl per write overrides |
|-------------|----------|----------|-------|---------------------------|
| SceneFile | - | - | script_path | :x: |
| Version | - | - | nuke_version | :white_check_mark: |
| UseNukeX | - | useNukeX | use_nuke_x | :white_check_mark: |
| BatchMode | - | batchMode | batch_mode | :white_check_mark: |
| BatchModeIsMovie | - | batchModeIsMovie | *auto-detected* | :x: |
| ContinueOnError | - | continueOnError | continue_on_error | :white_check_mark: |
| EnforceRenderOrder | - | enforceRenderOrder | enforce_render_order | :white_check_mark: |
| RenderMode | - | renderMode | render_mode | :white_check_mark: |
| UseGpu | - | useGpu | use_gpu | :white_check_mark: |
| GpuOverride | - | chooseGpu | gpu_override | :white_check_mark: |
| Threads | - | threads | threads | :white_check_mark: |
| RamUse | - | memoryUsage | ram_use | :white_check_mark: |
| StackSize | - | stackSize | stack_size | :white_check_mark: |
| Views | - | views | views | :white_check_mark: |
| PerformanceProfiler | - | performanceProfiler | performance_profiler | :white_check_mark: |
| PerformanceProfilerDir | - | performanceProfilerPath | performance_profiler_path | :white_check_mark: |
| ReloadPlugins | - | reloadPlugin | reload_plugins | :white_check_mark: |
| WriteNodesAsSeparateJobs | - | separateJobs | write_nodes_as_separate_jobs | :x: |
| WriteNode | - | write_nodes | write_nodes | :x: |
| WriteNode{index} | - | *auto-generated* | *auto-generated* | :x: |
| WriteNode{index}StartFrame | - | *auto-generated* | *auto-generated* | :x: |
| WriteNode{index}EndFrame | - | *auto-generated* | *auto-generated* | :x: |
| GraphScopeVariables | - | - | graph_scope_variables | :x: |
| GraphScopeVariablesEnabled | - | - | *auto-generated* | :x: |
| OutputFilePath | - | - | output_file_path | :white_check_mark: |
| ScriptJob | - | scriptJob | script_job_script_path | :x: |
| ScriptFilename | - | scriptFilename | script_job_script_path | :x: |
| BuildJobsFilename | - | - | *if submission_is_build_job=True* | :x: |
| - | Name | jobName | job_name | :x: |
| - | Plugin | "Nuke" | "Nuke" | :x: |
| - | Frames | frameList | frames | :white_check_mark: |
| - | ChunkSize | chunkSize | chunk_size | :white_check_mark: |
| - | ConcurrentTasks | concurrentTasks | concurrent_tasks | :white_check_mark: |
| - | Pool | pool | pool | :white_check_mark: |
| - | Group | group | group | :white_check_mark: |
| - | Priority | priority | priority | :white_check_mark: |
| - | BatchName | batchName | batch_name | :white_check_mark: |
| - | Department | department | department | :white_check_mark: |
| - | UserName | - | user_name | :white_check_mark: |
| - | Comment | comment | comment | :white_check_mark: |
| - | ExtraInfo{index} | extraInfo{n} | extra_info | :x: |
| - | JobDependency{index} | dependencies | job_dependencies | :white_check_mark: |
| - | OutputFilename{index} | *auto-generated* | *auto-generated* | :x: |
| - | AuxiliaryFiles | - | *if submit_script_as_auxiliary_file=True* | :x: |
| - | OnJobComplete | onComplete | on_job_complete | :white_check_mark: |
| - | InitialStatus | submitSuspended | submit_suspended | :white_check_mark: |
| - | LimitGroups | limitGroups | limit_groups | :white_check_mark: |
| - | MachineLimit | machineLimit | machine_limit | :x: |
| - | Whitelist/Blacklist | isBlacklist/machineList | *implemnted as allow/deny lists* | :x: |
| - | TaskTimeoutSeconds | taskTimeout | task_timeout | :white_check_mark: |
| - | EnableAutoTimeout | autoTaskTimeout | enable_auto_timeout | :white_check_mark: |
| - | LimitConcurrentTasks | limitConcurrentTasks | limit_worker_tasks | :white_check_mark: |
| - | PreJobScript | - | pre_job_script | :white_check_mark: |
| - | PostJobScript | - | post_job_script | :white_check_mark: |
| - | PreTaskScript | - | pre_task_script | :white_check_mark: |
| - | PostTaskScript | - | post_task_script | :white_check_mark: |
| - | UseNodeFrameList | useNodeRange | use_node_frame_list | :x: |
| - | - | separateJobDependencies | render_order_dependencies | :x: |
| - | - | separateTasks | write_nodes_as_tasks | :x: |
| - | - | precompFirst | *no plans to implement* | :x: |
| - | - | precompOnly | *no plans to implement* | :x: |
| - | - | smartVectorOnly | *no plans to implement* | :x: |
| - | - | eddySimulateOnly | *no plans to implement* | :x: |
| - | - | draftTemplate | *no plans to implement* | :x: |
| - | - | draftUser | *no plans to implement* | :x: |
| - | - | draftEntity | *no plans to implement* | :x: |
| - | - | - | use_parser_instead_of_nuke | :x: |
| - | - | - | render_settings_from_metadata | :x: |
| - | - | - | proxy_args | :x: |
| - | - | - | copy_script | :x: |
| - | - | - | copy_script_path | :x: |
| - | - | - | submit_copied_script | :x: |
| - | - | - | script_is_current | :x: |
| - | - | - | submit_script_as_auxiliary_file | :x: |
| - | - | - | parse_output_paths_to_deadline | :x: |
| - | - | - | submit_writes_alphabetically | :x: |
| - | - | - | submit_writes_in_render_order | :x: |
| - | EnvironmentKeyValue{index} | - | *from environment settings* | :x: |
| - | - | - | use_current_environment | :x: |
| - | - | - | environment_keys | :x: |
| - | - | - | environment | :x: |
| - | - | - | omit_environment_keys | :x: |
| - | - | - | submission_is_build_job | :x: |
| - | - | - | build_job_script_path | :x: |
