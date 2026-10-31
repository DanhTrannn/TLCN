from __future__ import annotations

import logging
from typing import TYPE_CHECKING

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from pyflink.datastream import StreamExecutionEnvironment
    from pyflink.table import StreamTableEnvironment

from pyflink.common import Configuration
from pyflink.datastream import CheckpointingMode, StreamExecutionEnvironment
from pyflink.table import EnvironmentSettings, StreamTableEnvironment


def create_stream_environment(
    checkpoint_interval_ms: int = 10_000,
    checkpoint_dir: str = "file:///opt/flink/checkpoints",
) -> StreamExecutionEnvironment:
    """Create and configure StreamExecutionEnvironment with exactly-once checkpointing."""
    config = Configuration()
    env = StreamExecutionEnvironment.get_execution_environment(config)
    env.enable_checkpointing(checkpoint_interval_ms, CheckpointingMode.EXACTLY_ONCE)
    env.get_checkpoint_config().set_checkpoint_storage_dir(checkpoint_dir)
    env.get_checkpoint_config().set_min_pause_between_checkpoints(5_000)
    env.get_checkpoint_config().set_checkpoint_timeout(60_000)
    return env


def create_table_environment(
    env: StreamExecutionEnvironment,
    pipeline_name: str = "kafka_to_lakehouse_pure_streaming",
) -> StreamTableEnvironment:
    """Create StreamTableEnvironment with streaming settings and pipeline name."""
    t_env = StreamTableEnvironment.create(
        env,
        EnvironmentSettings.new_instance().in_streaming_mode().build(),
    )
    t_env.get_config().set("pipeline.name", pipeline_name)
    t_env.get_config().set("table.local-time-zone", "UTC")
    return t_env
