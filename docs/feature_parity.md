`nk2dl` uses the Thinkbox Deadline Nuke plugin on the server side.

On the client side it replaces the Thinkbox Deadline Nuke Submitter.

## Feature Parity Table
`Plugin` and `Job Info` columns are the backend/server-side variables. `Thinkbox` and `nk2dl` columns are the frontend/client-side variables.

| Plugin Info | Job Info | Thinkbox | nk2dl | nk2dl per write overrides |
|-------------|----------|----------|-------|---------------------------|
| SceneFile | - | - | script_path | NO |
| Version | - | - | nuke_version | YES |
| UseNukeX | - | useNukeX | use_nuke_x | YES |
| BatchMode | - | batchMode | batch_mode | YES |
| BatchModeIsMovie | - | batchModeIsMovie | *auto-detected* | NO |
| ContinueOnError | - | continueOnError | continue_on_error | YES |
| EnforceRenderOrder | - | enforceRenderOrder | enforce_render_order | YES |
| RenderMode | - | renderMode | render_mode | YES |
| UseGpu | - | useGpu | use_gpu | YES |
| GpuOverride | - | chooseGpu | gpu_override | YES |
| Threads | - | threads | threads | YES |
| RamUse | - | memoryUsage | ram_use | YES |
| StackSize | - | stackSize | stack_size | YES |
| Views | - | views | views | YES |
| PerformanceProfiler | - | performanceProfiler | performance_profiler | YES |
| PerformanceProfilerDir | - | performanceProfilerPath | performance_profiler_path | YES |
| ReloadPlugins | - | reloadPlugin | reload_plugins | YES |
| WriteNodesAsSeparateJobs | - | separateJobs | write_nodes_as_separate_jobs | NO |
| WriteNode | - | write_nodes | write_nodes | NO |
| WriteNode{index} | - | *auto-generated* | *auto-generated* | NO |
| WriteNode{index}StartFrame | - | *auto-generated* | *auto-generated* | NO |
| WriteNode{index}EndFrame | - | *auto-generated* | *auto-generated* | NO |
| GraphScopeVariables | - | - | graph_scope_variables | NO |
| GraphScopeVariablesEnabled | - | - | *auto-generated* | NO |
| OutputFilePath | - | - | output_file_path | YES |
| ScriptJob | - | scriptJob | script_job_script_path | NO |
| ScriptFilename | - | scriptFilename | script_job_script_path | NO |
| BuildJobsFilename | - | - | *if submission_is_build_job=True* | NO |
| - | Name | jobName | job_name | NO |
| - | Plugin | "Nuke" | "Nuke" | NO |
| - | Frames | frameList | frames | YES |
| - | ChunkSize | chunkSize | chunk_size | YES |
| - | ConcurrentTasks | concurrentTasks | concurrent_tasks | YES |
| - | Pool | pool | pool | YES |
| - | Group | group | group | YES |
| - | Priority | priority | priority | YES |
| - | BatchName | batchName | batch_name | YES |
| - | Department | department | department | YES |
| - | UserName | - | user_name | YES |
| - | Comment | comment | comment | YES |
| - | ExtraInfo{index} | extraInfo{n} | extra_info | NO |
| - | JobDependency{index} | dependencies | job_dependencies | YES |
| - | OutputFilename{index} | *auto-generated* | *auto-generated* | NO |
| - | AuxiliaryFiles | - | *if submit_script_as_auxiliary_file=True* | NO |
| - | OnJobComplete | onComplete | on_job_complete | YES |
| - | InitialStatus | submitSuspended | submit_suspended | YES |
| - | LimitGroups | limitGroups | limit_groups | YES |
| - | MachineLimit | machineLimit | machine_limit | NO |
| - | Whitelist/Blacklist | isBlacklist/machineList | *implemnted as allow/deny lists* | NO |
| - | TaskTimeoutSeconds | taskTimeout | task_timeout | YES |
| - | EnableAutoTimeout | autoTaskTimeout | enable_auto_timeout | YES |
| - | LimitConcurrentTasks | limitConcurrentTasks | limit_worker_tasks | YES |
| - | PreJobScript | - | pre_job_script | YES |
| - | PostJobScript | - | post_job_script | YES |
| - | PreTaskScript | - | pre_task_script | YES |
| - | PostTaskScript | - | post_task_script | YES |
| - | UseNodeFrameList | useNodeRange | use_node_frame_list | NO |
| - | - | separateJobDependencies | render_order_dependencies | NO |
| - | - | separateTasks | write_nodes_as_tasks | NO |
| - | - | precompFirst | *no plans to implement* | NO |
| - | - | precompOnly | *no plans to implement* | NO |
| - | - | smartVectorOnly | *no plans to implement* | NO |
| - | - | eddySimulateOnly | *no plans to implement* | NO |
| - | - | draftTemplate | *no plans to implement* | NO |
| - | - | draftUser | *no plans to implement* | NO |
| - | - | draftEntity | *no plans to implement* | NO |
| - | - | - | use_parser_instead_of_nuke | NO |
| - | - | - | render_settings_from_metadata | NO |
| - | - | - | proxy_args | NO |
| - | - | - | copy_script | NO |
| - | - | - | copy_script_path | NO |
| - | - | - | submit_copied_script | NO |
| - | - | - | script_is_current | NO |
| - | - | - | submit_script_as_auxiliary_file | NO |
| - | - | - | parse_output_paths_to_deadline | NO |
| - | - | - | submit_writes_alphabetically | NO |
| - | - | - | submit_writes_in_render_order | NO |
| - | EnvironmentKeyValue{index} | - | *from environment settings* | NO |
| - | - | - | use_current_environment | NO |
| - | - | - | environment_keys | NO |
| - | - | - | environment | NO |
| - | - | - | omit_environment_keys | NO |
| - | - | - | submission_is_build_job | NO |
| - | - | - | build_job_script_path | NO |
