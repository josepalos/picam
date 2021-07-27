from xmlrpc.server import SimpleXMLRPCServer, SimpleXMLRPCRequestHandler

from camera import Camera
from storage import Storage


class NotAllowedException(Exception):
    pass


class CameraWrapper(Camera):
    def get_exposure_speed(self):
        return float(super().get_exposure_speed())

    def preview(self):
        raise NotAllowedException


class StorageWrapper(Storage):
    pass


class Wrapper:
    def __init__(self):
        self.camera = None
        self.storage = None

    def initialize_camera(self, *args, **kwargs):
        self.camera = CameraWrapper(*args, **kwargs)

    def initialize_storage(self, *args, **kwargs):
        self.storage = StorageWrapper(*args, **kwargs)


class RequestHandler(SimpleXMLRPCRequestHandler):
    rpc_paths = ("/RPC2")


def main(address, port, storage_path):
    with SimpleXMLRPCServer((address, port),
                            requestHandler=RequestHandler,
                            allow_none=True) as server:
        server.register_introspection_functions()

        wrapper = Wrapper()
        wrapper.initialize_camera()
        wrapper.initialize_storage(storage_path)

        server.register_instance(wrapper, allow_dotted_names=True)

        server.serve_forever()
