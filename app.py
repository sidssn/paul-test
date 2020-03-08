#!/usr/bin/env python
"""
Author - Siddharth Nair


This module consists of functions to reports based on the below scenarios:

Generate the following report based on the number of deployments to Live (successful or unsuccessful)

Generate the following based on the average time taken in minutes for a successful release to go from Integration to
Live grouped by project_group and ordered by the time taken (longest first)


Prepare a report that identifies project groups with the highest number of releases that have a successful deployment
to Integration but never have a corresponding successful deployment to Live. The output should be ordered by the
count (highest first).
"""

import json
from datetime import datetime
import statistics
import csv


INTEGRATION = "Integration"
LIVE = "Live"
days_of_week = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}


def get_day_of_week_deployment_frequency(data):
    for day_of_week in get_live_deployment_days(data):
        if day_of_week in days_of_week:
            days_of_week[day_of_week] += 1
    return days_of_week


def get_slow_releases(releases_by_group, success_int, success_live):
    time_diff_in_successful_releases = get_time_diff_from_successful_int_to_live_in_release(success_live, success_int)
    project_data = group_into_project_group(releases_by_group, time_diff_in_successful_releases)
    project_data = get_average(project_data)
    return project_data


def get_failed_releases(releases_by_group, success_int, success_live):
    """
    Gets the list of all the failed releases by project group
    :param releases_by_group: Dictionary where the list of releases are grouped by the project group
    :param success_live: Dictionary with all release versions and deployed times for successful deployments to Live
    :param success_int: Dictionary with all release versions and deployed times for successful deployments to Integration
    """
    unsuccessful_rel_by_proj_group = get_unsuccessful_releases_count(releases_by_group,success_live, success_int)
    return unsuccessful_rel_by_proj_group


def load_data():
    """
    Loads data in the json file and returns data in the form of a dictionary
    """
    with open("projects.json") as file:
        return json.load(file)["projects"]


def get_live_deployment_days(data):
    """
    Returns the list of weekdays that the live deployment was made
    :param data: Input json in the form of dictionary
    """
    list_of_dates = []
    for rel in data:
        for release in rel["releases"]:
            for dep in release["deployments"]:
                if dep["environment"] == LIVE:
                    list_of_dates.append(get_weekday_of_date(dep["created"]))
    return list_of_dates


def get_weekday_of_date(dt):
    """
    Returns weekday from the date of deployment
    :param dt: datetime as string
    """
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.000Z").strftime("%A")


def get_releases_by_group(data):
    """
    Group releases by project group in the form of a dictionary
    :param data: Input json in the form of dictionary
    """
    project_group_dict = {}

    # Loop over each project and get releases
    for project in data:
        group = project.get("project_group")
        releases = project["releases"]

        # Process each release for a project and add to group
        for release in releases:
            if group in project_group_dict:
                project_group_dict[group].append(release)
            else:
                project_group_dict[group] = []
                project_group_dict[group].append(release)

    return project_group_dict


def get_successful_releases(releases_by_group, env):
    """
    Function to return a dictionary of all successful releases for that release version based on the environment given
    :param releases_by_group: Dictionary where the list of releases are grouped by the project group
    :param env: Environment to which the deployment has been made
    """
    success_deploy = {}
    for key in releases_by_group.keys():
        for rel in releases_by_group[key]:
            for dep in rel["deployments"]:
                if dep["environment"] == env and dep["state"] == "Success":
                    success_deploy[rel["version"]] = dep["created"]
    return success_deploy


def get_time_diff_from_successful_int_to_live_in_release(success_live, success_int):
    """
    Get the time taken for a successful release from Integration to Live and store it in a dictionary
    with the release version as the key
    :param success_live: Dictionary with all release versions and deployed times for successful deployments to Live
    :param success_int: Dictionary with all release versions and deployed times for successful deployments to Integration
    """
    time_diff_in_releases = {}
    for key in success_live.keys():
        if key in success_int.keys():
            time_diff_in_releases[key] = (get_datetime(success_live[key]) - get_datetime(success_int[key])).seconds/60
    return time_diff_in_releases


