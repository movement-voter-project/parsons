import unittest
import requests_mock
from parsons import MobilizeAmerica
from test.utils import validate_list
from unittest.mock import patch
import os


class TestMobilizeAmerica(unittest.TestCase):

    def setUp(self):
        self.MOBILIZE_AMERICA_API_KEY = "1234"

        with patch.dict(os.environ, {"MOBILIZE_AMERICA_API_KEY": self.MOBILIZE_AMERICA_API_KEY}):
            self.ma = MobilizeAmerica()

    def tearDown(self):

        pass

    def test_time_parse(self):

        # Test that Unix conversion works correctly
        self.assertEqual(self.ma._time_parse('<=2018-12-13'), 'lte_1544659200')

        # Test that it throws an error when you put in an invalid filter
        self.assertRaises(ValueError, self.ma._time_parse, '=2018-12-01')

    @requests_mock.Mocker()
    def test_get_organizations(self, m):

        json = {
            "count": 38,
            "next": None,
            "previous": (
                "https://events.mobilizeamerica.io/api/v1/organizations?updated_since=1543644000"),
            "data": [
                        {
                            "id": 1251,
                            "name": "Mike Blake for New York City",
                            "slug": "mikefornyc",
                            "is_coordinated": 'True',
                            "is_independent": 'True',
                            "is_primary_campaign": 'False',
                            "state": "",
                            "district": "",
                            "candidate_name": "",
                            "race_type": "OTHER_LOCAL",
                            "event_feed_url": "https://events.mobilizeamerica.io/mikefornyc/",
                            "created_date": 1545885434,
                            "modified_date": 1546132256
                        }
            ]
        }

        m.get(self.ma.uri + 'organizations', json=json)

        expected = [
            'id', 'name', 'slug', 'is_coordinated', 'is_independent', 'is_primary_campaign',
            'state', 'district', 'candidate_name', 'race_type', 'event_feed_url', 'created_date',
            'modified_date']

        # Assert response is expected structure
        self.assertTrue(validate_list(expected, self.ma.get_organizations()))

    @requests_mock.Mocker()
    def test_get_events(self, m):

        json = {
            'count': 1, 'next': None, 'previous': None,
            'data': [
                {
                    'id': 86738,
                    'description': (
                        'Join our team of volunteers and learn how to engage students in local '
                        'high schools, communicate our mission, and register young voters.'),
                    'timezone': 'America/Chicago',
                    'title': 'Student Voter Initiative Training',
                    'summary': '',
                    'featured_image_url': (
                        'https://mobilizeamerica.imgix.net/uploads/event/'
                        '40667432145_6188839fe3_o_20190102224312253645.jpeg'),
                    'sponsor': {
                        'id': 1076,
                        'name': 'Battleground Texas',
                        'slug': 'battlegroundtexas',
                        'is_coordinated': True,
                        'is_independent': False,
                        'is_primary_campaign': False,
                        'state': '',
                        'district': '',
                        'candidate_name': '',
                        'race_type': None,
                        'event_feed_url': 'https://events.mobilizeamerica.io/battlegroundtexas/',
                        'created_date': 1538590930,
                        'modified_date': 1546468308
                    },
                    'timeslots': [{
                        'id': 526226,
                        'start_date': 1547330400,
                        'end_date': 1547335800}],
                    'location': {
                        'venue': 'Harris County Democratic Party HQ',
                        'address_lines': ['4619 Lyons Ave', ''],
                        'locality': 'Houston',
                        'region': 'TX',
                        'postal_code': '77020',
                        'location': {'latitude': 29.776446, 'longitude': -95.323037},
                        'congressional_district': '18',
                        'state_leg_district': '142',
                        'state_senate_district': None
                    },
                    'event_type': 'TRAINING',
                    'created_date': 1546469706,
                    'modified_date': 1547335800,
                    'browser_url': (
                        'https://events.mobilizeamerica.io/battlegroundtexas/event/86738/'),
                    'high_priority': None,
                    'contact': None,
                    'visibility': 'PUBLIC'
                }
            ]
        }
        m.get(self.ma.uri + 'events', json=json)

        expected = [
            'id', 'description', 'timezone', 'title', 'summary', 'featured_image_url',
            'event_type', 'created_date', 'modified_date', 'browser_url', 'high_priority',
            'contact', 'visibility', 'sponsor_candidate_name', 'sponsor_created_date',
            'sponsor_district', 'sponsor_event_feed_url', 'sponsor_id', 'sponsor_is_coordinated',
            'sponsor_is_independent', 'sponsor_is_primary_campaign', 'sponsor_modified_date',
            'sponsor_name', 'sponsor_race_type', 'sponsor_slug', 'sponsor_state', 'address_lines',
            'congressional_district', 'locality', 'postal_code', 'region', 'state_leg_district',
            'state_senate_district', 'venue', 'latitude', 'longitude', 'timeslots_0_end_date',
            'timeslots_0_id', 'timeslots_0_start_date'
        ]

        # Assert response is expected structure
        self.assertTrue(validate_list(expected, self.ma.get_events()))

    @requests_mock.Mocker()
    def test_get_events_deleted(self, m):

        json = {'count': 2,
                'next': None,
                'previous': None,
                'data': [{'id': 86765,
                          'deleted_date': 1546705971},
                         {'id': 86782,
                          'deleted_date': 1546912779}
                         ]
                }

        m.get(self.ma.uri + 'events/deleted', json=json)

        # Assert response is expected structure
        self.assertTrue(validate_list(['id', 'deleted_date'], self.ma.get_events_deleted()))

    @requests_mock.Mocker()
    def test_get_attendances(self, m):

        json = {'count': 3859,
                'data': [{'attended': True,
                    'created_date': 1641253458,
                    'custom_signup_field_values': [],
                    'event': {'accessibility_notes': None,
                        'accessibility_status': 'NOT_SURE',
                        'address_visibility': 'PUBLIC',
                        'approval_status': 'APPROVED',
                        'browser_url': 'https://www.mobilize.us/mvp/event/434841/',
                        'contact': {'email_address': 'event1host@gmail.com',
                            'name': 'Best Host',
                            'owner_user_id': 111,
                            'phone_number': '2121112222'},
                        'created_by_volunteer_host': True,
                        'created_date': 1641166823,
                        'description': 'You are Invited to Defy the Odds and help '
                        'the Democrats Hold their House and Senate '
                        'Majority.\n'
                        '\n'
                        'Learn about Movement Voter Project (MVP). '
                        'MVP is your trusted source to move 100% '
                        'of your donations to the most effective '
                        'grassroots organizations getting out the '
                        'vote in battleground Senate and House '
                        'Races.\n'
                        '\n'
                        'Learn more here:\n'
                        'https://movement.vote',
                        'event_campaign': None,
                        'event_type': 'FUNDRAISER',
                        'featured_image_url': 'https://mobilizeamerica.imgix.net/uploads/organization/Mobilize%20event%20image%20-%201200%20x%20630px%20-%20MVPAC_20211222234248902257.png',
                        'high_priority': None,
                        'id': 434841,
                        'instructions': 'Thanks for signing up to learn about '
                        'Movement Voter Project and how your '
                        'support can help the Democrats Defy the '
                        'Odds and hold the House and Senate. \n'
                        '\n'
                        'This will be a lively, interesting & '
                        'informative Zoom call. Please consider '
                        'inviting your friends.',
                        'is_virtual': True,
                        'location': {'address_lines': ['123 Main St', ''],
                            'congressional_district': None,
                            'country': 'US',
                            'locality': 'Boulder',
                            'location': {'latitude': 39.1111111,
                                'longitude': -105.111111},
                            'postal_code': '80302',
                            'region': 'CO',
                            'state_leg_district': None,
                            'state_senate_district': None,
                            'venue': ''},
                        'modified_date': 1643853640,
                        'sponsor': {'candidate_name': '',
                                'created_date': 1579801969,
                                'district': '',
                                'event_feed_url': 'https://www.mobilize.us/mvp/',
                                'id': 2311,
                                'is_coordinated': False,
                                'is_independent': True,
                                'is_primary_campaign': False,
                                'logo_url': 'https://mobilize-uploads-prod.s3.us-east-2.amazonaws.com/uploads/organization/MVP%20logo%20-%20with%20map%20-%20transparent%20bg%20-%20750x500_20211027200904507277.png',
                                'modified_date': 1652881884,
                                'name': 'Movement Voter Project',
                                'org_type': 'C4',
                                'race_type': None,
                                'slug': 'mvp',
                                'state': ''},
                        'summary': '',
                                 'tags': None,
                                 'timeslots': None,
                                 'timezone': 'America/Denver',
                                 'title': '"Defy the Odds" Zoom House Party to hold the '
                                          'majority in the House & Senate',
                                 'virtual_action_url': None,
                                 'visibility': 'PUBLIC'},
                       'feedback': None,
                       'id': 1111118,
                       'modified_date': 1643765501,
                       'person': {'blocked_date': None,
                               'created_date': 1635365445,
                               'email_addresses': [{'address': 'attendee1@gmail.com',
                                   'primary': True}],
                               'family_name': 'Guest',
                               'given_name': 'Best',
                               'id': 4837959,
                               'modified_date': 1652396131,
                               'person_id': 4444444,
                               'phone_numbers': [{'number': None, 'primary': True}],
                               'postal_addresses': [{'postal_code': None,
                                   'primary': True}],
                               'sms_opt_in_status': 'UNSPECIFIED',
                               'user_id': 444444},
                       'rating': None,
                       'referrer': {'url': None,
                               'utm_campaign': None,
                               'utm_content': None,
                               'utm_medium': None,
                               'utm_source': None,
                               'utm_term': None},
                       'sponsor': {'candidate_name': '',
                               'created_date': 1579801969,
                               'district': '',
                               'event_feed_url': 'https://www.mobilize.us/mvp/',
                               'id': 2311,
                               'is_coordinated': False,
                               'is_independent': True,
                               'is_primary_campaign': False,
                               'logo_url': 'https://mobilize-uploads-prod.s3.us-east-2.amazonaws.com/uploads/organization/MVP%20logo%20-%20with%20map%20-%20transparent%20bg%20-%20750x500_20211027200904507277.png',
                               'modified_date': 1652881884,
                               'name': 'Movement Voter Project',
                               'org_type': 'C4',
                               'race_type': None,
                               'slug': 'mvp',
                               'state': ''},
                       'status': 'CONFIRMED',
                       'timeslot': {'end_date': 1643765400,
                               'id': 33333,
                               'instructions': None,
                               'is_full': False,
                               'start_date': 1643761800}}
                       ],
             'metadata': {'build_commit': '65c42a2049d6dcb46b8dc3cadf5aa4b359d32874',
                     'page_title': None,
                     'url_name': 'public_organization_attendances'},
             'next': 'https://api.mobilize.us/v1/organizations/2311/attendances?cursor=cD0xODA2NTV3NA%3D%3D&updated_since=1577836800',
             'previous': None}

        next_json = {'count': 3859,
                'data': [{'attended': True,
                    'created_date': 1641424898,
                    'custom_signup_field_values': [],
                    'event': {'accessibility_notes': None,
                        'accessibility_status': 'NOT_SURE',
                        'address_visibility': 'PUBLIC',
                        'approval_status': 'APPROVED',
                        'browser_url': 'https://www.mobilize.us/mvp/event/434831/',
                        'contact': {'email_address': 'event2host@gmail.com',
                            'name': 'Great Host',
                            'owner_user_id': 222333,
                            'phone_number': '9179991177'},
                        'created_by_volunteer_host': True,
                        'created_date': 1641163355,
                        'description': 'Support the best groups organizing to '
                        'advocate for their communities, build '
                        'lasting power, and win elections!\n'
                        '\n'
                        'Movement Voter PAC works to strengthen '
                        'progressive power at all levels of '
                        'government by helping donors – big and '
                        'small – support the best and most '
                        'promising local community-based '
                        'organizations in key states, with a focus '
                        'on youth and communities of color.\n'
                        '\n'
                        'We support hundreds of incredible '
                        'organizations that both turn out unlikely '
                        'voters and organize communities to grow '
                        'their power and create transformation, '
                        'from policy to the streets. We believe '
                        'that supporting local movement vote '
                        'groups is the most effective and most '
                        'cost-effective strategy to transform our '
                        'country.\n'
                        '\n'
                        '--\n'
                        '\n'
                        'Movement Voter PAC is a federal political '
                        'committee that primarily supports the '
                        'political work of local grassroots groups '
                        'organizing to elect progressive '
                        'candidates up and down the ballot.\n'
                        '\n'
                        'Learn more here:\n'
                        'https://movement.vote',
                        'event_campaign': None,
                        'event_type': 'HOUSE_PARTY',
                        'featured_image_url': 'https://mobilizeamerica.imgix.net/uploads/organization/Mobilize%20event%20image%20-%201200%20x%20630px%20-%20MVPAC_20211222234248902257.png',
                        'high_priority': None,
                        'id': 4343434,
                        'instructions': '',
                        'is_virtual': True,
                        'location': {'address_lines': ['', ''],
                                'congressional_district': None,
                                'country': 'US',
                                'locality': 'Ipswich',
                                'location': {'latitude': 42.666666,
                                    'longitude': -70.8888888},
                                'postal_code': '01938',
                                'region': 'MA',
                                'state_leg_district': None,
                                'state_senate_district': None,
                                'venue': ''},
                        'modified_date': 1645146344,
                             'sponsor': {'candidate_name': '',
                                     'created_date': 1579801969,
                                     'district': '',
                                     'event_feed_url': 'https://www.mobilize.us/mvp/',
                                     'id': 2311,
                                     'is_coordinated': False,
                                     'is_independent': True,
                                     'is_primary_campaign': False,
                                     'logo_url': 'https://mobilize-uploads-prod.s3.us-east-2.amazonaws.com/uploads/organization/MVP%20logo%20-%20with%20map%20-%20transparent%20bg%20-%20750x500_20211027200904507277.png',
                                     'modified_date': 1652881884,
                                     'name': 'Movement Voter Project',
                                     'org_type': 'C4',
                                     'race_type': None,
                                     'slug': 'mvp',
                                     'state': ''},
                             'summary': '',
                             'tags': None,
                             'timeslots': None,
                             'timezone': 'America/New_York',
                             'title': 'House Party for Movement Voter PAC',
                             'virtual_action_url': None,
                             'visibility': 'PUBLIC'},
                   'feedback': 'Bravo!!!',
                   'id': 1777777,
                   'modified_date': 1645488034,
                   'person': {'blocked_date': None,
                           'created_date': 1635365445,
                           'email_addresses': [{'address': 'attendee2@gmail.com',
                               'primary': True}],
                           'family_name': 'Guest',
                           'given_name': 'Great',
                           'id': 777777,
                           'modified_date': 1652396131,
                           'person_id': 888888,
                           'phone_numbers': [{'number': None, 'primary': True}],
                           'postal_addresses': [{'postal_code': None,
                               'primary': True}],
                           'sms_opt_in_status': 'UNSPECIFIED',
                           'user_id': 444444},
                   'rating': 'Positive',
                   'referrer': {'url': 'https://www.google.com/',
                           'utm_campaign': None,
                           'utm_content': None,
                           'utm_medium': None,
                           'utm_source': None,
                           'utm_term': None},
                   'sponsor': {'candidate_name': '',
                           'created_date': 1579801969,
                           'district': '',
                           'event_feed_url': 'https://www.mobilize.us/mvp/',
                           'id': 2311,
                           'is_coordinated': False,
                           'is_independent': True,
                           'is_primary_campaign': False,
                           'logo_url': 'https://mobilize-uploads-prod.s3.us-east-2.amazonaws.com/uploads/organization/MVP%20logo%20-%20with%20map%20-%20transparent%20bg%20-%20750x500_20211027200904507277.png',
                           'modified_date': 1652881884,
                           'name': 'Movement Voter Project',
                           'org_type': 'C4',
                           'race_type': None,
                           'slug': 'mvp',
                           'state': ''},
                   'status': 'CONFIRMED',
                   'timeslot': {'end_date': 1645059600,
                           'id': 3030303,
                           'instructions': None,
                           'is_full': False,
                           'start_date': 1645056000}}
                   ],
         'metadata': {'build_commit': '65c42a2049d6dcb46b8dc3cadf5aa4b359d32874',
                 'page_title': None,
                 'url_name': 'public_organization_attendances'},
         'next': '',
         'previous': 'https://api.mobilize.us/v1/organizations/2311/attendances?cursor=cj0xJnA9MTywNjY1Nzk%3D&1577836800&updated_since=1577836800'}

        m.get(self.ma.uri + 'organizations/2311/attendances', headers={"Authorization": "Bearer " + self.MOBILIZE_AMERICA_API_KEY}, json=json)
        m.get(json["next"], request_headers={"Authorization": "Bearer " + self.MOBILIZE_AMERICA_API_KEY}, json=next_json)

        expected = ['attended', 'created_date', 'custom_signup_field_values', 'event', 'feedback', 'id', 'modified_date', 'person', 'rating', 'referrer', 'sponsor', 'status', 'timeslot']
        # Assert response is expected structure
        self.assertTrue(validate_list(expected, self.ma.get_attendances(organization_id=2311, updated_since=1577836800)))
