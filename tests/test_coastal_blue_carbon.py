# -*- coding: utf-8 -*-
"""Tests for Coastal Blue Carbon Functions."""
import unittest
import os
import shutil
import csv

import numpy as np
from osgeo import gdal
from pygeoprocessing import geoprocessing as geoprocess
import pygeoprocessing.testing as pygeotest
from pygeoprocessing.testing import scm

SAMPLE_DATA = os.path.join(
    os.path.dirname(__file__), '..', 'data', 'invest-data')


lulc_lookup_list = \
    [['lulc-class', 'code', 'is_coastal_blue_carbon_habitat'],
     ['n', '0', 'False'],
     ['x', '1', 'True'],
     ['y', '2', 'True'],
     ['z', '3', 'True']]

lulc_lookup_list_unreadable = \
    [['lulc-class', 'code', 'is_coastal_blue_carbon_habitat'],
     ['n', '0', ''],
     ['x', '1', 'True'],
     ['y', '2', 'True'],
     ['z', '3', 'True']]

lulc_lookup_list_no_ones = \
    [['lulc-class', 'code', 'is_coastal_blue_carbon_habitat'],
     ['n', '0', 'False'],
     ['y', '2', 'True'],
     ['z', '3', 'True']]

lulc_transition_matrix_list = \
    [['lulc-class', 'n', 'x', 'y', 'z'],
     ['n', 'NCC', 'accum', 'accum', 'accum'],
     ['x', 'med-impact-disturb', 'accum', 'accum', 'accum'],
     ['y', 'med-impact-disturb', 'accum', 'accum', 'accum'],
     ['z', 'med-impact-disturb', 'accum', 'accum', 'accum']]

carbon_pool_initial_list = \
    [['code', 'lulc-class', 'biomass', 'soil', 'litter'],
     ['0', 'n', '0', '0', '0'],
     ['1', 'x', '5', '5', '0.5'],
     ['2', 'y', '10', '10', '0.5'],
     ['3', 'z', '20', '20', '0.5']]

carbon_pool_transient_list = \
    [['code', 'lulc-class', 'biomass-half-life', 'biomass-med-impact-disturb',
        'biomass-yearly-accumulation',
        'soil-half-life',
        'soil-med-impact-disturb',
        'soil-yearly-accumulation'],
     ['0', 'n', '0', '0', '0', '0', '0', '0'],
     ['1', 'x', '1', '0.5', '1', '1', '0.5', '1.1'],
     ['2', 'y', '1', '0.5', '2', '1', '0.5', '2.1'],
     ['3', 'z', '1', '0.5', '1', '1', '0.5', '1.1']]

price_table_list = \
    [['year', 'price'],
     [2000, 20]]

NODATA_INT = -9999


def _read_array(raster_path):
    """"Read raster as array."""
    ds = gdal.Open(raster_path)
    band = ds.GetRasterBand(1)
    a = band.ReadAsArray()
    ds = None
    return a


def _create_table(uri, rows_list):
    """Create csv file from list of lists."""
    with open(uri, 'w') as f:
        writer = csv.writer(f)
        writer.writerows(rows_list)
    return uri


def _create_workspace():
    """Create workspace directory."""
    path = os.path.dirname(os.path.realpath(__file__))
    workspace = os.path.join(path, 'workspace')
    if os.path.exists(workspace):
        shutil.rmtree(workspace)
    os.mkdir(workspace)
    return workspace


