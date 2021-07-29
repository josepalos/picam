from io import BytesIO
from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

import numpy.lib.format

from camera import Camera
from storage import Storage


class NotAllowedException(Exception):
    pass


def _marshall_image(image):
    f = BytesIO()
    numpy.lib.format.write_array(f, image._image)
    val = f.getvalue()
    return val


class CameraProxy:
    def __init__(self, camera):
        self._camera = camera
        self._is_open = False
        self._preview_generator = None

    def open(self):
        if self._is_open:
            return
        self._camera.open()
        self._is_open = True

    def close(self):
        self._camera.close()
        self._is_open = False

    def __getattr__(self, item):
        return getattr(self._camera, item)

    def get_exposure_speed(self):
        return float(self._camera.get_exposure_speed())

    def start_preview(self):
        self._preview_generator = self._camera.preview()

    def next_preview_frame(self):
        next_frame = next(self._preview_generator)
        return _marshall_image(next_frame)

    def preview(self):
        raise NotAllowedException


class StorageProxy(Storage):
    def __init__(self, storage):
        self._storage = storage

    def __getattr__(self, item):
        return getattr(self._storage, item)

    def get_image(self, filename):
        return _marshall_image(self._storage.get_image(filename))
        


class Wrapper:
    def __init__(self):
        self.camera = None
        self.storage = None

    def initialize_camera(self, *args, **kwargs):
        self.camera = CameraProxy(Camera(*args, **kwargs))

    def initialize_storage(self, *args, **kwargs):
        self.storage = StorageProxy(Storage(*args, **kwargs))


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2")


def main(address, port, storage_path):
    with SimpleXMLRPCServer((address, port),
                            requestHandler=RequestHandler,
                            logRequests=False,
                            allow_none=True) as server:
        server.register_introspection_functions()

        wrapper = Wrapper()
        wrapper.initialize_camera()
        wrapper.initialize_storage(storage_path)

        server.register_instance(wrapper, allow_dotted_names=True)

        print("Start listening...")
        server.serve_forever()

