from sqlalchemy import create_engine
from sqlalchemy.sql import text
from sqlalchemy import MetaData, Table, Column, INTEGER, FLOAT, CHAR, BIGINT, BLOB, ForeignKey
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import sys
import json


Base = declarative_base()


class Run(Base):
    __tablename__ = 'Run'

    id = Column(INTEGER, primary_key=True)
    processes = Column(INTEGER)
    jobid = Column(CHAR(255))
    application = Column(CHAR(255))
    runtime = Column(INTEGER)
    energy = Column(INTEGER)
    cpuhours = Column(FLOAT)


class NodeType(Base):
    __tablename__ = 'NodeType'

    id = Column(INTEGER, primary_key=True)
    host = Column(CHAR(255))
    name = Column(CHAR(255))


class Kernel(Base):
    __tablename__ = 'Kernel'

    id = Column(INTEGER, primary_key=True)
    name = Column(CHAR(255))
    config_hash = Column(CHAR(64))
    config_file = Column(BLOB)
    config_parameters = Column(BLOB)
    



class KernelPerf(Base):
    __tablename__ = 'KernelPerf'

    id = Column(INTEGER, primary_key=True)
    runtime = Column(BIGINT)
    cores = Column(INTEGER)
    muscle_time = Column(BIGINT)
    mpi_time = Column(BIGINT)
    io_time = Column(BIGINT)
    energy = Column(BIGINT)
    kernel_id = Column(INTEGER, ForeignKey("Kernel.id"))
    run_id = Column(INTEGER, ForeignKey("Run.id"))
    node_type_id = Column(INTEGER, ForeignKey("NodeType.id"))
    memory = Column(BIGINT)
    start_time = Column(INTEGER)
    end_time = Column(INTEGER)


def get_or_create(session, model, kwargs_f, kwargs):
    instance = session.query(model).filter_by(**kwargs_f).first()
    if instance:
        return instance
    else:
        tmp = kwargs.copy()
        tmp.update(kwargs_f)
        instance = model(**tmp)
        session.add(instance)
        session.commit()
        return instance


def create_tables(engine):
    
    Run.__table__.create(engine)
    Kernel.__table__.create(engine)
    NodeType.__table__.create(engine)
    KernelPerf.__table__.create(engine)

def drop_tables(engine):
    KernelPerf.__table__.drop(engine)
    Kernel.__table__.drop(engine)
    NodeType.__table__.drop(engine)
    Run.__table__.drop(engine)

if __name__ == '__main__':

    if len(sys.argv) == 3:
       # Assume reset
#       engine = create_engine('sqlite:////home/operks/Projects/Compat/python/perf.db')
       engine = create_engine('mysql://olly:olly@129.187.255.55/performance')
      # drop_tables(engine)
       create_tables(engine)
       exit()
    
    with open(sys.argv[1], 'r') as fd:
        data = json.loads(fd.read())

#    engine = create_engine('sqlite:////home/operks/Projects/Compat/python/perf.db')
    engine = create_engine('mysql://performance_update:password@129.187.255.55/performance')
#    create_tables(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    r = get_or_create(session, Run, {'jobid': data['job_ID']},{'processes':data['run_cores'], 'application':data['run_app'], 'runtime':0, 'energy':0, 'cpuhours':0})
    session.add(r)
    session.flush()


    for mapfile in data['kernels']:
        kernel = get_or_create(session, Kernel, {'name':mapfile['kernel_name'], 'config_hash':mapfile['kernel_hash']},{'config_parameters':json.dumps(mapfile['parameters'])})
        node = get_or_create(session, NodeType, {'host':mapfile['node_system'], 'name':mapfile['node_type']},{})
        session.flush()
        p = KernelPerf(runtime=mapfile['kernel_runtime'], cores=mapfile['kernel_cores'],
            muscle_time=mapfile['kernel_muscle'], mpi_time=mapfile['kernel_mpi'], io_time=mapfile['kernel_io'],
            energy=mapfile['kernel_energy'], kernel_id=kernel.id, run_id=r.id,
            node_type_id=node.id, memory=mapfile['memory'], start_time=mapfile['time_start'], end_time=mapfile['time_end'])
        session.add(p)
        session.flush()
        r.cpuhours += (mapfile['kernel_runtime'] * mapfile['kernel_cores'] / 3600)
        if data['run_app'].upper() == 'FUSION':
            r.energy = max(r.energy, mapfile['kernel_energy'])
            r.runtime = max(r.runtime, mapfile['kernel_runtime'])
        elif data['run_app'].upper() == 'BAC':
            r.energy += mapfile['kernel_energy']
            r.runtime += mapfile['kernel_runtime']
    session.commit()
    


