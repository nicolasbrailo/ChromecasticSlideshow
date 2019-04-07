from .image_providers import FSRandomImager, FSToWebRandomImager
from .chromecast_driver import ChromecastDriver

class ChromecasticSlideshow(object):
    def __init__(self, logger, root_path, allowed_extensions, public_host,
                 listen_port, target_chromecast_name, interval_seconds):

        self.img_server = FSToWebRandomImager(FSRandomImager(root_path, allowed_extensions),
                                                public_host=public_host, port=listen_port)

        # Start image server in BG without blocking (so that CC driver can be started)
        # Webserver needs to be up and listening before cc_driver, otherwise first request
        # will fail
        self.img_server.setup_server()

        self.cc_driver = ChromecastDriver(logger, target_chromecast_name,
                            self.img_server, interval_seconds=interval_seconds)

        self.img_server.wait_until_server_finishes()


