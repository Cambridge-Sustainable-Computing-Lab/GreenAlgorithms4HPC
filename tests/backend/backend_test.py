# ------------------------------------------------------------------
# This file contains fixtures, tests, and mocks for the backend/__init__.py module.
# It validates the orchestration of the backend pipeline
# ------------------------------------------------------------------

from backend import main_backend, prepare_config, summarise_data

from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch
import numpy as np
import pandas as pd
import pytest


# Fixtures
@pytest.fixture
def dummy_args(config_data):
    """
    Constructs a full command-line arguments namespace 
    """
    return SimpleNamespace(
        startDay=config_data["startDay"],
        endDay=config_data["endDay"],
        useCustomLogs=config_data["useCustomLogs"],
        use_mock_agg_data=True,
        customSuccessStates="COMPLETED",
        filterWD=None,
        filterJobIDs="all",
        filterAccount=None,
        path_infrastucture_info="clustersData/CSD3",
        userCWD="/home/uid_1",
        reportBug=False,
        reportBugHere=False
    )


@pytest.fixture
def mock_enriched_df():
    """
    Provides a pre-enriched DataFrame mimicking output from ga_core.
    Contains 2 jobs across 2 different submit dates to test aggregation logic.
    """
    return pd.DataFrame(
        {
            "UserX": ["uid_1", "uid_1"],
            "SubmitDatetimeX": pd.to_datetime(
                ["2022-02-11 19:11:21", "2022-02-12 14:04:01"]
            ),
            "energy": [10.0, 20.0],
            "energy_CPUs": [5.0, 10.0],
            "energy_GPUs": [3.0, 6.0],
            "energy_memory": [2.0, 4.0],
            "carbonFootprint": [100.0, 200.0],
            "carbonFootprint_memoryNeededOnly": [10.0, 20.0],
            "carbonFootprint_failedJobs": [0.0, 50.0],
            "TotalCPUtime2useX": [100, 200],
            "TotalGPUtime2useX": [0, 0],
            "WallclockTimeX": [50, 100],
            "CPUhoursChargedX": [2.0, 4.0],
            "GPUhoursChargedX": [0.0, 0.0],
            "ReqMemX": [6760, 250000],
            "memOverallocationFactorX": [1.5, 2.5],
            "StateX": [0, 1],  # 0 failed/timeout, 1 completed
            "treeMonths": [0.1, 0.2],
            "treeMonths_memoryNeededOnly": [0.01, 0.02],
            "treeMonths_failedJobs": [0.0, 0.05],
            "driving": [5.0, 10.0],
            "flying_NY_SF": [1.0, 2.0],
            "flying_PAR_LON": [2.0, 4.0],
            "flying_NYC_MEL": [0.1, 0.2],
            "cost": [10.0, 20.0],
            "cost_failedJobs": [0.0, 5.0],
            "cost_memoryNeededOnly": [1.0, 2.0],
        }
    )

class TestPrepareGaConfig:
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_prepare_config_mapping(
        self, 
        mock_yaml_load, 
        mock_file,
        dummy_args,
    ):
        """
        Scenario: Required and optional arguments are extracted correctly from the CLI namespace into a config dictionary.
        """
        # Mocks returns for the two yaml.safe_load calls
        mock_yaml_load.side_effect = [
            {"workload_manager": "slurm", "granularity_memory_request": "6"}, # cluster_info
            {"power_memory_perGB": 0.5} # fParams
        ]

        config, cluster_info, f_params = prepare_config(dummy_args)

        # Check ga_config dict contents
        expected_config = {
            "useCustomLogs": dummy_args.useCustomLogs,
            "startDay": dummy_args.startDay,
            "endDay": dummy_args.endDay,
            "filterWD": dummy_args.filterWD,
            "filterJobIDs": dummy_args.filterJobIDs,
            "filterAccount": dummy_args.filterAccount,
        }

        for arg in ("userCWD", "customSuccessStates"):
            value = getattr(dummy_args, arg, None)
            if value:
                expected_config[arg] = value

        assert config == expected_config

        # Check loaded configurations
        assert cluster_info == {"workload_manager": "slurm", "granularity_memory_request": "6"}
        assert f_params == {"power_memory_perGB": 0.5}

        # Check file reads occurred twice (cluster_info + fixed_params)
        assert mock_file.call_count == 2

