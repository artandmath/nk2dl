# nk2dl
 Nuke to Deadline. A toolset for submitting nukescripts to Thinkbox Deadline in a "big studio" manner.

## How to use

### Development and testing: 

Launch Nuke

```
# set working directory to nk2dl project root
cd <project root>

# set up environment
python scripts\setup_environment.py

# activate environment
.venv\Scripts\activate

# launch nuke
"C:\Program Files\Nuke15.1v1\Nuke15.1.exe"
```

### Basic Submission

Submit a single job from within Nuke:

```python
from nk2dl.core.submission import DeadlineSubmitter

# Create submitter
submitter = DeadlineSubmitter()

# Submit a job with custom settings
job_id = submitter.submit_job(
    "path/to/script.nk",
    name="My Nuke Job",
    priority=75,
    pool="nuke",
    frames="1-100",
    chunk_size=10,
    threads=4,
    ram_usage=16384,  # 16GB
    use_gpu=True,
    version = [15,1]
)
```