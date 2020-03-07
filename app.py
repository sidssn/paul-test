import json
from datetime import datetime
import statistics
import csv

days_of_week = {"Monday": 0, "Tuesday": 0, "Wednesday": 0, "Thursday": 0, "Friday": 0, "Saturday": 0, "Sunday": 0}
IS_REVERSE = True
INTEGRATION = "Integration"
LIVE = "Live"


def get_day_of_week_deployment_frequency(data):
    for day_of_week in get_live_deployment_days(data):
        if day_of_week in days_of_week:
            days_of_week[day_of_week] += 1
    return days_of_week


def get_slow_releases(data):
    releases_by_grp = get_releases_by_group(data)

    # Get all successful releases to Integration
    success_int = get_successful_releases(releases_by_grp, INTEGRATION)

    # Get all successful releases to Live
    success_live = get_successful_releases(releases_by_grp, LIVE)

    time_diff_in_successful_releases = get_time_diff_from_successful_int_to_live_in_release(success_live, success_int)
    project_data = grp_into_project_grp(releases_by_grp, time_diff_in_successful_releases)
    return get_average_then_sort(project_data)


def get_failed_releases(data):
    """
    Gets the list of all the failed releases by project group
    """
    releases_by_grp = get_releases_by_group(data)
    success_int = get_successful_releases(releases_by_grp, INTEGRATION)
    success_live = get_successful_releases(releases_by_grp, LIVE)
    return get_unsuccessful_releases_count_then_sort(releases_by_grp,success_live, success_int)


def load_data():
    """
    Loads data in the json file and returns data in the form of a dictionary
    """
    with open("projects.json") as file:
        return json.load(file)["projects"]


def get_live_deployment_days(data):
    """
    Returns the list of weekdays that the live deployment was made
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
    """
    return datetime.strptime(dt, "%Y-%m-%dT%H:%M:%S.000Z").strftime("%A")


def get_releases_by_group(data):
    """
    Group releases by project group in the form of a dictionary
    """
    project_grp_dict = {}

    # Loop over each project and get releases
    for project in data:
        group = project.get("project_group")
        releases = project["releases"]

        # Process each release for a project and add to group
        for release in releases:
            if group in project_grp_dict:
                project_grp_dict[group].append(release)
            else:
                project_grp_dict[group] = []
                project_grp_dict[group].append(release)

    return project_grp_dict


def get_successful_releases(releases_by_grp, env):
    """
    Function to return a dictionary of all successful releases for that release version based on the environment given
    """
    success_deploy = {}
    for key in releases_by_grp.keys():
        for rel in releases_by_grp[key]:
            for dep in rel["deployments"]:
                if dep["environment"] == env and dep["state"] == "Success":
                    success_deploy[rel["version"]] = dep["created"]
    return success_deploy


def get_time_diff_from_successful_int_to_live_in_release(success_live, success_int):
    """
    Get the time taken for a successful release from Integration to Live and store it in a dictionary
    with the release version as the key
    """
    time_diff_in_releases = {}
    for key in success_live.keys():
        if key in success_int.keys():
            time_diff_in_releases[key] = (get_datetime(success_live[key]) - get_datetime(success_int[key])).seconds/60
    return time_diff_in_releases


def grp_into_project_grp(releases_by_grp, time_diff_in_releases):
    """
    Group the time taken by each release in a list for each project group and store it in a dictionary
    with the key as the project group
    """
    project_data = {}
    for key in releases_by_grp.keys():
        for rel in releases_by_grp[key]:
            if rel["version"] in time_diff_in_releases:
                if key in project_data:
                    project_data[key].append(time_diff_in_releases[rel["version"]])
                else:
                    project_data[key] = []
                    project_data[key].append(time_diff_in_releases[rel["version"]])
    return project_data


def get_average_then_sort(project_data):
    """
    Get the average time taken for each release in that project group and sort with the longest time taken first
    """
    for key in project_data.keys():
        if len(project_data[key]) != 0:
            project_data[key] = statistics.mean(project_data[key])
    return sort_dictionary(project_data)


def get_unsuccessful_releases_count_then_sort(releases_by_grp, success_live, success_int):
    """
    Loop through all the releases that had successful integration deployments but no successful live ones and store the
    count in a dict with the project group as the key
    """
    unsuccessful_rel = { k : success_int[k] for k in set(success_int) - set(success_live)}
    unsuccessful_rel_by_proj_grp = {}
    for key in releases_by_grp.keys():
        for rel in releases_by_grp[key]:
            if rel["version"] in unsuccessful_rel:
                if key in unsuccessful_rel_by_proj_grp:
                    unsuccessful_rel_by_proj_grp[key] += 1
                else:
                    unsuccessful_rel_by_proj_grp[key] = 1

    return sort_dictionary(unsuccessful_rel_by_proj_grp)


def get_datetime(created):
    return datetime.strptime(created, "%Y-%m-%dT%H:%M:%S.000Z")


def sort_dictionary(dictionary):
    return sorted(dictionary.items(), key=lambda kv: kv[1], reverse=IS_REVERSE)


def get_headers(field1, field2):
    """
    Function to set the headers on the csv file
    """
    field_names = [
        field1,
        field2,
    ]
    return field_names


def write_csv(file_name, field_names, rows):
    """
    Writes to csv file
    """
    with open(file_name, "w") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(field_names)

        for row in rows:
            writer.writerow(row)


def main_function():
    data = load_data()
    days_of_live_deployments = get_day_of_week_deployment_frequency(data)
    write_csv("output/1_deployment_frequency.csv", get_headers("DaysOfWeek", "LiveDeployments"),
              list(days_of_live_deployments.items()))

    slow_releases = get_slow_releases(data)
    write_csv("output/2_slow_releases.csv", get_headers("ProjectGroup", "AverageTimeToLive"), slow_releases)

    failed_releases = get_failed_releases(data)
    write_csv("output/3_failing_releases.csv", get_headers("ProjectGroup", "FailedReleases"), failed_releases)


if __name__ == "__main__":
    main_function()
