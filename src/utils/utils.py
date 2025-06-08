import os
import random

import numpy as np


def init_seed():
    np.random.seed(0)
    random.seed(0)


def project_path():
    return os.path.join(
        os.path.dirname(    # /opt/mlops/src/utils
            os.path.abspath(__file__)    # /opt/mlops/src/utils/utils/py
        ),
        "..",    # /opt/mlops/src
        ".."     # /opt/mlops -> project_path
    )


def model_dir(model_name):
    return os.path.join(
        project_path(),   # /opt/mlops
        "models",         # /opt/mlops/models
        model_name        # /opt/mlops/models/{model_name}
    )
