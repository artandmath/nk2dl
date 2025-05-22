`nk2dl` uses the Thinkbox Deadline Nuke plugin on the server side.

On the client side it replaces the Thinkbox Deadline Nuke Submitter.

## Feature Parity Table
`Plugin` and `Job Info` columns are the backend/server-side variables. `nk2dl` and `Thinkbox` columns are the frontend/client-side variables.

| Plugin Info | Job Info | nk2dl | Thinkbox |
|-------------|----------|-------|----------|
| SceneFile | - | script_path | - |
| Version | - | nuke_version | - |
| UseNukeX | - | use_nuke_x | useNukeX |
| BatchMode | - | batch_mode | batchMode |
| BatchModeIsMovie | - | *auto-detected* | batchModeIsMovie |
| ContinueOnError | - | continue_on_error | continueOnError |
| EnforceRenderOrder | - | enforce_render_order | enforceRenderOrder |
| RenderMode | - | render_mode | renderMode |
| UseGpu | - | use_gpu | useGpu |
| GpuOverride | - | gpu_override | chooseGpu |
| Threads | - | threads | threads |
| RamUse | - | ram_use | memoryUsage |
| StackSize | - | stack_size | stackSize |
| Views | - | views | views |
| PerformanceProfiler | - | performance_profiler | performanceProfiler |
| PerformanceProfilerDir | - | performance_profiler_path | performanceProfilerPath |
| ReloadPlugins | - | reload_plugins | reloadPlugin |
| WriteNodesAsSeparateJobs | - | write_nodes_as_separate_jobs | separateJobs |
| WriteNode | - | write_nodes | write_nodes |
| WriteNode{index} | - | *auto-generated* | *auto-generated* |
| WriteNode{index}StartFrame | - | *auto-generated* | *auto-generated* |
| WriteNode{index}EndFrame | - | *auto-generated* | *auto-generated* |
| GraphScopeVariables | - | graph_scope_variables | - |
| GraphScopeVariablesEnabled | - | *auto-generated* | - |
| OutputFilePath | - | output_file_path | - |
| ScriptJob | - | - | scriptJob |
| ScriptFilename | - | - | scriptFilename |
| BuildJobsFilename | - | *if submission_is_build_job=True* | - |
| - | Name | job_name | jobName |
| - | Plugin | "Nuke" | "Nuke" |
| - | Frames | frames | frameList |
| - | ChunkSize | chunk_size | chunkSize |
| - | ConcurrentTasks | concurrent_tasks | concurrentTasks |
| - | Pool | pool | pool |
| - | Group | group | group |
| - | Priority | priority | priority |
| - | BatchName | batch_name | batchName |
| - | Department | department | department |
| - | Comment | comment | comment |
| - | ExtraInfo{index} | extra_info | extraInfo{n} |
| - | JobDependency{index} | job_dependencies | dependencies |
| - | OutputFilename{index} | *auto-generated* | *auto-generated* |
| - | AuxiliaryFiles | *if submit_script_as_auxiliary_file=True* | - |
| - | OnJobComplete | on_job_complete | onComplete |
| - | InitialStatus | submit_suspended | submitSuspended |
| - | LimitGroups | limit_groups | limitGroups |
| - | MachineLimit | machine_limit | machineLimit |
| - | Whitelist/Blacklist | *implemnted as allow/deny lists* | isBlacklist/machineList |
| - | TaskTimeoutSeconds | task_timeout | taskTimeout |
| - | EnableAutoTimeout | enable_auto_timeout | autoTaskTimeout |
| - | LimitConcurrentTasks | limit_worker_tasks | limitConcurrentTasks |
| - | PreJobScript | pre_job_script | - |
| - | PostJobScript | post_job_script | - |
| - | PreTaskScript | pre_task_script | - |
| - | PostTaskScript | post_task_script | - |
| - | UseNodeFrameList | use_node_frame_list | useNodeRange |
| - | - | render_order_dependencies | separateJobDependencies |
| - | - | write_nodes_as_tasks | separateTasks |
| - | - | *no plans to implement* | precompFirst |
| - | - | *no plans to implement* | precompOnly |
| - | - | *no plans to implement* | smartVectorOnly |
| - | - | *no plans to implement* | eddySimulateOnly |
| - | - | *no plans to implement* | draftTemplate |
| - | - | *no plans to implement* | draftUser |
| - | - | *no plans to implement* | draftEntity |
| - | - | use_parser_instead_of_nuke | - |
| - | - | render_settings_from_metadata | - |
| - | - | copy_script | - |
| - | - | copy_script_path | - |
| - | - | copy_script_name | - |
| - | - | submit_copied_script | - |
| - | - | script_is_current | - |
| - | - | submit_script_as_auxiliary_file | - |
| - | - | parse_output_paths_to_deadline | - |
| - | - | submit_writes_alphabetically | - |
| - | - | submit_writes_in_render_order | - |
| - | EnvironmentKeyValue{index} | *from environment settings* | - |
| - | - | use_current_environment | - |
| - | - | environment_keys | - |
| - | - | environment | - |
| - | - | omit_environment_keys | - |
| - | - | submission_is_build_job | - |
| - | - | build_job_script_path | - |
