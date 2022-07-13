# Phoenix Helpers

This repository includes helpers for the [Phoenix](https://github.com/HSF/phoenix) project.

## checkers

### event-file-checker

This python module allows to check that an event file follows properly the phoenix syntax for event files.
In order to check file `myfile.json` from the command line, just say
```
python event_file_checker.py myfile.json
```

In order to use the APi directly, write :
```python
import json
import event_file_checker

json_file = open("myfile.json")
topJson = json.load(json_file)
event_file_checker.check(topJson)
```

## scripts

### api-read-file

to be completed
