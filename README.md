# Experiment Secretary

A framework manages the versioning and recording of experiments. As well as some util functions often used in experiments.

## Components

### Core

**WorkSpace**

> [TO BE DEVELOPED]

The module where the experiments are conducted, which redirects the commands, listening and logging experiments. 

**Session**

A session is an experiment that needs to be logged. Create a session and record everything you think might be useful. For example

```python
from ExperimentSecretary.Core import Session
with Session(__file__,terminalLog = True) as ss:
        
        ### Experiment Code ###
        
        ss.add_info("outputPkl",outputPklpath)
```

Running script like this generates a log file as follows(saved in `.\.exp`):

```json
{
    "init_time": {
        "$date": 1588248158550
    },
    "fin_time": {
        "$date": 1588248158550
    },
    "git_version": "bd0cbfc87d3b8c0d7cc71e1f6d80953eec4fa284",
    "git_diff": "Some Uncommitted changes",
    "res": null,
    "termination": "success",
    "expName": "tests/VCCBFWalk.py",
    "outputPkl": "....",
    "stdout": "recorded stdout",
    "stderr": ""
}
```

Or you can inheret `Session` class and add custom log functions

### MDlogger

A logger that makes it easier to generate a MarkDown experiment report, especially in generating and linking figures in the markdown file.

### LogParser

The abstracted class for parsing a printed log, especially useful in plotting unstructured stuffes redirected from `stdout` into a file.


## install

Git clone into local and then run 

```python
pip install -e .
```
>`-e` will create a symbolic link for this package, so that you can modify this package without reinstall it.

## dependencies
- pymongo
- gitpython
