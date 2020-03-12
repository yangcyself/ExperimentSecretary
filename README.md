# Experiment Secretary

A framework manages the versioning and recording of experiments. As well as some util functions often used in experiments.

## Components

### Core

**WorkSpace**

> [TO BE DEVELOPED]

The module where the experiments are conducted, which redirects the commands, listening and logging experiments. 


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