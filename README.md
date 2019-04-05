# ChromecasticSlideshow

Slideshows in Chromecast directly from your filesystem, without going through any online service. No Google Photos, Facebook or anything else: plain old random files straight from your disk to your Chromecast.

Specify a local path with your pictures, a device to cast to and voila, instant slideshow from your local network.


# How to run
Make sure you have python3.6 and pipenv. This should work in most Linux-like environments:

$ pipenv sync
$ pipenv run python ./chromecastic_slideshow.py


# Setup
To show an image, Chromecast needs to download it from a URL. This app will create a web server which will send random images from the local filesystem, and periodically ask Chromecast to load this URL. This means the PC in which you run this app must be in the same network as the Chromecast: both need to be able to connect to one another.

