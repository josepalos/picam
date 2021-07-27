import sys
import traceback
import xmlrpc.client

import server
import picam


def main(address, port):
    s = xmlrpc.client.ServerProxy(f"http://{address}:{port}")

    camera = s.camera  # type: server.CameraWrapper
    storage = s.storage  # type: server.StorageWrapper

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
