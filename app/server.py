"""Uvicorn launcher with every log stream explicitly directed to stdout."""
import os
import sys
import uvicorn
from uvicorn.config import LOGGING_CONFIG

if __name__ == '__main__':
    for handler in LOGGING_CONFIG['handlers'].values():
        if 'stream' in handler:
            handler['stream'] = 'ext://sys.stdout'
    sys.argv = ['uvicorn', 'app.main:app', '--log-level', os.getenv('LOG_LEVEL', 'INFO').lower(), *sys.argv[1:]]
    uvicorn.main()
