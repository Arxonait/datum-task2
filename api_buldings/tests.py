from math import inf

from django.contrib.gis.geos import Polygon
from django.test import TestCase

from api_buldings.models import Building

# Create your tests here.
TEST_GEOM = "POLYGON ((19.298488064150035 43.510902041818866, 19.528309386031935 43.24686866222709, 20.179459092915266 42.82572783537185, 19.298488064150035 43.510902041818866))"
TEST_POLYGON = ((19.298488064150035, 43.510902041818866),
                (19.528309386031935, 43.24686866222709),
                (20.179459092915266, 42.82572783537185),
                (19.298488064150035, 43.510902041818866))
NOT_CLOSED_POLYGON = ((19.298488064150035, 43.510902041818866),
                      (19.528309386031935, 43.24686866222709),
                      (20.179459092915266, 42.82572783537185))
TEST_POINT1 = (39.67012990906166436, 47.21085518012574767)
TEST_POINT2 = (39.67416330589383477, 47.21440557674531391)


class BuildingsCRUDTestsCollection(TestCase):
    fixtures = ["buildings"]

    def test_create_wkt(self):
        url = "/api/buildings/"

        data = {
            "address": "test",
            "geom": TEST_GEOM
        }

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201)

    def test_create_feature(self):
        url = "/api/buildings/"

        geo_json = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [TEST_POLYGON]
            },
            "properties": {"address": "test"}
        }

        response = self.client.post(url, data=geo_json, content_type="application/json")
        self.assertEqual(response.status_code, 201)

    def test_create_not_close_polygon(self):
        url = "/api/buildings/"

        geo_json = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [NOT_CLOSED_POLYGON]
            },
            "properties": {"address": "test"}
        }

        response = self.client.post(url, data=geo_json, content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_delete_buildings(self):
        url = "/api/buildings/13/"
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 204)

    def test_put_buildings_wkt(self):
        url = "/api/buildings/14/"
        change_address = "new address"
        response = self.client.put(url,
                                   data={
                                       "address": change_address,
                                       "geom": TEST_GEOM
                                   },
                                   content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["properties"].get("address"), change_address)

    def test_put_buildings_feature(self):
        url = "/api/buildings/14/"
        change_address = "new address 2"

        geo_json = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [TEST_POLYGON]
            },
            "properties": {"address": change_address}
        }

        response = self.client.put(url, data=geo_json, content_type="application/json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["properties"].get("address"), change_address)

    def test_get_buildings(self):
        url = "/api/buildings/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        count = len(Building.objects.all())
        count_response = len(response.json()["features"])
        self.assertEqual(count, count_response)

    def test_get_target_building_and_format_feature(self):
        url = "/api/buildings/14/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIsInstance(data.get("type"), str)
        self.assertEqual(data.get("type"), "Feature")
        self.assertIsInstance(data.get("geometry"), dict)
        self.assertIsInstance(data["geometry"].get("coordinates"), list)
        self.assertIsInstance(data["geometry"].get("type"), str)
        self.assertEqual(data["geometry"].get("type").lower(), "polygon")
        self.assertIsInstance(data.get("properties"), dict)

    def test_get_target_building_not_found(self):
        url = "/api/buildings/50/"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class BuildingsFilterTestsCollection(TestCase):
    fixtures = ["buildings"]

    def test_building_area(self):
        url = "/api/buildings/13/?area"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "area", 1)

    def test_get_target_building_area_with_filter(self):
        min_area = 500
        url = f"/api/buildings/13/?area&{min_area=}"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "area", 1)
        self.assertGreater(response.json()["properties"]["area"], min_area)

    def test_get_buildings_filtrate(self):

        # test_data --- min area, max area
        test_data = [(500, 2000), (1000, None), (None, 1000), (5000, 2000)]

        for min_area, max_area in test_data:
            url = f"/api/buildings/?area&"
            if min_area is not None:
                url += f"{min_area=}&"
            else:
                min_area = 0
            if max_area is not None:
                url += f"{max_area=}&"
            else:
                max_area = inf

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            features = response.json()["features"]

            for feature in features:
                feature_area = feature["properties"]["area"]
                self.assertGreater(max_area, feature_area)
                self.assertLess(min_area, feature_area)

    def test_get_target_building_with_filter_point(self):
        longitude, latitude = TEST_POINT1
        max_distance = 50
        url = f"/api/buildings/13/?{max_distance=}&{longitude=}&{latitude=}"

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Feature")

    def test_get_buildings_with_wrong_format_filter_point(self):
        longitude_t, latitude_t = TEST_POINT1
        max_distance_t = 3000
        test_data = [(None, latitude_t, max_distance_t),
                     (longitude_t, None, max_distance_t), ]
        count = len(Building.objects.all())

        for longitude, latitude, max_distance in test_data:
            url = f"/api/buildings/?"
            if longitude is not None:
                url += f"{longitude=}&"
            if latitude is not None:
                url += f"{latitude=}&"
            if max_distance is not None:
                url += f"{max_distance=}&"

            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

            count_response = len(response.json()["features"])
            self.assertEqual(count, count_response)
            self.assertNotContains(response, "distance")

    def test_get_buildings_with_filter_point(self):
        longitude_t1, latitude_t1 = TEST_POINT1
        longitude_t2, latitude_t2 = TEST_POINT2
        test_data = [(longitude_t1, latitude_t1, 200),
                     (longitude_t1, latitude_t1, 50),
                     (longitude_t1, latitude_t1, 1000),
                     (longitude_t2, latitude_t2, 200),
                     (longitude_t2, latitude_t2, 500),
                     (longitude_t2, latitude_t2, 2000)]

        for longitude, latitude, max_distance in test_data:
            url = f"/api/buildings/?{max_distance=}&{longitude=}&{latitude=}"
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            features = response.json()["features"]
            for feature in features:
                distance_to_target_point = feature["properties"]["distance"]
                self.assertLess(distance_to_target_point, max_distance)

    def test_get_calc_field_area(self):
        url = f"/api/buildings/13/?area&"
        response = self.client.get(url)
        data = response.json()
        self.assertIsInstance(data["properties"].get("area"), float)

    def test_get_calc_field_distance_target_point(self):
        longitude, latitude = TEST_POINT1
        url = f"/api/buildings/13/?{longitude=}&{latitude=}"
        response = self.client.get(url)
        data = response.json()
        self.assertIsInstance(data["properties"].get("distance"), float)
