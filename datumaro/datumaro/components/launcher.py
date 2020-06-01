
# Copyright (C) 2019 Intel Corporation
#
# SPDX-License-Identifier: MIT

import numpy as np

from datumaro.components.extractor import Transform
from datumaro.util import take_by


# pylint: disable=no-self-use
class Launcher:
    def __init__(self, model_dir=None):
        pass

    def launch(self, inputs):
        raise NotImplementedError()

    def preferred_input_size(self):
        return None

    def categories(self):
        return None
# pylint: enable=no-self-use

class ModelTransform(Transform):
    def __init__(self, extractor, launcher, batch_size=1):
        super().__init__(extractor)
        self._launcher = launcher
        self._batch_size = batch_size

    def __iter__(self):
        for batch in take_by(self._extractor, self._batch_size):
            inputs = np.array([item.image.data for item in batch_items])
            inference = self._launcher.launch(inputs)

            for item, annotations in zip(batch, inference):
                yield self.wrap_item(item, annotations=annotations)

    def get_subset(self, name):
        subset = self._extractor.get_subset(name)
        return __class__(subset, self._launcher, self._batch_size)

    def categories(self):
        launcher_override = self._launcher.categories()
        if launcher_override is not None:
            return launcher_override
        return self._extractor.categories()

    def transform_item(self, item):
        inputs = np.expand_dims(item.image, axis=0)
        annotations = self._launcher.launch(inputs)[0]
        return self.wrap_item(item, annotations=annotations)