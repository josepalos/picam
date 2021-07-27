import sys
import traceback
import xmlrpc.client
from io import BytesIO

import numpy.lib.format

import server
import picam
from camera import Image


class CameraProxy:
    def __init__(self, rpc_camera):
        self._camera = rpc_camera  # type: server.CameraProxy

    def __getattr__(self, item):
        # Proxy the attributes not defined here
        return getattr(self._camera, item)

    def preview(self):
        self._camera.start_preview()
        while True:
            f = BytesIO(self._camera.next_preview_frame().data)
            next_frame = Image(numpy.lib.format.read_array(f))
            yield next_frame


class StorageProxy:
    def __init__(self, rpc_storage):
        self._storage = rpc_storage  # type: server.StorageProxy

    def __getattr__(self, item):
        return getattr(self._storage, item)


def main(address, port):
    s = xmlrpc.client.ServerProxy(f"http://{address}:{port}")

    camera = CameraProxy(s.camera)  # type: CameraProxy
    storage = s.storage  # type: StorageProxy

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
