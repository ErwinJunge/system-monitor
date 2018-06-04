#!/usr/bin/env python3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    Base,
    Measurement,
    CPUUtilization,
    CPUStats,
    MemoryStats,
    SwapStats,
    DiskStats,
    Process,
    ProcessMemory,
    ProcessIONice,
    ProcessIOCounters,
    ProcessContextSwitches,
)
import psutil
from time import sleep


def processes(measurement):
    for proc in psutil.process_iter(attrs=['cpu_percent']):
        pass
    sleep(1)
    attrs = [
        'pid',
        'name',
        'exe',
        'cmdline',
        'username',
        'nice',
        'ionice',
        'io_counters',
        'num_ctx_switches',
        'num_fds',
        'num_threads',
        'cpu_percent',
        'memory_full_info',
        'status',
    ]
    for item in psutil.process_iter(attrs=attrs):
        process = Process(
            measurement=measurement,
            pid=item.info['pid'],
            name=item.info['name'],
            exe=item.info['exe'],
            cmdline=' '.join(item.info['cmdline']),
            username=item.info['username'],
            nice=item.info['nice'],
            num_fds=item.info['num_fds'],
            num_threads=item.info['num_threads'],
            cpu_percent=item.info['cpu_percent'],
            status=item.info['status'],
        )
        if item.info['memory_full_info'] is not None:
            ProcessMemory(
                process=process,
                rss=item.info['memory_full_info'].rss,
                vms=item.info['memory_full_info'].vms,
                shared=item.info['memory_full_info'].shared,
                text=item.info['memory_full_info'].text,
                lib=item.info['memory_full_info'].lib,
                data=item.info['memory_full_info'].data,
                dirty=item.info['memory_full_info'].dirty,
                uss=item.info['memory_full_info'].uss,
                pss=item.info['memory_full_info'].pss,
                swap=item.info['memory_full_info'].swap,
            )
        ProcessIONice(
            process=process,
            ioclass=int(item.info['ionice'].ioclass),
            value=item.info['ionice'].value,
        )
        if item.info['io_counters'] is not None:
            ProcessIOCounters(
                process=process,
                read_count=item.info['io_counters'].read_count,
                write_count=item.info['io_counters'].write_count,
                read_bytes=item.info['io_counters'].read_bytes,
                write_bytes=item.info['io_counters'].write_bytes,
                read_chars=item.info['io_counters'].read_chars,
                write_chars=item.info['io_counters'].write_chars,
            )
        ProcessContextSwitches(
            process=process,
            voluntary=item.info['num_ctx_switches'].voluntary,
            involuntary=item.info['num_ctx_switches'].involuntary,
        )


def disk_stats(measurement):
    stats = psutil.disk_io_counters(perdisk=True)
    return [
        DiskStats(
            measurement=measurement,
            partition_id=partition_id,
            read_count=specifics.read_count,
            write_count=specifics.write_count,
            read_bytes=specifics.read_bytes,
            write_bytes=specifics.write_bytes,
            read_time=specifics.read_time,
            write_time=specifics.write_time,
            read_merged_count=specifics.read_merged_count,
            write_merged_count=specifics.write_merged_count,
            busy_time=specifics.busy_time,
        )
        for partition_id, specifics
        in stats.items()
    ]


def swap_stats(measurement):
    stats = psutil.swap_memory()
    return [
        SwapStats(
            measurement=measurement,
            total=stats.total,
            used=stats.used,
            sin=stats.sin,
            sout=stats.sout,
        )
    ]


def memory_stats(measurement):
    stats = psutil.virtual_memory()
    return [
        MemoryStats(
            measurement=measurement,
            total=stats.total,
            available=stats.available,
        )
    ]


def cpu_stats(measurement):
    stats = psutil.cpu_stats()
    return [
        CPUStats(
            measurement=measurement,
            ctx_switches=stats.ctx_switches,
            interrupts=stats.interrupts,
            soft_interrupts=stats.soft_interrupts,
            syscalls=stats.syscalls,
        )
    ]


def cpu_utilization(measurement):
    psutil.cpu_percent(interval=None, percpu=True)
    psutil.cpu_times_percent(interval=None, percpu=True)
    sleep(1)
    return [
        CPUUtilization(
            measurement=measurement,
            index=index,
            total=total,
            user=specific.user,
            nice=specific.nice,
            system=specific.system,
            idle=specific.idle,
            iowait=specific.iowait,
            irq=specific.irq,
            softirq=specific.softirq,
            steal=specific.steal,
            guest=specific.guest,
            guest_nice=specific.guest_nice,
        )
        for index, (total, specific)
        in enumerate(
            zip(
                psutil.cpu_percent(interval=None, percpu=True),
                psutil.cpu_times_percent(interval=None, percpu=True)
            )
        )
    ]


def create_measurement(Session):
    session = Session()
    measurement = Measurement()
    cpu_utilization(measurement)
    cpu_stats(measurement)
    memory_stats(measurement)
    swap_stats(measurement)
    disk_stats(measurement)
    processes(measurement)
    session.add(measurement)
    session.commit()


def show_measurements(Session):
    session = Session()
    for instance in session.query(Measurement).order_by(Measurement.id):
        print(
            instance.id,
            instance.created_at,
            instance.cpu_utilizations,
            instance.cpu_stats,
            instance.memory_stats,
            instance.swap_stats,
            instance.disk_stats,
            instance.processes,
        )


def run():
    engine = create_engine('sqlite:///data.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    while True:
        create_measurement(Session)
        sleep(5)


if __name__ == '__main__':
    run()
