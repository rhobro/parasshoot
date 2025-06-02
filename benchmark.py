from lab import *
from itertools import batched
import pandas as pd
import re


PING_SUMMARY_PATTERN = r"\d+\.\d+"
    

def benchmark_ping(host, username, n_parallel=20, n_ping=100, n_times_try_failed=0):
    """Benchmark the ping to a host from all lab machines.

    Args:
        host (str): Host to test ping for, e.g. a ticketing website :)
        username (str): Self-explanatory
        n_parallel (int, optional): Number of lab machines benchmarking in parallel. Defaults to 20.
        n_ping (int, optional): Number of ping replies to wait for in each benchmark. Defaults to 100.
        n_times_try_failed (int, optional): Number of times to retry failed connections to lab machines. Defaults to 0. Recommended <= 1.

    Returns:
        (pd.DataFrame, list): DataFrame of benchmark results sorted in descending order of average ping, list of machines that failed the benchmark.
    """
    
    batches = list(batched(MACHINES, n_parallel))
    df = pd.DataFrame()
    failed = []
    
    # test batch
    for batch in batches:
        df_, failed_ = benchmark_ping_selected(host, username, batch, n_ping)
        df = pd.concat([df, df_])
        failed.extend(failed_)
        break
    
    # retry failed
    for _ in range(n_times_try_failed):
        if len(failed) == 0:
            break
        
        df_, failed =  benchmark_ping_selected(host, username, failed, n_ping)
        df = pd.concat([df, df_])
        
    return df.sort_values("avg", ascending=False), failed


def benchmark_ping_selected(host, username, batch, n_ping):
    """Benchmark the ping to a host from a subset of all lab machines. Like above."""
    
    machines = {}
    outs = {}
    failed = []
    stats = {
        "machine": [],
        "min": [],
        "avg": [],
        "max": [],
        "std": []
    }
    
    # connect
    for m in batch:
        try:
            machines[m] = connect_to(m, username=username)
        except:
            failed.append(m)
            continue
            
    # exec
    for m, machine in machines.items():
        # always assuming success :)
        _, outs[m], _ = machine.cmd(f"ping {host} -c {n_ping}")
    
    # process
    for m in outs:
        raw = outs[m].readlines()[-1]
        try:
            min, avg, max, std = [float(t) for t in re.findall(PING_SUMMARY_PATTERN, raw)]
            
            stats["machine"].append(m)
            stats["min"].append(min)
            stats["avg"].append(avg)
            stats["max"].append(max)
            stats["std"].append(std)
        except:
            failed.append(m)
            continue
    
    # close
    for machine in machines.values():
        machine.close()

    # process
    return pd.DataFrame(stats), failed