def _get_args():
    """Create and return arguements for CBC main model.

    Returns:
        args (dict): main model arguements
    """
    band_matrices = [np.ones((2, 2))]
    band_matrices_two = [np.ones((2, 2)) * 2]
    band_matrices_with_nodata = [np.ones((2, 2))]
    band_matrices_with_nodata[0][0][0] = NODATA_INT
    srs = pygeotest.sampledata.SRS_WILLAMETTE

    workspace = _create_workspace()
    lulc_lookup_uri = _create_table(
        os.path.join(workspace, 'lulc_lookup.csv'), lulc_lookup_list)
    lulc_transition_matrix_uri = _create_table(
        os.path.join(workspace, 'lulc_transition_matrix.csv'),
        lulc_transition_matrix_list)
    carbon_pool_initial_uri = _create_table(
        os.path.join(workspace, 'carbon_pool_initial.csv'),
        carbon_pool_initial_list)
    carbon_pool_transient_uri = _create_table(
        os.path.join(workspace, 'carbon_pool_transient.csv'),
        carbon_pool_transient_list)
    raster_0_uri = pygeotest.create_raster_on_disk(
        band_matrices,
        srs.origin,
        srs.projection,
        NODATA_INT,
        srs.pixel_size(100),
        datatype=gdal.GDT_Int32,
        filename=os.path.join(workspace, 'raster_0.tif'))
    raster_1_uri = pygeotest.create_raster_on_disk(
        band_matrices_with_nodata,
        srs.origin,
        srs.projection,
        NODATA_INT,
        srs.pixel_size(100),
        datatype=gdal.GDT_Int32,
        filename=os.path.join(workspace, 'raster_1.tif'))
    raster_2_uri = pygeotest.create_raster_on_disk(
        band_matrices_two,
        srs.origin,
        srs.projection,
        NODATA_INT,
        srs.pixel_size(100),
        datatype=gdal.GDT_Int32,
        filename=os.path.join(workspace, 'raster_2.tif'))
    lulc_baseline_map_uri = raster_0_uri
    lulc_transition_maps_list = [raster_1_uri, raster_2_uri]

    args = {
        'workspace_dir': workspace,
        'results_suffix': 'test',
        'lulc_lookup_uri': lulc_lookup_uri,
        'lulc_transition_matrix_uri': lulc_transition_matrix_uri,
        'lulc_baseline_map_uri': raster_0_uri,
        'lulc_transition_maps_list': [raster_1_uri, raster_2_uri],
        'lulc_transition_years_list': [2000, 2005],
        'analysis_year': 2010,
        'carbon_pool_initial_uri': carbon_pool_initial_uri,
        'carbon_pool_transient_uri': carbon_pool_transient_uri,
        'do_economic_analysis': True,
        'do_price_table': False,
        'price': 2.,
        'interest_rate': 5.,
        'price_table_uri': None,
        'discount_rate': 2.
    }

    return args


def _get_preprocessor_args(args_choice):
    """Create and return arguments for preprocessor model.

    Args:
        args_choice (int): which arguments to return

    Returns:
        args (dict): preprocessor arguments
    """
    band_matrices_zeros = [np.zeros((2, 2))]
    band_matrices_ones = [np.ones((2, 2))]
    band_matrices_nodata = [np.ones((2, 2)) * NODATA_INT]
    srs = pygeotest.sampledata.SRS_WILLAMETTE

    workspace = _create_workspace()

    lulc_lookup_uri = _create_table(
        os.path.join(workspace, 'lulc_lookup.csv'), lulc_lookup_list)

    raster_0_uri = pygeotest.create_raster_on_disk(
        band_matrices_ones, srs.origin, srs.projection, NODATA_INT,
        srs.pixel_size(100), datatype=gdal.GDT_Int32,
        filename=os.path.join(workspace, 'raster_0.tif'))
    raster_1_uri = pygeotest.create_raster_on_disk(
        band_matrices_ones, srs.origin, srs.projection, NODATA_INT,
        srs.pixel_size(100), datatype=gdal.GDT_Int32,
        filename=os.path.join(workspace, 'raster_1.tif'))
    raster_2_uri = pygeotest.create_raster_on_disk(
        band_matrices_ones, srs.origin, srs.projection, NODATA_INT,
        srs.pixel_size(100), datatype=gdal.GDT_Int32,
        filename=os.path.join(workspace, 'raster_2.tif'))
    raster_3_uri = pygeotest.create_raster_on_disk(
        band_matrices_zeros, srs.origin, srs.projection, NODATA_INT,
        srs.pixel_size(100), datatype=gdal.GDT_Int32,
        filename=os.path.join(workspace, 'raster_3.tif'))
    raster_nodata_uri = pygeotest.create_raster_on_disk(
        band_matrices_nodata, srs.origin, srs.projection, NODATA_INT,
        srs.pixel_size(100), datatype=gdal.GDT_Int32,
        filename=os.path.join(workspace, 'raster_4.tif'))

    args = {
        'workspace_dir': workspace,
        'results_suffix': 'test',
        'lulc_lookup_uri': lulc_lookup_uri,
        'lulc_snapshot_list': [raster_0_uri, raster_1_uri, raster_2_uri]
    }

    args2 = {
        'workspace_dir': workspace,
        'results_suffix': 'test',
        'lulc_lookup_uri': lulc_lookup_uri,
        'lulc_snapshot_list': [raster_0_uri, raster_1_uri, raster_3_uri]
    }

    args3 = {
        'workspace_dir': workspace,
        'results_suffix': 'test',
        'lulc_lookup_uri': lulc_lookup_uri,
        'lulc_snapshot_list': [raster_0_uri, raster_nodata_uri, raster_3_uri]
    }

    if args_choice == 1:
        return args
    elif args_choice == 2:
        return args2
    else:
        return args3


