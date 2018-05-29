from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    ForeignKey,
    String,
    Numeric,
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.sql import func


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=Base)


class Measurement(Base):
    created_at = Column(DateTime, default=func.now())
    cpu_utilizations = relationship('CPUUtilization', back_populates='measurement')
    cpu_stats = relationship('CPUStats', uselist=False, back_populates='measurement')
    memory_stats = relationship('MemoryStats', uselist=False, back_populates='measurement')
    swap_stats = relationship('SwapStats', uselist=False, back_populates='measurement')
    disk_stats = relationship('DiskStats', back_populates='measurement')
    processes = relationship('Process', back_populates='measurement')


class CPUUtilization(Base):
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    measurement = relationship('Measurement', back_populates='cpu_utilizations')
    index = Column(Integer)
    total = Column(Integer)
    user = Column(Integer)
    nice = Column(Integer)
    system = Column(Integer)
    idle = Column(Integer)
    iowait = Column(Integer)
    irq = Column(Integer)
    softirq = Column(Integer)
    steal = Column(Integer)
    guest = Column(Integer)
    guest_nice = Column(Integer)

    def __repr__(self):
        return '{}: {}, {}'.format(self.index, self.total, self.idle)


class CPUStats(Base):
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    measurement = relationship('Measurement', back_populates='cpu_stats')
    ctx_switches = Column(Integer)
    interrupts = Column(Integer)
    soft_interrupts = Column(Integer)
    syscalls = Column(Integer)

    def __repr__(self):
        return 'ctx_switches: {}, interrupts: {}, soft_interrupts: {}, syscalls: {}'.format(
            self.ctx_switches,
            self.interrupts,
            self.soft_interrupts,
            self.syscalls,
        )


class MemoryStats(Base):
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    measurement = relationship('Measurement', back_populates='memory_stats')
    total = Column(Integer)
    available = Column(Integer)

    def __repr__(self):
        return 'memory available: {}'.format(
            self.available,
        )


class SwapStats(Base):
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    measurement = relationship('Measurement', back_populates='swap_stats')
    total = Column(Integer)
    used = Column(Integer)
    sin = Column(Integer)
    sout = Column(Integer)

    def __repr__(self):
        return 'swap used: {}, sin: {}, sout: {}'.format(
            self.used,
            self.sin,
            self.sout,
        )


class DiskStats(Base):
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    measurement = relationship('Measurement', back_populates='disk_stats')
    partition_id = Column(String)
    read_count = Column(Integer)
    write_count = Column(Integer)
    read_bytes = Column(Integer)
    write_bytes = Column(Integer)
    read_time = Column(Integer)
    write_time = Column(Integer)
    read_merged_count = Column(Integer)
    write_merged_count = Column(Integer)
    busy_time = Column(Integer)

    def __repr__(self):
        return '{} busy: {}'.format(
            self.partition_id,
            self.busy_time,
        )


class Process(Base):
    measurement_id = Column(Integer, ForeignKey('measurement.id'))
    measurement = relationship('Measurement', back_populates='processes')
    pid = Column(Integer)
    name = Column(String)
    exe = Column(String)
    cmdline = Column(String)
    username = Column(String)
    nice = Column(Integer)
    num_fds = Column(Integer)
    num_threads = Column(Integer)
    cpu_percent = Column(Numeric(3, 1))
    status = Column(String)
    memory = relationship('ProcessMemory', uselist=False, back_populates='process')
    ionice = relationship('ProcessIONice', uselist=False, back_populates='process')
    iocounters = relationship('ProcessIOCounters', uselist=False, back_populates='process')
    ctx_switches = relationship('ProcessContextSwitches', uselist=False, back_populates='process')

    def __repr__(self):
        return '{}, {}, {}, {}, mem: {}, swap: {}'.format(
            self.cpu_percent,
            self.name,
            self.exe,
            self.cmdline,
            self.memory.rss if self.memory else '?',
            self.memory.swap if self.memory else '?',
        )


class ProcessMemory(Base):
    process_id = Column(Integer, ForeignKey('process.id'))
    process = relationship('Process', back_populates='memory')
    rss = Column(Integer)
    vms = Column(Integer)
    shared = Column(Integer)
    text = Column(Integer)
    lib = Column(Integer)
    data = Column(Integer)
    dirty = Column(Integer)
    uss = Column(Integer)
    pss = Column(Integer)
    swap = Column(Integer)


class ProcessIONice(Base):
    process_id = Column(Integer, ForeignKey('process.id'))
    process = relationship('Process', back_populates='ionice')
    ioclass = Column(Integer)
    value = Column(Integer)


class ProcessIOCounters(Base):
    process_id = Column(Integer, ForeignKey('process.id'))
    process = relationship('Process', back_populates='iocounters')
    read_count = Column(Integer)
    write_count = Column(Integer)
    read_bytes = Column(Integer)
    write_bytes = Column(Integer)
    read_chars = Column(Integer)
    write_chars = Column(Integer)


class ProcessContextSwitches(Base):
    process_id = Column(Integer, ForeignKey('process.id'))
    process = relationship('Process', back_populates='ctx_switches')
    voluntary = Column(Integer)
    involuntary = Column(Integer)
