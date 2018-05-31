#!/usr/bin/env python3
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import (
    Measurement,
    CPUUtilization,
)
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
        x_labels_major_every=60,
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


def run():
    engine = create_engine('sqlite:///data.db')
    Session = sessionmaker(bind=engine)
    session = Session()
    measurement_times = get_measurement_times(session)
    create_cpu_chart(session, measurement_times)


if __name__ == '__main__':
    run()
