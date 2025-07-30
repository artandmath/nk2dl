## Feature Parity Table
`nk2dl` uses the Thinkbox Deadline Nuke plugin on the back-end/server-side.
- The `Plugin` and `Job Info` columns are the back-end/server-side variables.
- Some back-end/server-side features require a modified version of the Nuke plugin. See the plugin section in the [Installation Guide](./installation.md#3-install-the-deadline-plugin-for-nuke-152-optional).

On the front-end/client-side it `nk2dl` replaces the Thinkbox Deadline Nuke Submitter.
- The `nk2dl` column are the front-end/client-side variables and the `Thinkbox` equivalents.

| Plugin Info | Job Info | Thinkbox | nk2dl | nk2dl per write overrides |
|-------------|----------|----------|-------|---------------------------|
| SceneFile | - | - | script_path | - |
| Version | - | - | nuke_version | &#10004; |
| UseNukeX | - | useNukeX | use_nuke_x | &#10004; |
| BatchMode | - | batchMode | batch_mode | &#10004; |
| BatchModeIsMovie | - | batchModeIsMovie | *auto-detected* | - |
| ContinueOnError | - | continueOnError | continue_on_error | &#10004; |
| EnforceRenderOrder | - | enforceRenderOrder | enforce_render_order | &#10004; |
| RenderMode | - | renderMode | render_mode | &#10004; |
| UseGpu | - | useGpu | use_gpu | &#10004; |
| GpuOverride | - | chooseGpu | gpu_override | &#10004; |
| Threads | - | threads | threads | &#10004; |
| RamUse | - | memoryUsage | ram_use | &#10004; |
| StackSize | - | stackSize | stack_size | &#10004; |
| Views | - | views | views | &#10004; |
| PerformanceProfiler | - | performanceProfiler | performance_profiler | &#10004; |
| PerformanceProfilerDir | - | performanceProfilerPath | performance_profiler_path | &#10004; |
| ReloadPlugins | - | reloadPlugin | reload_plugins | &#10004; |
| WriteNodesAsSeparateJobs | - | separateJobs | write_nodes_as_separate_jobs | - |
| WriteNode | - | write_nodes | write_nodes | - |
| WriteNode{index} | - | *auto-generated* | *auto-generated* | - |
| WriteNode{index}StartFrame | - | *auto-generated* | *auto-generated* | - |
| WriteNode{index}EndFrame | - | *auto-generated* | *auto-generated* | - |
| GraphScopeVariables | - | - | graph_scope_variables | - |
| GraphScopeVariablesEnabled | - | - | *auto-generated* | - |
| OutputFilePath | - | - | output_file_path | &#10004; |
| ScriptJob | - | scriptJob | script_job_script_path | - |
| ScriptFilename | - | scriptFilename | script_job_script_path | - |
| BuildJobsFilename | - | - | *if submission_is_build_job=True* | - |
| - | Name | jobName | job_name | - |
| - | Plugin | "Nuke" | "Nuke" | - |
| - | Frames | frameList | frames | &#10004; |
| - | ChunkSize | chunkSize | chunk_size | &#10004; |
| - | ConcurrentTasks | concurrentTasks | concurrent_tasks | &#10004; |
| - | Pool | pool | pool | &#10004; |
| - | Group | group | group | &#10004; |
| - | Priority | priority | priority | &#10004; |
| - | BatchName | batchName | batch_name | &#10004; |
| - | Department | department | department | &#10004; |
| - | UserName | - | user_name | &#10004; |
| - | Comment | comment | comment | &#10004; |
| - | ExtraInfo{index} | extraInfo{n} | extra_info | - |
| - | JobDependency{index} | dependencies | job_dependencies | &#10004; |
| - | OutputFilename{index} | *auto-generated* | *auto-generated* | - |
| - | AuxiliaryFiles | - | *if submit_script_as_auxiliary_file=True* | - |
| - | OnJobComplete | onComplete | on_job_complete | &#10004; |
| - | InitialStatus | submitSuspended | submit_suspended | &#10004; |
| - | LimitGroups | limitGroups | limit_groups | &#10004; |
| - | MachineLimit | machineLimit | machine_limit | - |
| - | Whitelist/Blacklist | isBlacklist/machineList | *implemnted as allow/deny lists* | - |
| - | TaskTimeoutSeconds | taskTimeout | task_timeout | &#10004; |
| - | EnableAutoTimeout | autoTaskTimeout | enable_auto_timeout | &#10004; |
| - | LimitConcurrentTasks | limitConcurrentTasks | limit_worker_tasks | &#10004; |
| - | PreJobScript | - | pre_job_script | &#10004; |
| - | PostJobScript | - | post_job_script | &#10004; |
| - | PreTaskScript | - | pre_task_script | &#10004; |
| - | PostTaskScript | - | post_task_script | &#10004; |
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