class TestPreprocessor(unittest.TestCase):
    """Test Coastal Blue Carbon preprocessor library functions."""

    def test_create_carbon_pool_transient_table_template(self):
        """Coastal Blue Carbon: Test creation of transient table template."""
        from natcap.invest.coastal_blue_carbon import preprocessor
        args = _get_preprocessor_args(1)
        filepath = os.path.join(args['workspace_dir'], 'transient_temp.csv')
        code_to_lulc_dict = {1: 'one', 2: 'two', 3: 'three'}
        preprocessor._create_carbon_pool_transient_table_template(
            filepath, code_to_lulc_dict)
        transient_dict = geoprocess.get_lookup_from_table(filepath, 'code')
        # demonstrate that output table contains all input land cover classes
        for i in [1, 2, 3]:
            self.assertTrue(i in transient_dict.keys())

    def test_preprocessor_ones(self):
        """Coastal Blue Carbon: Test entire run of preprocessor.

        All rasters contain ones.
        """
        from natcap.invest.coastal_blue_carbon import preprocessor
        args = _get_preprocessor_args(1)
        preprocessor.execute(args)
        trans_csv = os.path.join(
            args['workspace_dir'],
            'outputs_preprocessor',
            'transitions_test.csv')
        with open(trans_csv, 'r') as f:
            lines = f.readlines()
        # just a regression test.  this tests that an output file was
        # successfully created, and demonstrates that one land class transition
        # does not occur and the other is set in the right direction.
        self.assertTrue(lines[2].startswith('x,,accum'))

    def test_preprocessor_zeros(self):
        """Coastal Blue Carbon: Test entire run of preprocessor.

        First two rasters contain ones, last contains zeros.
        """
        from natcap.invest.coastal_blue_carbon import preprocessor
        args2 = _get_preprocessor_args(2)
        preprocessor.execute(args2)
        trans_csv = os.path.join(
            args2['workspace_dir'],
            'outputs_preprocessor',
            'transitions_test.csv')
        with open(trans_csv, 'r') as f:
            lines = f.readlines()

        # just a regression test.  this tests that an output file was
        # successfully created, and that two particular land class transitions
        # occur and are set in the right directions.
        self.assertTrue(lines[2][:].startswith('x,disturb,accum'))

    def test_preprocessor_nodata(self):
        """Coastal Blue Carbon: Test entire run of preprocessor.

        First raster contains ones, second nodata, third zeros.
        """
        from natcap.invest.coastal_blue_carbon import preprocessor
        args = _get_preprocessor_args(3)
        preprocessor.execute(args)
        trans_csv = os.path.join(
            args['workspace_dir'],
            'outputs_preprocessor',
            'transitions_test.csv')
        with open(trans_csv, 'r') as f:
            lines = f.readlines()
        # just a regression test.  this tests that an output file was
        # successfully created, and that two particular land class transitions
        # occur and are set in the right directions.
        self.assertTrue(lines[2][:].startswith('x,,'))

    def test_lookup_parsing_exception(self):
        """Coastal Blue Carbon: Test lookup table parsing exception."""
        from natcap.invest.coastal_blue_carbon import preprocessor
        args = _get_preprocessor_args(1)
        _create_table(args['lulc_lookup_uri'], lulc_lookup_list_unreadable)
        with self.assertRaises(ValueError):
            preprocessor.execute(args)

    def test_raster_validation(self):
        """Coastal Blue Carbon: Test raster validation."""
        from natcap.invest.coastal_blue_carbon import preprocessor
        args = _get_preprocessor_args(1)
        OTHER_NODATA = -1
        srs = pygeotest.sampledata.SRS_WILLAMETTE
        band_matrices_with_nodata = [np.ones((2, 2)) * OTHER_NODATA]
        raster_wrong_nodata = pygeotest.create_raster_on_disk(
            band_matrices_with_nodata,
            srs.origin,
            srs.projection,
            OTHER_NODATA,
            srs.pixel_size(100),
            datatype=gdal.GDT_Int32,
            filename=os.path.join(
                args['workspace_dir'], 'raster_wrong_nodata.tif'))
        args['lulc_snapshot_list'][0] = raster_wrong_nodata
        with self.assertRaises(ValueError):
            preprocessor.execute(args)

    def test_raster_values_not_in_lookup_table(self):
        """Coastal Blue Carbon: Test raster values not in lookup table."""
        from natcap.invest.coastal_blue_carbon import preprocessor
        args = _get_preprocessor_args(1)
        _create_table(args['lulc_lookup_uri'], lulc_lookup_list_no_ones)
        with self.assertRaises(ValueError):
            preprocessor.execute(args)

    def test_mark_transition_type(self):
        """Coastal Blue Carbon: Test mark_transition_type."""
        from natcap.invest.coastal_blue_carbon import preprocessor
        args = _get_preprocessor_args(1)

        band_matrices_zero = [np.zeros((2, 2))]
        srs = pygeotest.sampledata.SRS_WILLAMETTE
        raster_zeros = pygeotest.create_raster_on_disk(
            band_matrices_zero,
            srs.origin,
            srs.projection,
            NODATA_INT,
            srs.pixel_size(100),
            datatype=gdal.GDT_Int32,
            filename=os.path.join(
                args['workspace_dir'], 'raster_1.tif'))
        args['lulc_snapshot_list'][0] = raster_zeros

        preprocessor.execute(args)
        trans_csv = os.path.join(
            args['workspace_dir'],
            'outputs_preprocessor',
            'transitions_test.csv')
        with open(trans_csv, 'r') as f:
            lines = f.readlines()
        self.assertTrue(lines[1][:].startswith('n,NCC,accum'))

    def test_mark_transition_type_nodata_check(self):
        """Coastal Blue Carbon: Test mark_transition_type."""
        from natcap.invest.coastal_blue_carbon import preprocessor
        args = _get_preprocessor_args(1)

        band_matrices_zero = [np.zeros((2, 2))]
        srs = pygeotest.sampledata.SRS_WILLAMETTE
        raster_zeros = pygeotest.create_raster_on_disk(
            band_matrices_zero,
            srs.origin,
            srs.projection,
            NODATA_INT,
            srs.pixel_size(100),
            datatype=gdal.GDT_Int32,
            filename=os.path.join(
                args['workspace_dir'], 'raster_1.tif'))
        args['lulc_snapshot_list'][0] = raster_zeros
        preprocessor.execute(args)

    @scm.skip_if_data_missing(SAMPLE_DATA)
    def test_binary(self):
        """Coastal Blue Carbon: Test main model run against InVEST-Data."""
        from natcap.invest.coastal_blue_carbon import preprocessor

        sample_data_path = os.path.join(SAMPLE_DATA, 'CoastalBlueCarbon')
        raster_0_uri = os.path.join(
            sample_data_path,
            'inputs/GBJC_2004_mean_Resample.tif')
        raster_1_uri = os.path.join(
            sample_data_path, 'inputs/GBJC_2050_mean_Resample.tif')
        raster_2_uri = os.path.join(
            sample_data_path, 'inputs/GBJC_2100_mean_Resample.tif')
        args = {
            'workspace_dir': _create_workspace(),
            'results_suffix': '',
            'lulc_lookup_uri': os.path.join(
                sample_data_path,
                'inputs/lulc_lookup.csv'),
            'lulc_snapshot_list': [raster_0_uri, raster_1_uri, raster_2_uri]
        }
        preprocessor.execute(args)

    def tearDown(self):
        """Remove workspace."""
        shutil.rmtree(os.path.join(
            os.path.dirname(os.path.realpath(__file__)), 'workspace'))


