import unittest
from src.profiles import CareerProfile, MANUFACTURING_PM, distance_km, evaluate

class ProfileTests(unittest.TestCase):
    def test_management_and_coordination_are_equal(self):
        for title in ("Manufacturing Project Manager", "Manufacturing Project Coordinator"):
            self.assertTrue(evaluate({"title":title,"remote":True}, MANUFACTURING_PM)["role_match"])

    def test_excludes_it_titles(self):
        self.assertFalse(evaluate({"title":"IT Project Manager","remote":True}, MANUFACTURING_PM)["role_match"])

    def test_zero_distance(self):
        self.assertEqual(distance_km((-22.78,-47.29),(-22.78,-47.29)), 0)

    def test_remote_without_coordinates(self):
        result=evaluate({"title":"Project Coordinator","remote":True},MANUFACTURING_PM)
        self.assertEqual(result["location_status"],"remote_check_country")

    def test_onsite_unknown_location_not_assumed_eligible(self):
        result=evaluate({"title":"Project Coordinator","remote":False},MANUFACTURING_PM)
        self.assertFalse(result["eligible_for_location_filter"])
        self.assertEqual(result["location_status"],"distance_unknown")

    def test_radius_filter(self):
        p=CareerProfile("test",["project manager"],origin_coordinates=(-22.78,-47.29),max_commute_km=20)
        self.assertTrue(evaluate({"title":"Project Manager","coordinates":(-22.78,-47.29)},p)["eligible_for_location_filter"])
        self.assertFalse(evaluate({"title":"Project Manager","coordinates":(-23.55,-46.63)},p)["eligible_for_location_filter"])

if __name__=="__main__": unittest.main()
