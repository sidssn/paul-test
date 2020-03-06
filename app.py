import json
from datetime import datetime
import statistics
import csv

days_of_week = {'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 'Friday': 0, 'Saturday': 0, 'Sunday': 0}


# Loads data in the json file and returns data in the form of a dictionary
def load_data():
    with open("projects.json") as file:
        return json.load(file)["projects"]


# Returns the list of weekdays that the live deployment was made
def get_live_deployment_days(data):
    list_of_dates = []
    for rel in data:
        for release in rel['releases']:
            for dep in release['deployments']:
                if dep['environment'] == 'Live':
                    list_of_dates.append(get_weekday_of_date(dep['created']))
    return list_of_dates


# Returns weekday from the date of deployment
def get_weekday_of_date(dt):
    return datetime.strptime(dt, '%Y-%m-%dT%H:%M:%S.000Z').strftime('%A')


def get_day_of_deployment_frequency(data):
    for day_of_week in get_live_deployment_days(data):
        if day_of_week in days_of_week:
            days_of_week[day_of_week] += 1
    return days_of_week


# Group releases by project group in the form of a dictionary
def get_releases_by_group(data):
    proj_grp_dict = {}

    # Loop over each project and get releases
    for proj in data:
        group = proj.get("project_group")
        releases = proj["releases"]

        # Process each release for a project and add to group
        for release in releases:
            if group in proj_grp_dict:
                proj_grp_dict[group].append(release)
            else:
                proj_grp_dict[group] = []
                proj_grp_dict[group].append(release)

    return proj_grp_dict


def get_slow_releases(data):
    releases_by_grp = get_releases_by_group(data)
    # Get all successful releases to Integration
    success_int = get_successful_releases(releases_by_grp, 'Integration')

    # Get all successful releases to Live
    success_live = get_successful_releases(releases_by_grp, 'Live')

    print(success_live)
    print(success_int)
    return get_time_diff_between_successful_releases(releases_by_grp, success_live, success_int)


# Function to return a dictionary of all successful releases for that release version based on the environment given
def get_successful_releases(releases_by_grp, env):
    success_deploy = {}
    for key in releases_by_grp.keys():
        for rel in releases_by_grp[key]:
            for dep in rel['deployments']:
                if dep['environment'] == env and dep['state'] == 'Success':
                    success_deploy[rel['version']] = dep['created']
    return success_deploy


# Get the time taken for a successful release from Integration to Live and store it in a dictionary
# with the release version as the key
def get_time_diff_between_successful_releases(releases_by_grp, success_live, success_int):
    time_diff_in_releases = {}
    for key in success_live.keys():
        if key in success_int.keys():
            time_diff_in_releases[key] = (get_datetime(success_live[key]) - get_datetime(success_int[key])).seconds/60
    print(time_diff_in_releases)
    return grp_into_proj_grp(releases_by_grp, time_diff_in_releases)


# Group the time taken by each release in a list for each project group and store it in a dictionary
# with the key as the project group
def grp_into_proj_grp(releases_by_grp, time_diff_in_releases):
    proj_data = {}
    for key in releases_by_grp.keys():
        for rel in releases_by_grp[key]:
            if rel['version'] in time_diff_in_releases:
                if key in proj_data:
                    proj_data[key].append(time_diff_in_releases[rel['version']])
                else:
                    proj_data[key] = []
                    proj_data[key].append(time_diff_in_releases[rel['version']])
    print(str(proj_data))
    return get_average(proj_data)


# Get the average time taken for each release in that project group and sort with the longest time taken first
def get_average(proj_data):
    for key in proj_data.keys():
        if len(proj_data[key]) != 0:
            proj_data[key] = statistics.mean(proj_data[key])
    return sort_in_descending(proj_data)


# Gets the list of all the failed releases by project group
def get_failed_releases(data):
    releases_by_grp = get_releases_by_group(data)
    success_int = get_successful_releases(releases_by_grp, 'Integration')
    success_live = get_successful_releases(releases_by_grp, 'Live')
    return get_unsuccessful_releases_count(releases_by_grp,success_live, success_int)


# Loop through all the releases that had successful integration deployments but no successful live ones and store the
# count in a dict with the project group as the key
def get_unsuccessful_releases_count(releases_by_grp, success_live, success_int):
    unsuccessful_rel = { k : success_int[k] for k in set(success_int) - set(success_live)}
    unsuccessful_rel_by_proj_grp = {}
    for key in releases_by_grp.keys():
        for rel in releases_by_grp[key]:
            if rel['version'] in unsuccessful_rel:
                if key in unsuccessful_rel_by_proj_grp:
                    unsuccessful_rel_by_proj_grp[key] += 1
                else:
                    unsuccessful_rel_by_proj_grp[key] = 1

    return sort_in_descending(unsuccessful_rel_by_proj_grp)


def get_datetime(created):
    return datetime.strptime(created, '%Y-%m-%dT%H:%M:%S.000Z')


def sort_in_descending(nvm):
    return  sorted(nvm.items(), key=lambda kv: kv[1], reverse=True)


# Function to set the headers on the csv file
def get_headers(field1, field2):
    field_names = [
        field1,
        field2,
    ]
    return field_names


#Wrties to csv file
def write_csv(file_name, field_names, rows):
    with open(file_name, 'w') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(field_names)

        for row in rows:
            print(row)
            writer.writerow(row)


if __name__ == '__main__':
    data = load_data()
    days_of_live = get_day_of_deployment_frequency(data)
    print(list(days_of_live.items()))
    write_csv('output/1_deployment_frequency.csv', get_headers('DaysOfWeek', 'LiveDeployments'), list(days_of_live.items()))

    slow_releases = get_slow_releases(data)
    print(slow_releases)
    write_csv('output/2_slow_releases.csv', get_headers('ProjectGroup', 'AverageTimeToLive'), slow_releases)

    failed_releases = get_failed_releases(data)
    print(failed_releases)
    write_csv('output/3_failing_releases.csv', get_headers('ProjectGroup', 'FailedReleases'), failed_releases)

