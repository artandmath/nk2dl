`nk2dl` uses the Thinkbox Deadline Nuke plugin on the server side.

On the client side it replaces the Thinkbox Deadline Nuke Submitter.

## Feature Parity Table
`Plugin` and `Job Info` columns are the backend/server-side variables. `Thinkbox` and `nk2dl` columns are the frontend/client-side variables.

| Plugin Info | Job Info | Thinkbox | nk2dl | nk2dl per write overrides |
|-------------|----------|----------|-------|---------------------------|
| SceneFile | - | - | script_path | - |
| Version | - | - | nuke_version | YES |
| UseNukeX | - | useNukeX | use_nuke_x | YES |
| BatchMode | - | batchMode | batch_mode | YES |
| BatchModeIsMovie | - | batchModeIsMovie | *auto-detected* | - |
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
| Write-desAsSeparateJobs | - | separateJobs | write_-des_as_separate_jobs | - |
| Write-de | - | write_-des | write_-des | - |
| Write-de{index} | - | *auto-generated* | *auto-generated* | - |
| Write-de{index}StartFrame | - | *auto-generated* | *auto-generated* | - |
| Write-de{index}EndFrame | - | *auto-generated* | *auto-generated* | - |
| GraphScopeVariables | - | - | graph_scope_variables | - |
| GraphScopeVariablesEnabled | - | - | *auto-generated* | - |
| OutputFilePath | - | - | output_file_path | YES |
| ScriptJob | - | scriptJob | script_job_script_path | - |
| ScriptFilename | - | scriptFilename | script_job_script_path | - |
| BuildJobsFilename | - | - | *if submission_is_build_job=True* | - |
| - | Name | jobName | job_name | - |
| - | Plugin | "Nuke" | "Nuke" | - |
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
| - | ExtraInfo{index} | extraInfo{n} | extra_info | - |
| - | JobDependency{index} | dependencies | job_dependencies | YES |
| - | OutputFilename{index} | *auto-generated* | *auto-generated* | - |
| - | AuxiliaryFiles | - | *if submit_script_as_auxiliary_file=True* | - |
| - | OnJobComplete | onComplete | on_job_complete | YES |
| - | InitialStatus | submitSuspended | submit_suspended | YES |
| - | LimitGroups | limitGroups | limit_groups | YES |
| - | MachineLimit | machineLimit | machine_limit | - |
| - | Whitelist/Blacklist | isBlacklist/machineList | *implemnted as allow/deny lists* | - |
| - | TaskTimeoutSeconds | taskTimeout | task_timeout | YES |
| - | EnableAutoTimeout | autoTaskTimeout | enable_auto_timeout | YES |
| - | LimitConcurrentTasks | limitConcurrentTasks | limit_worker_tasks | YES |
| - | PreJobScript | - | pre_job_script | YES |
| - | PostJobScript | - | post_job_script | YES |
| - | PreTaskScript | - | pre_task_script | YES |
| - | PostTaskScript | - | post_task_script | YES |
| - | Use-deFrameList | use-deRange | use_-de_frame_list | - |
| - | - | separateJobDependencies | render_order_dependencies | - |
| - | - | separateTasks | write_-des_as_tasks | - |
| - | - | precompFirst | *- plans to implement* | - |
| - | - | precompOnly | *- plans to implement* | - |
| - | - | smartVectorOnly | *- plans to implement* | - |
| - | - | eddySimulateOnly | *- plans to implement* | - |
| - | - | draftTemplate | *- plans to implement* | - |
| - | - | draftUser | *- plans to implement* | - |
| - | - | draftEntity | *- plans to implement* | - |
| - | - | - | use_parser_instead_of_nuke | - |
| - | - | - | render_settings_from_metadata | - |
| - | - | - | proxy_args | - |
| - | - | - | copy_script | - |
| - | - | - | copy_script_path | - |
| - | - | - | submit_copied_script | - |
| - | - | - | script_is_current | - |
| - | - | - | submit_script_as_auxiliary_file | - |
| - | - | - | parse_output_paths_to_deadline | - |
| - | - | - | submit_writes_alphabetically | - |
| - | - | - | submit_writes_in_render_order | - |
| - | EnvironmentKeyValue{index} | - | *from environment settings* | - |
| - | - | - | use_current_environment | - |
| - | - | - | environment_keys | - |
| - | - | - | environment | - |
| - | - | - | omit_environment_keys | - |
| - | - | - | submission_is_build_job | - |
| - | - | - | build_job_script_path | - |
