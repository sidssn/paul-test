import json
import unittest
from app import (get_successful_releases, get_releases_by_group, get_time_diff_from_successful_int_to_live_in_release,
                 get_unsuccessful_releases_count, write_csv, get_headers)
import filecmp, os


def load_data():
    with open("unit_tests/test.json") as file:
        return json.load(file)


class TestStringMethods(unittest.TestCase):

    def test_success_releases(self):
        releases_by_grp = get_releases_by_group(load_data())
        self.assertEqual(get_successful_releases(releases_by_grp, 'Integration'), {'0.0.2': '2015-02-22T22:41:00.000Z', '0.0.3': '2015-02-23T11:01:04.000Z', '0.0.4': '2015-02-24T13:04:04.000Z', '0.0.5': '2015-02-24T16:34:03.000Z', '0.0.6': '2015-02-24T16:34:03.000Z', '0.0.7': '2015-02-24T16:56:01.000Z', '1.0.22.32': '2015-02-25T08:57:04.000Z', '1.0.24.34': '2015-03-03T14:50:05.000Z'})

    def test_time_diff(self):
        releases_by_grp = get_releases_by_group(load_data())
        time_diff_dict = get_time_diff_from_successful_int_to_live_in_release(get_successful_releases(releases_by_grp, 'Integration'), get_successful_releases(releases_by_grp, 'Live'))
        self.assertEqual(time_diff_dict, {'1.0.22.32': 1138.0333333333333, '1.0.24.34': 227.01666666666668})

    def test_unsuccessful_count(self):
        releases_by_grp = get_releases_by_group(load_data())
        unsuccessful_count = get_unsuccessful_releases_count(releases_by_grp, get_successful_releases(releases_by_grp, 'Live'), get_successful_releases(releases_by_grp, 'Integration'))
        self.assertEqual(unsuccessful_count['Vouliagmeni'], 6)

    def test_csv_creation(self):
        test_data = [('Monday', 2), ('Tuesday', 3)]
        write_csv("unit_tests/test_actual.csv", get_headers("Day", "TestCount"), test_data)
        self.assertTrue(filecmp.cmp('unit_tests/test_expected.csv', 'unit_tests/test_actual.csv'))
        os.remove('unit_tests/test_actual.csv')


if __name__ == '__main__':
    unittest.main()
