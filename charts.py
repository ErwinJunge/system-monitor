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
from collections import Counter


def round_to_interval(number, interval):
    return (
        (interval * int(number / interval))
        + (interval / 2)
    )


def get_mode(list_like, bin_size):
    binned_list = [
        round_to_interval(item, bin_size)
        for item in list_like
    ]
    return Counter(binned_list).most_common(1)[0][0]


def chop_list(list_like, step_sizes):
    return [
        list_like[sum(step_sizes[:i]):sum(step_sizes[:i+1])]
        for i in range(len(step_sizes))
    ]


def get_step_sizes(total_length, number_of_steps):
    step_sizes = [int(total_length / number_of_steps)] * number_of_steps
    remainder = total_length - sum(step_sizes)
    for i in range(remainder):
        step_sizes[i] += 1
    return step_sizes


def get_measurement_times(session):
    times_query = (
        session
        .query(Measurement.created_at)
        .order_by(Measurement.created_at)
    )
    return [obj.created_at for obj in times_query]


def create_cpu_chart(session, measurement_times, steps):
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
        show_dots=False,
    )
    step_sizes = get_step_sizes(len(measurement_times), steps)
    mid_points = [
        sum(step_sizes[:i]) + int(step_sizes[i]/2)
        for i in range(len(step_sizes))
    ]
    chart.x_labels = [
        measurement_times[i].isoformat()
        for i in mid_points
    ]
    for cpu_index, cpu_measurements in measurements.items():
        data = [
            cpu_measurements.get(measurement_time, 0)
            for measurement_time
            in measurement_times
        ]
        chopped_data = chop_list(data, step_sizes)
        modes = [
            get_mode(part, 2)
            for part in chopped_data
        ]
        chart.add(
            '{}'.format(cpu_index),
            modes,
            allow_interruptions=True,
        )
    chart.render_to_file('./cpu_chart.svg')
    chart.render_to_png('./cpu_chart.png')


def create_process_chart(session, measurement_times, steps):
    interesting_cmdlines = (
        session
        .query(Process.cmdline)
        .group_by(Process.cmdline)
        .order_by(desc(func.sum(Process.cpu_percent)))
        .slice(0, 5)
    )
    process_query = (
        session
        .query(
            Measurement.created_at,
            Process.cmdline,
            Process.cpu_percent,
        )
        .filter(
            Process.cmdline.in_(interesting_cmdlines),
            Measurement.id == Process.measurement_id,
        )
    )
    measurements = {}
    for measurement_time, cmdline, cpu_percent in process_query:
        cpu_measurements = measurements.setdefault(cmdline, {})
        cpu_measurements[measurement_time] = cpu_percent
    chart = pygal.Line(
        x_label_rotation=20,
        x_labels_major_count=10,
        show_minor_x_labels=False,
        show_dots=False,
        legend_at_bottom=True,
        legend_at_bottom_columns=1,
    )
    step_sizes = get_step_sizes(len(measurement_times), steps)
    mid_points = [
        sum(step_sizes[:i]) + int(step_sizes[i]/2)
        for i in range(len(step_sizes))
    ]
    chart.x_labels = [
        measurement_times[i].isoformat()
        for i in mid_points
    ]
    for cmdline, cpu_measurements in measurements.items():
        data = [
            cpu_measurements.get(measurement_time, 0)
            for measurement_time
            in measurement_times
        ]
        chopped_data = chop_list(data, step_sizes)
        modes = [
            get_mode(part, 2)
            for part in chopped_data
        ]
        chart.add(
            '{}'.format(cmdline),
            modes,
            allow_interruptions=True,
        )
    chart.render_to_file('./process_chart.svg')
    chart.render_to_png('./process_chart.png')


def run():
    Session = sessionmaker(bind=engine)
    session = Session()
    measurement_times = get_measurement_times(session)
    steps = 400
    create_cpu_chart(session, measurement_times, steps)
    create_process_chart(session, measurement_times, steps)


if __name__ == '__main__':
    run()
