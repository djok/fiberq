"""End-to-end fiber path tracing algorithm.

Traces a fiber from a starting element port through patch connections,
cables, and splice closures to find the complete path.
"""
import json
import logging

import asyncpg

from fiber_plan.models import FiberPathOut

logger = logging.getLogger("fiberq.fiber_plan.tracer")

MAX_HOPS = 100  # safety limit


async def trace_fiber_path(
    pool: asyncpg.Pool,
    start_element_fid: int,
    start_port_number: int,
    start_element_layer_id: str = "",
) -> FiberPathOut | None:
    """Trace a fiber from a starting port through the network.

    Algorithm:
    1. Start at a patch connection (element port)
    2. Follow the cable + fiber number to the next splice or patch
    3. At a splice, follow the other side (A→B or B→A)
    4. Continue until reaching another patch connection (endpoint) or dead end
    """
    async with pool.acquire() as conn:
        # Find starting patch connection
        if start_element_layer_id:
            start_patch = await conn.fetchrow(
                """SELECT * FROM fiber_patch_connections
                   WHERE element_fid = $1 AND port_number = $2 AND element_layer_id = $3""",
                start_element_fid, start_port_number, start_element_layer_id,
            )
        else:
            start_patch = await conn.fetchrow(
                """SELECT * FROM fiber_patch_connections
                   WHERE element_fid = $1 AND port_number = $2""",
                start_element_fid, start_port_number,
            )

        if not start_patch:
            return None

        segments = []
        total_loss = 0.0
        total_length = 0.0
        visited_splices = set()

        current_cable_layer = start_patch["fiber_cable_layer_id"]
        current_cable_fid = start_patch["fiber_cable_fid"]
        current_fiber_num = start_patch["fiber_number"]

        # Add initial patch segment
        segments.append({
            "type": "patch",
            "element_fid": start_element_fid,
            "port_number": start_port_number,
            "cable_fid": current_cable_fid,
            "fiber_number": current_fiber_num,
        })

        end_element_fid = None
        end_port_number = None

        for hop in range(MAX_HOPS):
            if current_cable_fid is None or current_fiber_num is None:
                break

            # Add cable segment
            segments.append({
                "type": "cable",
                "cable_layer_id": current_cable_layer,
                "cable_fid": current_cable_fid,
                "fiber_number": current_fiber_num,
            })

            # Find splice where this fiber connects
            splice = await conn.fetchrow(
                """SELECT * FROM fiber_splices
                   WHERE (cable_a_layer_id = $1 AND cable_a_fid = $2 AND fiber_a_number = $3)
                      OR (cable_b_layer_id = $1 AND cable_b_fid = $2 AND fiber_b_number = $3)""",
                current_cable_layer, current_cable_fid, current_fiber_num,
            )

            if splice:
                splice_id = splice["id"]
                if splice_id in visited_splices:
                    break  # loop detected
                visited_splices.add(splice_id)

                splice_loss = splice["loss_db"] or 0.0
                total_loss += splice_loss

                # Determine which side we came from and follow the other side
                if (splice["cable_a_layer_id"] == current_cable_layer
                        and splice["cable_a_fid"] == current_cable_fid
                        and splice["fiber_a_number"] == current_fiber_num):
                    # Came from side A → follow to side B
                    current_cable_layer = splice["cable_b_layer_id"]
                    current_cable_fid = splice["cable_b_fid"]
                    current_fiber_num = splice["fiber_b_number"]
                else:
                    # Came from side B → follow to side A
                    current_cable_layer = splice["cable_a_layer_id"]
                    current_cable_fid = splice["cable_a_fid"]
                    current_fiber_num = splice["fiber_a_number"]

                segments.append({
                    "type": "splice",
                    "splice_id": splice_id,
                    "loss_db": splice_loss,
                    "status": splice["status"],
                })
                continue

            # No splice found - check for endpoint patch connection
            end_patch = await conn.fetchrow(
                """SELECT * FROM fiber_patch_connections
                   WHERE fiber_cable_layer_id = $1 AND fiber_cable_fid = $2 AND fiber_number = $3
                   AND NOT (element_fid = $4 AND port_number = $5)""",
                current_cable_layer, current_cable_fid, current_fiber_num,
                start_element_fid, start_port_number,
            )

            if end_patch:
                end_element_fid = end_patch["element_fid"]
                end_port_number = end_patch["port_number"]
                segments.append({
                    "type": "patch",
                    "element_fid": end_element_fid,
                    "port_number": end_port_number,
                    "status": end_patch["status"],
                })

            break  # end of path

        path_name = f"Port {start_element_fid}/{start_port_number}"
        if end_element_fid:
            path_name += f" → Port {end_element_fid}/{end_port_number}"

        return FiberPathOut(
            id=0,
            path_name=path_name,
            olt_element_fid=start_element_fid,
            olt_port_number=start_port_number,
            onu_element_fid=end_element_fid,
            onu_port_number=end_port_number,
            total_loss_db=round(total_loss, 3),
            total_length_m=round(total_length, 1),
            status="traced",
            path_segments=segments,
        )