def group_into_project_group(releases_by_group, time_diff_in_releases):
    """
    Group the time taken by each release in a list for each project group and store it in a dictionary
    with the key as the project group
    :param releases_by_group: Dictionary where the list of releases are grouped by the project group
    :param time_diff_in_releases: Dictionary of the time difference in releases between successful Integration to Live
    in minutes grouped by release version as the key
    """
    project_data = {}
    for key in releases_by_group.keys():
        for rel in releases_by_group[key]:
            if rel["version"] in time_diff_in_releases:
                if key in project_data:
                    project_data[key].append(time_diff_in_releases[rel["version"]])
                else:
                    project_data[key] = []
                    project_data[key].append(time_diff_in_releases[rel["version"]])
    return project_data


def get_average(project_data):
    """
    Get the average time taken for each release in that project group and sort with the longest time taken first
    :param project_data: Input dictionary with list of all the times it has taken in minutes from successful deployment
    from Integration to Live in the form of a list grouped by the project group as the key
    """
    for key in project_data.keys():
        if len(project_data[key]) != 0:
            project_data[key] = statistics.mean(project_data[key])
    return project_data


def get_unsuccessful_releases_count(releases_by_group, success_live, success_int):
    """
    Loop through all the releases that had successful integration deployments but no successful live ones and store the
    count in a dict with the project group as the key
    :param releases_by_group: Dictionary where the list of releases are grouped by the project group
    :param success_live: Dictionary with all release versions and deployed times for successful deployments to Live
    :param success_int: Dictionary with all release versions and deployed times for successful deployments to Integration
    """
    unsuccessful_rel = { k : success_int[k] for k in set(success_int) - set(success_live)}
    unsuccessful_rel_by_proj_group = {}
    for key in releases_by_group.keys():
        for rel in releases_by_group[key]:
            if rel["version"] in unsuccessful_rel:
                if key in unsuccessful_rel_by_proj_group:
                    unsuccessful_rel_by_proj_group[key] += 1
                else:
                    unsuccessful_rel_by_proj_group[key] = 1

    return unsuccessful_rel_by_proj_group


def get_datetime(created):
    return datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.000Z")


def sort_dictionary(dictionary, is_reverse=False):
    return sorted(dictionary.items(), key=lambda kv: kv[1], reverse=is_reverse)


def get_headers(field1, field2):
    """
    Function to set the headers on the csv file
    :param field1: Header to be set for the first column in the csv file
    :param field2: Header to be set for the second column in the csv file
    """
    field_names = [
        field1,
        field2,
    ]
    return field_names


def write_csv(file_name, field_names, rows):
    """
    Writes to csv file based with the given file_name having the headers based on the field_names and values populated
    by the rows
    :param file_name: The name to be given to the csv file generated
    :param field_names: List of headers for the columns in the csv file
    :param rows: List of tuples to populate the rows of the csv file
    """
    with open(file_name, "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(field_names)

        for row in rows:
            writer.writerow(row)


def generate_reports():
    data = load_data()
    days_of_live_deployments = get_day_of_week_deployment_frequency(data)
    write_csv("output/1_deployment_frequency.csv", get_headers("DaysOfWeek", "LiveDeployments"),
              list(days_of_live_deployments.items()))

    releases_by_group = get_releases_by_group(data)

    # Get all successful releases to Integration
    success_int = get_successful_releases(releases_by_group, INTEGRATION)

    # Get all successful releases to Live
    success_live = get_successful_releases(releases_by_group, LIVE)

    slow_releases = get_slow_releases(releases_by_group, success_int, success_live)
    write_csv("output/2_slow_releases.csv", get_headers("ProjectGroup", "AverageTimeToLive"),
              sort_dictionary(slow_releases, True))

    failed_releases = get_failed_releases(releases_by_group, success_int, success_live)
    write_csv("output/3_failing_releases.csv", get_headers("ProjectGroup", "FailedReleases"),
              sort_dictionary(failed_releases, True))


if __name__ == "__main__":
    generate_reports()
