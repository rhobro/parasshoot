# paraSSHoot

Programmatically SSH into DoC machines and run commands.

## Examples

### Connection
#### To a specific machine
```python3
from parasshoot.lab import connect_to

machine = connect_to(
    "ash03",  # a favourite
    username="rm1723",  # shortcode
    # skipping password arg since password auth disabled by CSG
    key_main_path=...,  # defaults to the path as chosen by Kishan's script afaik
    key_jump_path=...,  # ^
    timeout=5,  # finite patience
)
machine.close()
```

#### To a random machine
This will retry until it finds a random working machine
```python3
from parasshoot.lab import connect_to_random

machine = connect_to_random(
    username="ab1234",  # shortcode
    # skipping password arg since password auth disabled by CSG
    key_main_path=...,  # default is path from Kishan's script afaik
    key_jump_path=...,  # ^
    timeout=1,  # even less patience
)
machine.close()
```

### Run commands
```python3
from parasshoot.lab import connect_to_random

machine = connect_to_random(...)
stdin, stdout, stderr = machine.cmd("pwd")

print("".join(stdout.readlines()))
machine.close()
```

### Ping benchmark
Test the ping times from each lab machines to a host. This is particularly
useful to find out which lab machine has the fastest ping time to a particular
website. For example, when IC Hack tickets release :)

#### Specific set of machines
```python3
from parasshoot.benchmark import ping_some

df = ping_some(
    host="www.tome.com",  # host to test
    batch=["vertex01", "beech02", "ash03",],  # lab machines to test
    username="ab1234",  # shortcode
    n_ping=10,  # number of pings to benchmark per machine
)

print(df)
```

#### Test ALL lab machines
Ensure that you set a reasonable batch size so that you are polite with CSG haha.

```python3
from parasshoot.benchmark import ping

df = ping(
    host="www.tome.com",  # host to test
    username="ab1234",  # shortcode
    n_parallel=20,  # number of machines to test simultaneously
    n_ping=100,  # number of pings to benchmark per machine
    n_times_try_failed=1,  # number of times to retry failed benchmark
)

print(df)
```

### Parallel downloads
Often sites (e.g. for book downloads) restrict 1 concurrent download per IP address.
Since these sites are run by the community, the downloads are often slow even on the
fastest Wi-Fi. This can make downloading multiple resources a very long process.

This tool allows you to download resources in parallel to your local filesystem. It
relays the data through separate lab machines in order to bypass IP restrictions.

The arguments accepted in `urls` and `tos` allows for 4 combinations of using this function.
You can choose whether you'd like to use a list of input URLs or a path leading
to a file containing them.
You can also choose to dump the files in a particular directory or you can give each file a custom name and path too.

#### File of URLs --> Directory
*links.txt*
```
https://from.me/a.pdf
https://from.me/b.pdf
https://from.me/c.pdf
...
```
```python3
from parasshoot.downloader import download 

download(
    urls="links.txt",
    tos="path/to/dir",
    username="ab1234"
)
```

#### URL List --> Directory
```python3
from parasshoot.downloader import download 

download(
    urls=[
        "https://from.me/a.pdf",
        "https://from.me/b.pdf",
        "https://from.me/c.pdf"
    ],
    tos="path/to/dir",
    username="ab1234"
)
```

#### URL List --> Custom paths
```python3
from parasshoot.downloader import download 

download(
    urls=[
        "https://from.me/a.pdf",
        "https://from.me/b.pdf",
        "https://from.me/c.pdf"
    ],
    tos=[
        "path/to/some1/a.pdf",
        "path/to/some2/b.pdf",
        "path/to/some3/c.pdf",
    ],
    username="ab1234"
)
```