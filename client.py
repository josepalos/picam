import sys
import traceback
import xmlrpc.client
import server


def main(address, port, extension):
    s = xmlrpc.client.ServerProxy(f"http://{address}:{port}")

    camera = s.camera  # type: server.CameraWrapper
    storage = s.storage  # type: server.StorageWrapper


    camera.open()
    storage.start()
    try:
        new_name = storage.get_new_name(extension)
        print(new_name)
        camera.take_picture(new_name)
    except xmlrpc.client.Fault as err:
        print(err, file=sys.stderr)
    except Exception:
        traceback.print_exc()
    finally:
        camera.close()
