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

    def get_random_image_url(self):
        rnd = time.time() # Add a "random" bit to the url to avoid caching
        return 'http://{}:{}/get_random_image/{}'.format(
                        self.public_host, self.port, rnd)



import atexit
from apscheduler.schedulers.background import BackgroundScheduler

# https://github.com/balloob/pychromecast
import pychromecast

class ChromecastDriver(object):
    def __init__(self, target_chromecast_name, img_url_provider, interval_seconds):
        """
        Run a background task: every $interval seconds to load a new url
        in a chromecast, as provided by $img_url_provider
        Constructor will look for all chromcasts in the network (ie: slow)
        target_chromecast: Name of CC to use
        """
        self.target_chromecast_name = target_chromecast_name
        self.img_url_provider = img_url_provider
        self.interval_seconds = interval_seconds

        # Try to find the right chromecast
        print('Looking for all Chromecasts in the network')
        all_casts = pychromecast.get_chromecasts()
        try:
            self.cast = next(cc for cc in all_casts
                            if cc.device.friendly_name == target_chromecast_name)
        except StopIteration:
            all_casts_names = [cc.device.friendly_name for cc in all_casts]
            print('Chromecast {} not found. These are available: {}'.format(
                    target_chromecast, all_casts_names))
            raise pychromecast.NoChromecastFoundError()

        print('Found {}, connecting...'.format(self.target_chromecast_name))
        self.cast.wait()
        self.cast.quit_app()
        self.cast.wait()

        # Call show_image once to load the first one (otherwise we need to
        # wait for the first interval trigger)
        self.show_image()

        # Call self every $interval_seconds to reload image
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job(func=self.show_image,
                               trigger="interval", seconds=interval_seconds)
        self.scheduler.start()
        atexit.register(self.disconnect)

    def disconnect(self):
        print('Shutdown: disconnecting from Chromecast')
        self.scheduler.shutdown()
        self.cast.quit_app()
        self.cast.wait()
        self.cast.disconnect()
        self.cast.join()

    def show_image(self):
        url = self.img_url_provider.get_random_image_url()
        print('Asking CC {} to load image {}'.format(self.target_chromecast_name, url))
        # TODO: Hardcoded mime type might break
        self.cast.play_media(url=url, content_type='image/jpeg')
        self.cast.wait()
        print('Image should be shown')


foo = FSRandomImager('/media/laptus/Personal files/Fotos/2012/', ['jpg'])
bar = FSToWebRandomImager(foo, public_host='192.168.2.200', port=5000)
baz = ChromecastDriver('Baticueva TV', bar, interval_seconds=45)
bar.run_server()

