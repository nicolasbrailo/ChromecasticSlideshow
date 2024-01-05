# ChromecasticSlideshow

Slideshows in Chromecast directly from your filesystem, without going through any online service. No Google Photos, Facebook or anything else: plain old random files straight from your disk to your Chromecast.

Specify a local path with your pictures, a device to cast to and voila, instant slideshow from your local network.


# How to run
Make sure you have python3.6 and pipenv/virtualenv. This should work in most Linux-like environments:

Install/set up env:
```
$ cd $this_repo
$ virtualenv chromecastic_slideshow
$ source chromecastic_slideshow/bin/activate
$ pipenv install
$ pipenv sync
$ python ./chromecastic_slideshow.py -h
```

To run:
```
$ LAN_IP=$(ip a | grep 192.168.1 | awk '{print $2}' | sed 's#/24##g')
$ python ./chromecastic_slideshow.py -H $LAN_IP -c $CHROMECAST_NAME /path/to/pictures
```

LAN_IP will probably fail in all but most basic setups, but you can use `ip a` to find out an ip address that your Chromecast can access.

# How it works
To show an image, Chromecast needs to download it from a URL. This app will create a web server which will send random images from the local filesystem, and periodically ask Chromecast to load this URL. This means the PC in which you run this app must be in the same network as the Chromecast: both need to be able to connect to one another.

