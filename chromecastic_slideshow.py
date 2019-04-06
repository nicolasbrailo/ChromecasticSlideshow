from chromecastic_slideshow import ChromecasticSlideshow

root_path = '/media/laptus/Personal files/Fotos/'
allowed_extensions = ['jpg']
public_host = '192.168.2.200'
listen_port = 5000
target_chromecast_name = 'Baticueva TV'
interval_seconds = 45

print('Loading images from {}'.format(root_path))

cs = ChromecasticSlideshow(root_path, allowed_extensions, public_host, listen_port,
                target_chromecast_name, interval_seconds)


