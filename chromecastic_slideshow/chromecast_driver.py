import atexit, time
from apscheduler.schedulers.background import BackgroundScheduler

# https://github.com/balloob/pychromecast
import pychromecast

import logging
log = logging.getLogger(__name__)

def _get_cc(cc_name):
    log.info('Looking for all Chromecasts in the network')
    all_casts = pychromecast.get_chromecasts()

    all_cast_names = [cc.name for cc in all_casts[0]]
    if cc_name not in all_cast_names:
        raise KeyError(f'Chromecast {cc_name} not found. Available: {all_cast_names}')
    return [cc for cc in all_casts[0] if cc.name == cc_name][0]


class ChromecastDriver(object):
    class Listener(object):
        def __init__(self, expected_url_prefix, 
                        callback_another_cast_started):
            self.expected_url_prefix = expected_url_prefix
            self.callback_another_cast_started = callback_another_cast_started
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
                self.callback_another_cast_started()

    def __init__(self, target_chromecast_name, img_url_provider, interval_seconds):
        """
        Run a background task: every $interval seconds to load a new url
        in a chromecast, as provided by $img_url_provider
        Constructor will look for all chromcasts in the network (ie: slow)
        target_chromecast: Name of CC to use

        $img_url_provider should provide a unique URL each time it's called
        """
        self.cleanup_on_exit = True
        self.target_chromecast_name = target_chromecast_name
        self.img_url_provider = img_url_provider

        # Get target CC or throw
        self._cc = _get_cc(target_chromecast_name)

        log.info('Found ChromeCast %s, connecting...', target_chromecast_name)
        self._cc.wait()
        self._cc.quit_app()
        self._cc.wait()

        # Register callback for status changes
        self.cc_listener = ChromecastDriver.Listener(img_url_provider.get_url_prefix(),
                                self.on_another_cast_started)
        self._cc.media_controller.register_status_listener(self.cc_listener)

        # Call show_image once to load the first one (otherwise we need to
        # wait for the first interval trigger)
        self.show_image()

        # Call self every $interval_seconds to reload image
        self.scheduler = BackgroundScheduler()
        self.sched_job_obj = self.scheduler.add_job(func=self.show_image,
                               trigger="interval", seconds=int(interval_seconds))
        self.scheduler.start()

        # TODO: Move from atexit to main obj?
        atexit.register(self.disconnect)

    def on_another_cast_started(self):
        log.info('Someone else started casting to %s! Will shutdown...', self.target_chromecast_name)
        # pychromecast doesn't like shutting down while on a listener thread, so
        # instead we remove our 'show new image' job and schedule a disconnect
        self.sched_job_obj.remove()
        self.cleanup_on_exit = False
        print("RQ CLEAN SHUTDOWN")
        self.scheduler.add_job(func=self.disconnect, 
                               trigger="interval", seconds=1)

    def disconnect(self):
        log.info('Shutdown: disconnecting from Chromecast')
        self.scheduler.shutdown()

        if self.cleanup_on_exit:
            self._cc.quit_app()
            self._cc.wait()

        self._cc.disconnect()
        self._cc.join()

    def show_image(self):
        url = self.img_url_provider.get_random_image_url()
        log.info('Asking CC %s to load image %s', self.target_chromecast_name, url)
        # TODO: Hardcoded mime type might break
        self._cc.play_media(url=url, content_type='image/jpeg')
        self._cc.wait()

        # TODO: Configure timeout count
        timeout_count = 5
        while timeout_count > 0:
            if self.cc_listener.last_media == url:
                log.debug('Image should be shown')
                break

            timeout_count -= 1
            try:
                time.sleep(1)
            except Exception as ex:
                raise ex

        if timeout_count == 0:
            log.error('Image display seems to have failed')