class TestIO(unittest.TestCase):
    """Test Coastal Blue Carbon io library functions."""

    def setUp(self):
        """Create arguments."""
        self.args = _get_args()

    def test_get_inputs(self):
        """Coastal Blue Carbon: Test get_inputs function in IO module."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc
        d = cbc.get_inputs(self.args)
        # check several items in the data dictionary to check that the inputs
        # are properly fetched.
        self.assertTrue(d['lulc_to_Hb'][0] == 0.0)
        self.assertTrue(d['lulc_to_Hb'][1] == 1.0)
        self.assertTrue(len(d['price_t']) == 11)
        self.assertTrue(len(d['snapshot_years']) == 3)
        self.assertTrue(len(d['transition_years']) == 2)

    def test_get_price_table_exception(self):
        """Coastal Blue Carbon: Test price table exception."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc
        self.args['price_table_uri'] = os.path.join(
            self.args['workspace_dir'], 'price.csv')
        self.args['do_price_table'] = True
        self.args['price_table_uri'] = _create_table(
            self.args['price_table_uri'], price_table_list)
        with self.assertRaises(KeyError):
            cbc.get_inputs(self.args)

    def test_chronological_order_exception(self):
        """Coastal Blue Carbon: Test exception checking chronological order."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc
        self.args['lulc_transition_years_list'] = [2005, 2000]
        with self.assertRaises(ValueError):
            cbc.get_inputs(self.args)

    def test_chronological_order_exception_analysis_year(self):
        """Coastal Blue Carbon: Test exception checking analysis year order."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc
        self.args['analysis_year'] = 2000
        with self.assertRaises(ValueError):
            cbc.get_inputs(self.args)

    def test_create_transient_dict(self):
        """Coastal Blue Carbon: Test function to read transient table."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc
        biomass_transient_dict, soil_transient_dict = \
            cbc._create_transient_dict(self.args['carbon_pool_transient_uri'])
        # check that function can properly parse table of transient carbon pool
        # values.
        self.assertTrue(1 in biomass_transient_dict.keys())
        self.assertTrue(1 in soil_transient_dict.keys())

    def test_get_lulc_trans_to_D_dicts(self):
        """Coastal Blue Carbon: Test function to read transient table."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc
        biomass_transient_dict, soil_transient_dict = \
            cbc._create_transient_dict(self.args['carbon_pool_transient_uri'])
        lulc_transition_uri = self.args['lulc_transition_matrix_uri']
        lulc_lookup_uri = self.args['lulc_lookup_uri']
        lulc_trans_to_Db, lulc_trans_to_Ds = cbc._get_lulc_trans_to_D_dicts(
            lulc_transition_uri,
            lulc_lookup_uri,
            biomass_transient_dict,
            soil_transient_dict)

        # check that function can properly parse table of transient carbon pool
        # values.
        self.assertTrue((3.0, 0.0) in lulc_trans_to_Db.keys())
        self.assertTrue((3.0, 0.0) in lulc_trans_to_Ds.keys())

    def tearDown(self):
        """Remove workspace."""
        shutil.rmtree(self.args['workspace_dir'])


