
import sys
from awyes.deployment import Deployment


_, root_path, config_path, source_path = sys.argv

Deployment(
    root_path=root_path,
    config_path=config_path,
    source_path=source_path
).deploy()
