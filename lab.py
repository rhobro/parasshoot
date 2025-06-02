from itertools import chain
from random import shuffle, choice as choose
from paramiko import *
from pathlib import Path


# connect A --> B --> C
class Machine:
    
    def download(self, url, to):
        """Download the resource to a buffer satisfying I/O operations.
        NOTE: you are responsible for closing the destination I/O object.

        Args:
            url (str): URL of resource to be downloaded
            to (file-like object): Destination of download (e.g. open file, BytesIO)

        Returns:
            Download: Lazy object responsible for download progress.
        """
        
        _, stdout, stderr = self.inner.exec_command(f"wget -qO- {url}")
        return Download(stdout, stderr, to)
    
    
    def cmd(self, cmd):
        """Run command on Lab machine.

        Args:
            cmd (str): Linux command.

        Returns:
            (stdin, stdout, stderr): Outputs from command.
        """
        
        return self.inner.exec_command(cmd)
    
    def __init__(self, host, machine: SSHClient, jumper: SSHClient):
        self.host = host
        self.inner = machine
        self.jumper = jumper
        
        
    def close(self):
        """Self-explanatory: closing the SSH connection"""
        
        # close jumper, automatically closing connection to C
        self.jumper.close()
        
        # add back into consideration
        MACHINES.append(self.host)
        
        
class Download:
    
    def next(self, chunk_size = 4096):
        """Process next chunk of download.

        Args:
            chunk_size (int, optional): Size of chunk. Advised to keep default. Defaults to 4KB.

        Raises:
            RuntimeError: If an error is thrown on the destination machine.

        Returns:
            bool: If the download has finished.
        """
        
        # read chunk
        data = self.stdout.read(chunk_size)
        
        if not data:            
            # check errors
            err = "".join(self.stderr.readlines())
            if err != "":
                raise RuntimeError(err)
            
            return True
        
        self.f.write(data)
        return False
    
    def all(self):
        """Process all chunks until download is completed."""
        
        done = False
        while not done:
            done = self.next()
    
    def __init__(self, stdout, stderr, f):
        self.stdout = stdout
        self.stderr = stderr
        self.f = f


# CONNECTION


# lab machine names
JUMPERS = [f"shell{i}.doc.ic.ac.uk" for i in range(1, 6)]
ranges = {
    "texel": 44,
    "oak": 38,
    # "perry": 6,  # excluding since not Linux
    "cedar": 7,
    "gpu": 36,
    "ash": 41,
    "beech": 20,
    "willow": 20,
    "vertex": 22,
    "ray": 26,
    "maple": 10,
}
MACHINES = list(chain(*[
    [
        f"{group}{i:02d}"
        for i in range(1, n + 1)
    ]
    for (group, n) in ranges.items()
]))
shuffle(MACHINES)

# constants
LOCALHOST = "127.0.0.1"
PORT = 22
KEY_MAIN_PATH = (Path.home() / ".ssh" / "doclab_ecdsa").as_posix(),
KEY_JUMP_PATH = (Path.home() / ".ssh" / "doclab_ecdsa_jump").as_posix(),


def connect_to(
    machine_host,
    username,
    password=None,
    key_main_path=KEY_MAIN_PATH,
    key_jump_path=KEY_JUMP_PATH,
    timeout=10
) -> Machine:
    """Connect to a specific machine in the lab.

    Args:
        machine_host (str): Name of host e.g. ash03, a favourite :)
        username (str): CID
        password (str, optional): Lab machine password. Currently (as of 01/06/2025) not supported as CSG disabled password-based sign-in. Use Defaults to None.
        key_main_path (str, optional): Path to SSH key file for first hop. Defaults to KEY_MAIN_PATH, as defined by Kishan's SSH script.
        key_jump_path (str, optional): Path to SSH key file for second hop. Defaults to KEY_JUMP_PATH, like above.
        timeout (int, optional): SSH connection timeout. Defaults to 10s.

    Raises:
        RuntimeError: When it is not possible to connect to the host because of an SSH issue.

    Returns:
        Machine: Wrapper to represent the target machine and the relay.
    """
    
    # choose jumper
    jumper = _rand_jumper(username, password, key_main_path, timeout)
    
    try:
        # connect to machine
        machine = _connect_to_via(
            machine_host,
            jumper.get_transport(),
            username,
            password,
            key_jump_path,
            timeout
        )
        return Machine(machine_host, machine, jumper)
    
    except SSHException as e:
        jumper.close()
        raise RuntimeError(f"can't to connect to {machine_host}: {e}")
    

def connect_to_random(
    username,
    password=None,
    key_main_path=KEY_MAIN_PATH,
    key_jump_path=KEY_JUMP_PATH,
    timeout=10
) -> Machine:
    """Connect to a random available machine in the lab via a random relay (advised).
    Otherwise same as `connect_to()`
    """
    
    # choose jumper
    jumper = _rand_jumper(username, password, key_main_path, timeout)
    
    machines = MACHINES[:]
    while len(machines) > 0:
        host = choose(machines)

        try:
            machine = _connect_to_via(
                host,
                jumper.get_transport(),
                username,
                password,
                key_jump_path,
                timeout
            )
            return Machine(host, machine, jumper)
        
        except SSHException as e:
            print(f"failed machine connection to {host}: {e}")
            machines.remove(host)
    
    # no machines working
    raise RuntimeError("can't find working machine")
    

def _connect_to_via(
    machine_host,
    transport,
    username,
    password,
    key_path,
    timeout,
) -> SSHClient:
    # access jumper network
    channel = transport.open_channel(
        "direct-tcpip",
        (machine_host, PORT),
        (LOCALHOST, PORT),
        timeout=timeout
    )
    machine = SSHClient()
    machine.set_missing_host_key_policy(AutoAddPolicy())
    
    machine.connect(
        machine_host,
        username=username,
        password=password,
        key_filename=key_path,
        sock=channel,
        compress=True,
        timeout=timeout
    )
    
    # remove from consideration
    MACHINES.remove(machine_host)
    
    return machine
        

def _rand_jumper(username, password, key_path, timeout) -> SSHClient:
    jumpers = JUMPERS[:]
    
    while len(jumpers) > 0:
        host = choose(jumpers)
        cli = SSHClient()
        cli.set_missing_host_key_policy(AutoAddPolicy())

        try:
            cli.connect(
                host,
                username=username,
                password=password,
                key_filename=key_path,
                compress=True,
                timeout=timeout
            )
            return cli
        
        except SSHException as e:
            print(f"failed jumper connection to {host}: {e}")
            jumpers.remove(host)
    
    # no jumpers working
    raise RuntimeError("can't find working jumper")
