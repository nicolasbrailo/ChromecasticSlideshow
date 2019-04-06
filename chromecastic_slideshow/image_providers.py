import os
import random
import threading

class FSRandomImager(object):
    """ Return random image urls from the local filesystem """

    @staticmethod
    def glob_dir(path, extensions):
        """
        Recursively look for files ending in any of the specified extensions
        using case insensitive match
        """
        files = []
        for file_name in os.listdir(path):
            path_name = os.path.join(path, file_name)
            if os.path.isdir(path_name):
                files.extend(FSRandomImager.glob_dir(path_name, extensions))
            else:
                for ext in extensions:
                    if path_name.lower().endswith(ext):
                        files.append(path_name)
                        break

        return files

    def __init__(self, fs_root, img_types):
        """
        fs_root: base directory where images are located. Will recursively
                     look for images in subdirectories and keep a list in
                     memory (ie this constructor is slow and FS changes won't
                     be reflected on the images list until the object is
                     reconstructed)
        img_types: extensions to look for. Case insensitive.
        """
        self.image_list = FSRandomImager.glob_dir(fs_root, img_types)

    def get_random_image_url(self):
        return random.choice(self.image_list)


import flask
import time
from flask import Flask

class FSToWebRandomImager(object):
    """
    Wrap an FSRandomImager so that local images will be served via an http
    url (using a flask server)

        fs_random_imager: FileSystem random image url provider
        public_host: Listen addr. Needs to be a host that can be accessed
                     by whoever will consume the urls provided by this object
                     (eg: should be a LAN IP if this is to work with a Chromecast)
        port: Listen port
    """
    def __init__(self, fs_random_imager, public_host, port):
        self.bg_thread = None
        self.fs_random_imager = fs_random_imager
        self.public_host = public_host
        self.port = port
        self.flask_app = Flask(__name__)

        @self.flask_app.route('/get_random_image/<rnd_bit>')
        def _get_random_image(rnd_bit):
            img = fs_random_imager.get_random_image_url()
            fn = os.path.basename(img)
            path = img[0:-len(fn)]
            return flask.send_from_directory(path, fn)

    def run_server(self):
        """ Note: blocking, doesn't return """
        self.flask_app.run(host=self.public_host, port=self.port, debug=True)

    def setup_server(self):
        """ Note: non-blocking. Flak's reloader doesn't work in a bg thread, so
        use this method when running this server from a thread """
        def _run():
            self.flask_app.run(host=self.public_host, port=self.port, debug=False)

        self.bg_thread = threading.Thread(target=_run)
        self.bg_thread.start()

    def wait_until_server_finishes(self):
        if self.bg_thread is None:
            raise Exception('Web server not started as background thread')

        self.bg_thread.join()

    def get_random_image_url(self):
        rnd = time.time() # Add a "random" bit to the url to avoid caching
        return 'http://{}:{}/get_random_image/{}'.format(
                        self.public_host, self.port, rnd)


