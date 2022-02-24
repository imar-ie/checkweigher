
# Checkweigher

Python lib to enable data acquisition from CE3000/CE3100 Controller
Yamato Checkweighers



1. [Command List](#command-list)
2. [Instalation](#instalation)
3. [Usage](#usage)
4. [Examples](#examples)


## Command List

The followings show the details of command given for data communication.

| Command | Detail                        |          (Status)          |
|---------|:------------------------------|:--------------------------|
| DC      | Clear TOTAL data              | Implemented, not tested *  |
| DS      | Request TOTAL data w/o clear  | Implemented         |
| DT      | Request TOTAL data and clear  | Implemented, not tested *  |
| AS      | Request 500 Weight Data       | Implemented         |
| PN      | Request PROGRAM number change | Not Implemented *      |
    
\* Destructive Commands


## Instalation
```
git clone https://github.com/imar-ie/checkweigher.git
cd checkweigher
```

All dependencies are provided as part of the standard library, except for PyYAML, this can be installed by either:

```
pip install -r requirements.txt
```

or

```
pip install pyyaml
```


## Usage 

Can be used via the command line or as a module, options are the same for both 

```
checkweigher.py [-h] [-p PORT] [-c {DC,DS,DT,AS}] [-v] ip
```

### Positional/Required arguments:

#### IP

The checkweigher's IP address

### Optional arguments:

#### -p , --port
Device port    
Default: ***1001*** 

#### -c, --command
Command to be issued    
Options: {DC,DS,DT,AS}    
Default: ***DS***    

####  -v, --version
show program's version number and exit

####  -h, --help
show this help message and exit

## Examples

### CLI
```
python yamatocheckweigher.py 192.168.1.123 -p 1234 -c AS
```

### Module

```python
from yamatocheckweigher.yamatocheckweigher import Checkweigher

cw = Checkweigher('127.0.0.1', 1234)

cw.connect()

total = cw.DC()

fivehundred = cw.AS()

cw.disconnect()

```
