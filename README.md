# w1r3catcher
Weechat script for downloading all uploads from https://w1r3.net and other file hosters

## Install 
Place `w1r3catcher.py` into your `~/.weechat/python/` folder and enable it in weechat with  
`/script load w1r3catcher.py`

## Usage
```
/w1r3catcher list
    List all file hosters the script is currently aware of
/w1r3catcher add <domain>
    Add a new file hoster
/w1r3catcher del {<domain> | <position>}
    Delete a file hoster by name or by position in /w1r3catcher list
/w1r3catcher logging {on | off}
    Enable/disable logging of matched urls to core buffer
```


Files will be saved into `~/.weechat/w1r3catcher/` as `irc.SERVER.CHANNEL-YYYYMMDD-HH:MM:SS.EXT`

