from pydantic import field_validator, BaseModel
from pathlib import Path
from typing import List, Optional, Tuple, Union, Sequence

from mdocfile.utils import find_section_entries, find_title_entries


class MdocGlobalData(BaseModel):
    """Data model for global data in a SerialEM mdoc file.

    https://bio3d.colorado.edu/SerialEM/hlp/html/about_formats.htm
    """
    DataMode: Optional[int] = None
    ImageSize: Optional[Tuple[int, int]] = None
    Montage: Optional[bool] = None
    ImageSeries: Optional[int] = None
    ImageFile: Optional[Path] = None
    PixelSpacing: Optional[float] = None
    Voltage: Optional[float] = None

    @field_validator('ImageSize', mode="before")
    @classmethod
    def multi_number_string_to_tuple(cls, value: str):
        return tuple(value.split())

    @classmethod
    def from_lines(cls, lines: List[str]):
        lines = [
            line for line in lines
            if len(line) > 0
        ]
        key_value_pairs = [
            line.split('=') for line in lines
            if not line.startswith('[T =')
        ]
        key_value_pairs = [
            (k.strip(), v.strip()) for k, v in key_value_pairs
        ]
        data = {k: v for k, v in key_value_pairs}
        return cls(**data)

    def to_string(self):
        lines = []
        for k, v in self.model_dump().items():
            if v is None:
                continue
            if isinstance(v, tuple):
                v = ' '.join(str(el) for el in v)
            if v == 'nan':
                v = 'NaN'
            lines.append(f'{k} = {v}')
        return '\n'.join(lines)


class MdocSectionData(BaseModel):
    """Data model for section data in a SerialEM mdoc file.

    https://bio3d.colorado.edu/SerialEM/hlp/html/about_formats.htm
    """
    # headers
    ZValue: Optional[int] = None
    MontSection: Optional[int] = None
    FrameSet: Optional[int] = None

    # section data
    TiltAngle: Optional[float] = None
    PieceCoordinates: Optional[Tuple[float, float, int]] = None
    StagePosition: Optional[Tuple[float, float]] = None
    StageZ: Optional[float] = None
    Magnification: Optional[float] = None
    CameraLength: Optional[float] = None
    MagIndex: Optional[int] = None
    Intensity: Optional[float] = None
    SuperMontCoords: Optional[Tuple[float, float]] = None
    PixelSpacing: Optional[float] = None
    ExposureDose: Optional[float] = None
    DoseRate: Optional[float] = None
    SpotSize: Optional[float] = None
    Defocus: Optional[float] = None
    TargetDefocus: Optional[float] = None
    ImageShift: Optional[Tuple[float, float]] = None
    RotationAngle: Optional[float] = None
    ExposureTime: Optional[float] = None
    Binning: Optional[float] = None
    UsingCDS: Optional[bool] = None
    CameraIndex: Optional[int] = None
    DividedBy2: Optional[bool] = None
    LowDoseConSet: Optional[int] = None
    MinMaxMean: Optional[Tuple[float, float, float]] = None
    PriorRecordDose: Optional[float] = None
    XedgeDxy: Optional[Tuple[float, float]] = None
    YedgeDxy: Optional[Tuple[float, float]] = None
    XedgeDxyVS: Optional[Union[Tuple[float, float], Tuple[float, float, float]]] = None
    YedgeDxyVS: Optional[Union[Tuple[float, float], Tuple[float, float, float]]] = None
    StageOffsets: Optional[Tuple[float, float]] = None
    AlignedPieceCoords: Optional[Union[Tuple[float, float], Tuple[float, float, float]]] = None
    AlignedPieceCoordsVS: Optional[
        Union[Tuple[float, float], Tuple[float, float, float]]] = None
    SubFramePath: Optional[Path] = None
    NumSubFrames: Optional[int] = None
    FrameDosesAndNumbers: Optional[Sequence[Tuple[float, int]]] = None
    DateTime: Optional[str] = None
    NavigatorLabel: Optional[str] = None
    FilterSlitAndLoss: Optional[Tuple[float, float]] = None
    ChannelName: Optional[str] = None
    MultiShotHoleAndPosition: Optional[Union[Tuple[int, int], Tuple[int, int, int]]] = None
    CameraPixelSize: Optional[float] = None
    Voltage: Optional[float] = None

    @field_validator(
        'PieceCoordinates',
        'SuperMontCoords',
        'ImageShift',
        'MinMaxMean',
        'StagePosition',
        'XedgeDxy',
        'YedgeDxy',
        'XedgeDxyVS',
        'YedgeDxyVS',
        'StageOffsets',
        'AlignedPieceCoords',
        'AlignedPieceCoordsVS',
        'FrameDosesAndNumbers',
        'FilterSlitAndLoss',
        'MultiShotHoleAndPosition',
        mode="before")
    @classmethod
    def multi_number_string_to_tuple(cls, value: str):
        return tuple(value.split())

    @classmethod
    def from_lines(cls, lines: List[str]):
        lines = [line.strip('[]')
                 for line
                 in lines
                 if len(line) > 0]
        key_value_pairs = [line.split('=') for line in lines]
        key_value_pairs = [
            (k.strip(), v.strip())
            for k, v
            in key_value_pairs
        ]
        lines = {k: v for k, v in key_value_pairs}
        return cls(**lines)

    def to_string(self):
        data = self.model_dump()
        z_value = data.pop('ZValue')
        lines = [f'[ZValue = {z_value}]']
        for k, v in data.items():
            if v is None:
                continue
            elif isinstance(v, tuple):
                v = ' '.join(str(el) for el in v)
            elif v == 'nan':
                v = 'NaN'
            lines.append(f'{k} = {v}')
        return '\n'.join(lines)


class Mdoc(BaseModel):
    titles: List[str]
    global_data: MdocGlobalData
    section_data: List[MdocSectionData]

    @classmethod
    def from_file(cls, filename: str):
        with open(filename) as file:
            lines = [line.strip() for line in file.readlines()]
        split_idxs = find_section_entries(lines)
        split_idxs.append(len(lines))

        header_lines = lines[0:split_idxs[0]]
        title_idxs = find_title_entries(header_lines)

        titles = [header_lines[idx] for idx in title_idxs]
        global_data = MdocGlobalData.from_lines(header_lines)
        section_data = [
            MdocSectionData.from_lines(lines[start_idx:end_idx])
            for start_idx, end_idx
            in zip(split_idxs, split_idxs[1:])
        ]
        return cls(titles=titles, global_data=global_data, section_data=section_data)

    def to_string(self):
        """
        Generate the string representation of the Mdoc data
        """
        return '\n\n'.join([
            self.global_data.to_string(),
            '\n\n'.join(self.titles),
            '\n\n'.join(section.to_string() for section in self.section_data),
        ])