class TestModel(unittest.TestCase):
    """Test Coastal Blue Carbon main model functions."""

    def setUp(self):
        """Create arguments."""
        self.args = _get_args()

    def test_model_run(self):
        """Coastal Blue Carbon: Test run function in main model."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc
        cbc.execute(self.args)
        netseq_output_raster = os.path.join(
            self.args['workspace_dir'],
            'outputs_core/total_net_carbon_sequestration_test.tif')
        npv_output_raster = os.path.join(
            self.args['workspace_dir'],
            'outputs_core/net_present_value_test.tif')
        netseq_array = _read_array(netseq_output_raster)
        npv_array = _read_array(npv_output_raster)

        # (Explanation for why netseq is 31.)
        # LULC Code: Baseline: 1 --> Year 2000: 1, Year 2005: 2,  Year 2010: 2
        # Initial Stock from Baseline: 5+5=10
        # Sequest:
        #    2000-->2005: (1+1.1)*5=10.5, 2005-->2010: (2+2.1)*5=20.5
        #       Total: 10.5 + 20.5 = 31.
        netseq_test = np.array([[np.nan, 31.], [31., 31.]])
        npv_test = np.array(
            [[np.nan, 60.27801514], [60.27801514, 60.27801514]])

        # just a simple regression test.  this demonstrates that a NaN value
        # will properly propagate across the model. the npv raster was chosen
        # because the values are determined by multiple inputs, and any changes
        # in those inputs would propagate to this raster.
        np.testing.assert_array_almost_equal(
            netseq_array, netseq_test, decimal=4)
        np.testing.assert_array_almost_equal(
            npv_array, npv_test, decimal=4)

    def test_model_run_2(self):
        """Coastal Blue Carbon: Test run function in main model."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc
        self.args['analysis_year'] = None
        cbc.execute(self.args)
        netseq_output_raster = os.path.join(
            self.args['workspace_dir'],
            'outputs_core/total_net_carbon_sequestration_test.tif')
        npv_output_raster = os.path.join(
            self.args['workspace_dir'],
            'outputs_core/net_present_value_test.tif')
        netseq_array = _read_array(netseq_output_raster)
        npv_array = _read_array(npv_output_raster)

        # (Explanation for why netseq is 10.5.)
        # LULC Code: Baseline: 1 --> Year 2000: 1, Year 2005: 2
        # Initial Stock from Baseline: 5+5=10
        # Sequest:
        #    2000-->2005: (1+1.1)*5=10.5
        netseq_test = np.array([[np.nan, 10.5], [10.5, 10.5]])

        # just a simple regression test.  this demonstrates that a NaN value
        # will properly propagate across the model. the npv raster was chosen
        # because the values are determined by multiple inputs, and any changes
        # in those inputs would propagate to this raster.
        np.testing.assert_array_almost_equal(
            netseq_array, netseq_test, decimal=4)

    @scm.skip_if_data_missing(SAMPLE_DATA)
    def test_binary(self):
        """Coastal Blue Carbon: Test main model run against InVEST-Data."""
        from natcap.invest.coastal_blue_carbon \
            import coastal_blue_carbon as cbc

        sample_data_path = os.path.join(SAMPLE_DATA, 'CoastalBlueCarbon')
        args = {
            'workspace_dir': self.args['workspace_dir'],
            'analysis_year': 2100,
            'carbon_pool_initial_uri': os.path.join(
                sample_data_path,
                'outputs_preprocessor/carbon_pool_initial_sample.csv'),
            'carbon_pool_transient_uri': os.path.join(
                sample_data_path,
                'outputs_preprocessor/carbon_pool_transient_sample.csv'),
            'discount_rate': 6.0,
            'do_economic_analysis': True,
            'do_price_table': True,
            'interest_rate': 3.0,
            'lulc_lookup_uri': os.path.join(
                sample_data_path,
                'inputs/lulc_lookup.csv'),
            'lulc_baseline_map_uri': os.path.join(
                sample_data_path,
                'inputs/GBJC_2004_mean_Resample.tif'),
            'lulc_transition_maps_list': [
                os.path.join(sample_data_path,
                             'inputs/GBJC_2050_mean_Resample.tif'),
                os.path.join(
                    sample_data_path,
                    'inputs/GBJC_2100_mean_Resample.tif')],
            'price_table_uri': os.path.join(
                sample_data_path, 'inputs/price_table.csv'),
            'lulc_transition_matrix_uri': os.path.join(
                sample_data_path,
                'outputs_preprocessor/transitions_sample.csv'),
            'lulc_transition_years_list': [2004, 2050],
            'price': 10.0,
            'results_suffix': '150225'
        }
        cbc.execute(args)
        npv_raster = os.path.join(
            os.path.join(
                args['workspace_dir'],
                'outputs_core/net_present_value_150225.tif'))
        npv_array = _read_array(npv_raster)

        # this is just a regression test, but it will capture all values
        # in the net present value raster.  the npv raster was chosen because
        # the values are determined by multiple inputs, and any changes in
        # those inputs would propagate to this raster.
        u = np.unique(npv_array)
        u.sort()
        a = np.array([-3.935801e+04, -2.052500e+04, -1.788486e+04,
                      -1.787341e+04, 0.0, 1.145100e+01, 3.724291e+03,
                      3.743750e+03, 3.770121e+03])
        a.sort()
        np.testing.assert_array_almost_equal(u, a, decimal=2)

    def tearDown(self):
        """Remove workspace."""
        shutil.rmtree(self.args['workspace_dir'])


if __name__ == '__main__':
    unittest.main()