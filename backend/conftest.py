import os
import tempfile
from pathlib import Path
import pytest

@pytest.fixture(scope='session')
def postgres_url(tmp_path_factory):
    if os.getenv('TEST_DATABASE_URL'):
        yield os.environ['TEST_DATABASE_URL']
        return
    if os.getenv('TEST_POSTGRES')!='1':
        yield None
        return
    # Unix-socket-only temporary server; avoids broad process enumeration.
    from pgserver._commands import initdb, pg_ctl
    with tempfile.TemporaryDirectory(prefix='inqi-pg-',dir='/tmp') as directory:
        root=Path(directory);data=root/'data'
        initdb(['--auth-local=trust','-c','shared_memory_type=mmap','-c','dynamic_shared_memory_type=mmap','--encoding=utf8','-U','postgres'],pgdata=data,timeout=30)
        pg_ctl(['-w','-o',f'-h "" -k {root}','-l',str(root/'postgres.log'),'start'],pgdata=data,timeout=30)
        try: yield f'postgresql://postgres@/postgres?host={root}'
        finally: pg_ctl(['-w','stop','-m','fast'],pgdata=data,timeout=30)
