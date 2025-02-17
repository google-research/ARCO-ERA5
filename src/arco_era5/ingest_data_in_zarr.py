# Copyright 2023 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import logging
import os

from .utils import replace_non_alphanumeric_with_hyphen, subprocess_run

logger = logging.getLogger(__name__)

AR_FILE_PATH = '/arco-era5/src/update-ar-data.py'
CO_FILE_PATH = '/arco-era5/src/update-co-data.py'
CO_FILES_MAPPING = {
    'model-level-moisture': ['o3q', 'qrqs'],
    'model-level-wind': ['dve', 'tw'],
    'single-level-forecast': ['rad', 'pcp_surface_cp', 'pcp_surface_crr',
                              'pcp_surface_csf', 'pcp_surface_csfr', 'pcp_surface_es',
                              'pcp_surface_lsf', 'pcp_surface_lsp', 'pcp_surface_lspf',
                              'pcp_surface_lsrr', 'pcp_surface_lssfr',
                              'pcp_surface_ptype', 'pcp_surface_rsn', 'pcp_surface_sd',
                              'pcp_surface_sf', 'pcp_surface_smlt', 'pcp_surface_tp'],
    'single-level-reanalysis': ['cape', 'cisst', 'sfc', 'tcol',
                                'soil_depthBelowLandLayer_istl1',
                                'soil_depthBelowLandLayer_istl2',
                                'soil_depthBelowLandLayer_istl3',
                                'soil_depthBelowLandLayer_istl4',
                                'soil_depthBelowLandLayer_stl1',
                                'soil_depthBelowLandLayer_stl2',
                                'soil_depthBelowLandLayer_stl3',
                                'soil_depthBelowLandLayer_stl4',
                                'soil_depthBelowLandLayer_swvl1',
                                'soil_depthBelowLandLayer_swvl2',
                                'soil_depthBelowLandLayer_swvl3',
                                'soil_depthBelowLandLayer_swvl4',
                                'soil_surface_tsn'],
    'single-level-surface': ['lnsp', 'zs']
}


def ingest_data_in_zarr_dataflow_job(target_path: str, region: str, start_date: str,
                                     end_date: str, init_date: str, project: str,
                                     bucket: str, sdk_container_image: str,  python_path: str) -> None:
    """Ingests data into a Zarr store and runs a Dataflow job.

    Args:
        target_path (str): The target Zarr store path.
        region (str): The region in which this job will run.
        start_date (str): The start date in the format 'YYYY-MM-DD'.
        end_date (str): The end date in the format 'YYYY-MM-DD'.
        init_date (str): The initial date of the zarr store in the format of str.

    Returns:
        None
    """
    job_name = target_path.split('/')[-1]
    job_name = os.path.splitext(job_name)[0]
    job_name = (
        f"zarr-data-ingestion-{replace_non_alphanumeric_with_hyphen(job_name)}-{start_date}-to-{end_date}"
    )
    if '/ar/' in target_path:
        logger.info(f"Data ingestion for {target_path} of AR data.")
        command = (
            f"{python_path} {AR_FILE_PATH} --output_path {target_path} "
            f"-s {start_date} -e {end_date} --pressure_levels_group full_37 "
            f"--temp_location gs://{bucket}/temp --runner DataflowRunner "
            f"--project {project} --region {region} --experiments use_runner_v2 "
            f"--worker_machine_type n2-highmem-32 --disk_size_gb 250 "
            f"--setup_file /arco-era5/setup.py "
            f"--job_name {job_name} --number_of_worker_harness_threads 1 "
            f"--init_date {init_date}")
    else:
        chunks = CO_FILES_MAPPING[target_path.split('/')[-1].split('.')[0]]
        chunks = " ".join(chunks)
        time_per_day = 2 if 'single-level-forecast' in target_path else 24
        logger.info(f"Data ingestion for {target_path} of CO data.")
        command = (
            f"{python_path} {CO_FILE_PATH} --output_path {target_path} "
            f"-s {start_date} -e {end_date} -c {chunks} "
            f"--time_per_day {time_per_day} "
            f"--temp_location gs://{bucket}/temp --runner DataflowRunner "
            f"--project {project} --region {region} --experiments use_runner_v2 "
            f"--worker_machine_type n2-highmem-8 --disk_size_gb 250 "
            f"--setup_file /arco-era5/setup.py "
            f"--job_name {job_name} --number_of_worker_harness_threads 1 "
            f"--sdk_container_image {sdk_container_image} "
            f"--init_date {init_date}")

    subprocess_run(command)