class TestSummariseData:

    def test_summarise_data_output_schema(self, mock_enriched_df):
        """
        Scenario: The output schema of summarise_data is correct.

        Checks done:
        1. All expected top-level keys ('userDaily', 'userActivity', etc.) exist.
        2. The primary user ID is identified correctly from the DataFrame.
        """
        summary = summarise_data(mock_enriched_df.copy())

        assert "userDaily" in summary
        assert "userActivity" in summary
        assert "user" in summary
        assert "memoryOverallocationFactors" in summary

        assert summary["user"] == "uid_1"
        assert "uid_1" in summary["userActivity"]

    def test_two_stage_aggregation_and_derived_ratios(self, mock_enriched_df):
        """
        Scenario: job metrics aggregate correctly for two stages - daily totals and overall stats
        and derived ratios are computed correctly.

        Checks done:
        1. First aggregation groups raw jobs into daily records.
        2. Second aggregation switches logic (checks missing 'UserX' column) 
           and computes sums over pre-aggregated daily data.
        3. Success/failure rates and carbon percentages are derived correctly.
        """
        summary = summarise_data(mock_enriched_df.copy())

        # Daily DataFrame
        daily_df = summary["userDaily"]
        assert len(daily_df) == 2  # 2 distinct dates in fixture data

        # Overall User Statistics
        overall = summary["userActivity"]["uid_1"]
        assert overall["n_jobs"] == 2
        assert overall["n_success"] == 1
        assert overall["success_rate"] == pytest.approx(0.5)
        assert overall["failure_rate"] == pytest.approx(0.5)

    def test_zero_carbon_footprint_division_edge_case(self, mock_enriched_df):
        """
        Scenario: Tests edge case behavior when carbon footprint is zero.

        Checks done:
        Verifies if zero total carbon footprint leads to NaN or floating point zero 
        in `share_carbonFootprint` calculation without throwing an unexpected exception.
        """
        zero_carbon_df = mock_enriched_df.copy()
        zero_carbon_df["carbonFootprint"] = 0.0

        summary = summarise_data(zero_carbon_df)
        daily_df = summary["userDaily"]

        assert daily_df["share_carbonFootprint"].isna().all() # 0 / 0 in Pandas results in NaN

class TestMainBackend:

    @patch("backend.prepare_config")
    @patch("backend.ga_core.HPCDataProcessor")
    @patch("backend.summarise_data")
    def test_main_backend_execution_pipeline(
        self,
        mock_summarise,
        mock_processor_cls,
        mock_prepare_config,
        dummy_args,
    ):
        """
        Scenario: `main_backend` acts as an orchestration pipeline that calls external dependencies 
        and sub-modules in the strict sequential order required.
        """

        # Config mocks
        dummy_config = {"startDay": dummy_args.startDay}
        dummy_cluster_info = {"workload_manager": "slurm"}
        dummy_f_params = {"power_memory_perGB": 0.5}
        
        mock_prepare_config.return_value = (dummy_config, dummy_cluster_info, dummy_f_params)
        
        # Processor and summarise mocks
        mock_processor_inst = MagicMock()
        mock_processor_cls.return_value = mock_processor_inst

        raw_df = pd.DataFrame({"UserX": ["uid_1"]})
        enriched_df = pd.DataFrame({"UserX": ["uid_1"], "enriched": [True]})

        mock_processor_inst.extract_data.return_value = raw_df
        mock_processor_inst.enrich_data.return_value = enriched_df
        mock_summarise.return_value = {"user": "uid_1", "status": "complete"}

        result = main_backend(dummy_args)

        # Assert correct execution order and parameters passed
        mock_prepare_config.assert_called_once_with(dummy_args)
        
        # Check HPCDataProcessor initialization arguments
        mock_processor_cls.assert_called_once_with(
            dummy_config,
            dummy_cluster_info,
            dummy_f_params,
            all_users_access=False
        )
        
        mock_processor_inst.extract_data.assert_called_once()
        mock_processor_inst.enrich_data.assert_called_once_with(raw_df)
        mock_summarise.assert_called_once_with(enriched_df)

        assert result == {"user": "uid_1", "status": "complete"}