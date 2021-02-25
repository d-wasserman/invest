import os
import json
import unittest

TEST_DATA_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'invest-test-data')


class EndpointFunctionTests(unittest.TestCase):
    """Tests for some UI server endpoint functions.

    Other endpoints have tests in the workbench repo. These ones need 
    vector/raster test data so it makes more sense to have them here.
    """

    def test_get_vector_colnames(self):
        """UI server: getVectorColnames endpoint"""
        from natcap.invest import ui_server
        test_client = ui_server.app.test_client()
        # an empty path
        response = test_client.post('/colnames', json={'vector_path': ''})
        colnames = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 422)
        self.assertEqual(colnames, [])
        # a vector with one column
        path = os.path.join(
            TEST_DATA_PATH, 'aquaculture', 'Input', 'Finfish_Netpens.shp')
        response = test_client.post('/colnames', json={'vector_path': path})
        colnames = json.loads(response.get_data(as_text=True))
        self.assertEqual(colnames, ['FarmID'])
        # a non-vector file
        path = os.path.join(TEST_DATA_PATH, 'ndr', 'input', 'dem.tif')
        response = test_client.post('/colnames', json={'vector_path': path})
        colnames = json.loads(response.get_data(as_text=True))
        self.assertEqual(response.status_code, 422)
        self.assertEqual(colnames, [])

    def test_get_vector_may_have_points(self):
        """UI server: getVectorMayHavePoints endpoint"""
        from natcap.invest import ui_server
        test_client = ui_server.app.test_client()
        # an empty path
        response = test_client.post(
            '/vector_may_have_points', 
            json={'vector_path': ''})
        may_have_points = json.loads(
            response.get_data(as_text=True))['may_have_points']
        self.assertEqual(response.status_code, 422)
        self.assertEqual(may_have_points, False)
        # a vector with no point geometries
        path = os.path.join(
            TEST_DATA_PATH, 'aquaculture', 'Input', 'Finfish_Netpens.shp')
        response = test_client.post(
            '/vector_may_have_points', 
            json={'vector_path': path})
        may_have_points = json.loads(
            response.get_data(as_text=True))['may_have_points']
        self.assertEqual(may_have_points, False)
        # a vector with point geometries
        path = os.path.join(
            TEST_DATA_PATH, 'delineateit', 'input', 'outlets.shp')
        response = test_client.post(
            '/vector_may_have_points', 
            json={'vector_path': path})
        may_have_points = json.loads(
            response.get_data(as_text=True))['may_have_points']
        self.assertEqual(may_have_points, True)
        # a non-vector file
        path = os.path.join(TEST_DATA_PATH, 'ndr', 'input', 'dem.tif')
        response = test_client.post(
            '/vector_may_have_points', 
            json={'vector_path': path})
        may_have_points = json.loads(
            response.get_data(as_text=True))['may_have_points']
        self.assertEqual(response.status_code, 422)
        self.assertEqual(may_have_points, False)