#!/usr/bin/env python3
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
from models import (
    Measurement,
    CPUUtilization,
    Process,
)
from engine import engine
import pygal


def get_measurement_times(session):
    times_query = (
        session
        .query(Measurement.created_at)
        .order_by(Measurement.created_at)
    )
    return [obj.created_at for obj in times_query]


def create_cpu_chart(session, measurement_times):
    query = (
        session
        .query(
            Measurement.created_at,
            CPUUtilization.index,
            CPUUtilization.total,
        )
        .filter(
            Measurement.id == CPUUtilization.measurement_id,
        )
    )
    measurements = {}
    for measurement_time, cpu_index, total in query:
        cpu_measurements = measurements.setdefault(cpu_index, {})
        cpu_measurements[measurement_time] = total
    chart = pygal.Line(
        x_label_rotation=20,
        x_labels_major_count=10,
        show_minor_x_labels=False,
    )
    chart.x_labels = [
        measurement_time.isoformat()
        for measurement_time
        in measurement_times
    ]
    for cpu_index, cpu_measurements in measurements.items():
        chart.add(
            '{}'.format(cpu_index),
            [
                cpu_measurements.get(measurement_time, None)
                for measurement_time
                in measurement_times
            ],
            allow_interruptions=True,
        )
    chart.render_to_file('./cpu_chart.svg')


def create_process_chart(session, measurement_times):
    interesting_names = (
        session
        .query(Process.name)
        .group_by(Process.name)
        .order_by(desc(func.sum(Process.cpu_percent)))
        .slice(0, 5)
    )
    process_query = (
        session
        .query(
            Measurement.created_at,
            Process.name,
            Process.cpu_percent,
        )
        .filter(
            Process.name.in_(interesting_names),
            Measurement.id == Process.measurement_id,
        )
    )
    measurements = {}
    for measurement_time, name, cpu_percent in process_query:
        cpu_measurements = measurements.setdefault(name, {})
        cpu_measurements[measurement_time] = cpu_percent
    chart = pygal.Line(
        x_label_rotation=20,
        x_labels_major_count=10,
        show_minor_x_labels=False,
    )
    chart.x_labels = [
        measurement_time.isoformat()
        for measurement_time
        in measurement_times
    ]
    for name, cpu_measurements in measurements.items():
        chart.add(
            '{}'.format(name),
            [
                cpu_measurements.get(measurement_time, None)
                for measurement_time
                in measurement_times
            ],
            allow_interruptions=True,
        )
    chart.render_to_file('./process_chart.svg')


def run():
    Session = sessionmaker(bind=engine)
    session = Session()
    measurement_times = get_measurement_times(session)
    create_cpu_chart(session, measurement_times)
    create_process_chart(session, measurement_times)


if __name__ == '__main__':
    run()
