
import sys
from awyes.deployment import Deployment


_, config_path, source_path = sys.argv

Deployment(
    config_path=config_path,
    source_path=source_path
).deploy()
