from lab import *
import os
from urllib.parse import urlparse as parse


def download_all(urls, tos, username):
    """Download multiple files in parallel to specificed I/O destination.

    Args:
        urls (list or str): List of URLs or path to file containing it.
        tos (list or str): List of I/O objects to download to (e.g. open file, BytesIO) or destination directory.
        username (str): CID
    """
    if urls is str:
        with open(urls, "r") as f:
            urls = [l.strip() for l in f.readlines()]
            urls = [l for l in urls if l != ""]
            
    into_dir = False
    if tos is str:
        tos = [open(f"{tos}/{file_name(u)}", "w") for u in urls]
        into_dir = True
        
    ms = []
    dls = []
    
    # start downloads
    for url, to in zip(urls, tos):
        m = connect_to_random(username)
        dl = m.download(url, to)
        
        ms.append(m)
        dls.append(dl)
        
    # cycle finish downloads
    while len(dls) > 0:
        for dl in dls:
            if dl.next():
                dls.remove(dl)
                
    # close files if into directory
    if into_dir:
        for f in tos:
            f.close()
    
    # disconnect machines
    for m in ms:
        m.close()
    

# extract file name from url
def file_name(url):
    a = parse(url)
    return os.path.basename(a.path)
