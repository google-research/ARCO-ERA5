import apache_beam as beam
import logging
import subprocess
import tempfile
import os
import datetime
import xarray as xr
import zarr as zr
from dataclasses import dataclass
from contextlib import contextmanager
import calendar

logger = logging.getLogger(__name__)

variable_dict = {
    'dve': ['d', 'vo'], # model-level-wind
    'tw': ['t', 'w'],
    'o3q': ['q', 'o3', 'clwc', 'ciwc', 'cc'], # model-level-moisture
    'qrqs': ['crwc', 'cswc'],
    'lnsp': ['lnsp'], # single-level-surface
    'zs': ['z'],
    'cape': ['cape', 'p79.162', 'p80.162'], # single-level-reanalysis
    'cisst': ['siconc', 'sst', 'skt'],
    'sfc': ['z', 'sp', 'tcwv', 'msl', 'tcc', 'u10', 'v10', 't2m', 'd2m', 'lcc', 'mcc', 'hcc', 'u100', 'v100'],
    'tcol': ['tclw', 'tciw', 'tcw', 'tcwv', 'tcrw', 'tcsw'],
    'soil_depthBelowLandLayer_istl1': ['istl1'],
    'soil_depthBelowLandLayer_istl2': ['istl2'],
    'soil_depthBelowLandLayer_istl3': ['istl3'],
    'soil_depthBelowLandLayer_istl4': ['istl4'],
    'soil_depthBelowLandLayer_stl1': ['stl1'],
    'soil_depthBelowLandLayer_stl2': ['stl2'],
    'soil_depthBelowLandLayer_stl3': ['stl3'],
    'soil_depthBelowLandLayer_stl4': ['stl4'],
    'soil_depthBelowLandLayer_swvl1': ['swvl1'],
    'soil_depthBelowLandLayer_swvl2': ['swvl2'],
    'soil_depthBelowLandLayer_swvl3': ['swvl3'],
    'soil_depthBelowLandLayer_swvl4': ['swvl4'],
    'soil_surface_tsn': ['tsn'],
    'rad': ['ssrd', 'strd', 'str', 'ttr', 'gwd'], # single-level-forecast
    'pcp_surface_cp': ['cp'],
    'pcp_surface_crr': ['crr'],
    'pcp_surface_csf': ['csf'],
    'pcp_surface_csfr': ['csfr'],
    'pcp_surface_es': ['es'],
    'pcp_surface_lsf': ['lsf'],
    'pcp_surface_lsp': ['lsp'],
    'pcp_surface_lspf': ['lspf'],
    'pcp_surface_lsrr': ['lsrr'],
    'pcp_surface_lssfr': ['lssfr'],
    'pcp_surface_ptype': ['ptype'],
    'pcp_surface_rsn': ['rsn'],
    'pcp_surface_sd': ['sd'],
    'pcp_surface_sf': ['sf'],
    'pcp_surface_smlt': ['smlt'],
    'pcp_surface_tp': ['tp']
}

def convert_to_date(date_str: str, format: str = '%Y-%m-%d'):
    return datetime.datetime.strptime(date_str, format)

def copy(src: str, dst: str):
    cmd = 'gcloud alpha storage cp'
    try:
        subprocess.run(cmd.split() + [src, dst], check=True, capture_output=True, text=True, input="n/n")
        return
    except subprocess.CalledProcessError as e:
        msg = f"Failed to copy file {src!r} to {dst!r} Error {e}"
        logger.error(msg)

@contextmanager
def opener(fname: str):
    _, suffix = os.path.splitext(fname)
    with tempfile.NamedTemporaryFile(suffix=suffix) as ntf:
        tmp_name = ntf.name
        logger.info(f"Copying '{fname}' to local file '{tmp_name}'")
        copy(fname, tmp_name)
        yield tmp_name

@dataclass
class GenerateOffset(beam.PTransform):

    init_date: str = '1900-01-01'
    timestamps_per_file: int = 24
    is_single_level: bool = False

    def apply(self, url: str):
        # generate start offset
        file_name = url.rsplit('/', 1)[1].rsplit('.', 1)[0]
        int_date, chunk = file_name.split('_hres_')
        if "_" in chunk:
            chunk = chunk.replace(".grb2_", "_")
        if self.is_single_level:
            int_date += "01"
        start_date = convert_to_date(int_date, '%Y%m%d')
        days_diff = start_date - convert_to_date(self.init_date)
        start = days_diff.days * self.timestamps_per_file
        end = start + self.timestamps_per_file * (calendar.monthrange(start_date.year, start_date.month)[1] if self.is_single_level else 1)
        return url, slice(start, end), variable_dict[chunk]

    def expand(self, pcoll: beam.PCollection) -> beam.PCollection:
        return pcoll | beam.Map(self.apply)


@dataclass
class UpdateSlice(beam.PTransform):

    target: str

    def apply(self, file_slice):
        url, region, vars = file_slice
        zf = zr.open(self.target)
        with opener(url) as file:
            logger.info(f"Opened {url}")
            ds = xr.open_dataset(file, engine='cfgrib')
            for vname in vars:
                logger.info(f"Started {vname} from {url}")
                zv = zf[vname]
                zv[region] = ds[vname].values
                logger.info(f"Done {vname} from {url}")
            logger.info(f"Finished for {url}")
            del zv
            del ds

    def expand(self, pcoll: beam.PCollection) -> beam.PCollection:
        return pcoll | beam.Map(self.apply)