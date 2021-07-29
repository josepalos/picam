import sys
import traceback
import xmlrpc.client
from io import BytesIO

import numpy.lib.format

import picam
from camera import Image


def _unmarshall_image(image):
    data = image.data
    f = BytesIO(data)
    return Image(numpy.lib.format.read_array(f))


class _Proxy:
    def __init__(self, original):
        self._original = original

    def __getattr__(self, item):
        return getattr(self._original, item)


class CameraProxy(_Proxy):
    def __init__(self, rpc_camera):
        super().__init__(rpc_camera)

    def preview(self):
        self._original.start_preview()
        while True:
            yield _unmarshall_image(self._original.next_preview_frame())


class StorageProxy(_Proxy):
    def __init__(self, rpc_storage):
        super().__init__(rpc_storage)

    def get_image(self, filename):
        return _unmarshall_image(self._original.get_image(filename))


def main(address, port):
    s = xmlrpc.client.ServerProxy(f"http://{address}:{port}")

    camera = CameraProxy(s.camera)  # type: CameraProxy
    storage = StorageProxy(s.storage)  # type: StorageProxy

    camera.open()
    storage.start()

    try:
        picam.window(camera, storage)
    except xmlrpc.client.Fault as err:
        print(err, file=sys.stderr)
    except Exception:
        traceback.print_exc()
    finally:
        camera.close()
