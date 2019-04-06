import atexit, time
from apscheduler.schedulers.background import BackgroundScheduler

# https://github.com/balloob/pychromecast
import pychromecast

class ChromecastDriver(object):
    class Listener(object):
        def __init__(self, expected_url_prefix):
            self.expected_url_prefix = expected_url_prefix
            self.last_media = None

        def new_media_status(self, status):
            # Sometimes empty status appear. Should be safe to ignore since if
            # content == null then no one must be casting. I hope.
            if status.content_id is None:
                return

            self.last_media = status.content_id

            # If content_id doesn't have our server prefix someone else started
            # casting and we should seppuku
            if self.last_media.find(self.expected_url_prefix) != 0:
                print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")
                print("XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX")

    def __init__(self, target_chromecast_name, img_url_provider, interval_seconds):
        """
        Run a background task: every $interval seconds to load a new url
        in a chromecast, as provided by $img_url_provider
        Constructor will look for all chromcasts in the network (ie: slow)
        target_chromecast: Name of CC to use

        $img_url_provider should provide a unique URL each time it's called
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

        # Register callback for status changes
        self.cc_listener = ChromecastDriver.Listener(img_url_provider.get_url_prefix())
        self.cast.media_controller.register_status_listener(self.cc_listener)

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

        timeout_count = 5
        while timeout_count > 0:
            if self.cc_listener.last_media == url:
                print('Image should be shown')
                break

            timeout_count -= 1
            time.sleep(1)

        if timeout_count == 0:
            print('Image display seems to have failed')


