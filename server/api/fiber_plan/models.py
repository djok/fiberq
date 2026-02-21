from datetime import datetime

from pydantic import BaseModel


class SpliceClosureCreate(BaseModel):
    muf_fid: int | None = None
    closure_type: str = "dome"
    closure_model: str = ""
    tray_count: int = 0
    max_splices: int | None = None
    project_id: int


class SpliceClosureOut(BaseModel):
    id: int
    muf_fid: int | None
    closure_type: str | None
    closure_model: str | None
    tray_count: int | None
    max_splices: int | None
    project_id: int | None


class SpliceTrayCreate(BaseModel):
    closure_id: int
    tray_number: int
    tray_type: str = "12F"
    capacity: int = 12


class SpliceTrayOut(BaseModel):
    id: int
    closure_id: int
    tray_number: int
    tray_type: str | None
    capacity: int | None


class SpliceCreate(BaseModel):
    tray_id: int
    position_in_tray: int
    cable_a_layer_id: str | None = None
    cable_a_fid: int | None = None
    fiber_a_number: int | None = None
    fiber_a_color: str = ""
    tube_a_number: int | None = None
    tube_a_color: str = ""
    cable_b_layer_id: str | None = None
    cable_b_fid: int | None = None
    fiber_b_number: int | None = None
    fiber_b_color: str = ""
    tube_b_number: int | None = None
    tube_b_color: str = ""
    splice_type: str = "fusion"
    loss_db: float | None = None
    status: str = "planned"
    notes: str = ""


class SpliceOut(BaseModel):
    id: int
    tray_id: int
    position_in_tray: int
    cable_a_layer_id: str | None
    cable_a_fid: int | None
    fiber_a_number: int | None
    fiber_a_color: str | None
    tube_a_number: int | None
    tube_a_color: str | None
    cable_b_layer_id: str | None
    cable_b_fid: int | None
    fiber_b_number: int | None
    fiber_b_color: str | None
    tube_b_number: int | None
    tube_b_color: str | None
    splice_type: str | None
    loss_db: float | None
    status: str | None
    spliced_by_sub: str | None
    spliced_at: datetime | None
    notes: str | None


class PatchConnectionCreate(BaseModel):
    element_layer_id: str
    element_fid: int
    port_number: int
    fiber_cable_layer_id: str | None = None
    fiber_cable_fid: int | None = None
    fiber_number: int | None = None
    fiber_color: str = ""
    connector_type: str = "SC/APC"
    status: str = "free"


class PatchConnectionOut(BaseModel):
    id: int
    element_layer_id: str | None
    element_fid: int | None
    port_number: int
    fiber_cable_layer_id: str | None
    fiber_cable_fid: int | None
    fiber_number: int | None
    fiber_color: str | None
    connector_type: str | None
    status: str | None


class FiberPathSegment(BaseModel):
    segment_type: str  # cable, splice, patch
    from_id: int | None = None
    to_id: int | None = None
    cable_fid: int | None = None
    fiber_number: int | None = None
    loss_db: float = 0.0
    length_m: float = 0.0


class FiberPathOut(BaseModel):
    id: int
    path_name: str
    olt_element_fid: int | None
    olt_port_number: int | None
    onu_element_fid: int | None
    onu_port_number: int | None
    total_loss_db: float | None
    total_length_m: float | None
    status: str | None
    path_segments: list | None
