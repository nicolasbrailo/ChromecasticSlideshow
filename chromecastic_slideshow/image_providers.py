import os
import random

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
import threading
from flask import Flask, redirect
from werkzeug.serving import make_server

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
        self.public_host = public_host
        self.port = port
        self.fs_random_imager = fs_random_imager
        self.flask_app = Flask(__name__)
        self.server = make_server(public_host, port, self.flask_app)
        self.bg_thread = threading.Thread(target=self.server.serve_forever)

        @self.flask_app.route('/')
        def _idx():
            return redirect(url_for('/get_random_image/1234'))
        @self.flask_app.route('/get_random_image/<rnd_bit>')
        def _get_random_image(rnd_bit):
            img = fs_random_imager.get_random_image_url()
            fn = os.path.basename(img)
            path = img[0:-len(fn)]
            return flask.send_from_directory(path, fn)

    def run_server(self):
        self.bg_thread.start()

    def stop(self):
        self.server.shutdown()

    def wait_until_server_finishes(self):
        try:
            self.bg_thread.join()
        except KeyboardInterrupt:
            # This Ctrl-C interrupted the join, not Flask, but there doesn't
            # seem to be an easy way to cleanly shutdown Flask. Return anyway
            # so others may have a chance to cleanup
            pass

    def get_url_prefix(self):
        """ All URLs ever provided by this component will start with this prefix """
        return 'http://{}:{}/get_random_image/'.format(self.public_host, self.port)

    def get_random_image_url(self):
        # Add a "random" bit to the make the url unique and to avoid caching
        return '{}{}'.format(self.get_url_prefix(), time.time())


