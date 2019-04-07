from chromecastic_slideshow import ChromecasticSlideshow
import argparse
import socket


def parse_argv():
    app_descr = """
ChromecasticSlideshow: Slideshows in Chromecast directly from your filesystem, without going through any online service. No Google Photos, Facebook or anything else: plain old random files straight from your disk to your Chromecast.

https://github.com/nicolasbrailo/ChromecasticSlideshow
"""
    class ArgsDescrFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass
    parser = argparse.ArgumentParser(description=app_descr, formatter_class=ArgsDescrFormatter)

    parser.add_argument('-i', '--interval_seconds', default=45,
                        help='Send a new image every $interval_seconds')
    parser.add_argument('-c', '--chromecast_name', type=str, required=True,
                        help='Friendly name of target Chromecast. Leave empty for a list of all Chromecasts')
    parser.add_argument('-H', '--host', required=True, type=str,
                        help='Host name (must be a host which chromecast can access)')
    parser.add_argument('-p', '--listen_port', default=0, type=int, help='Listen port')
    parser.add_argument('-e', '--allowed_extensions', default='jpg', type=str,
                        help='File extensions to cast (eg: jpg,png,bmp)')
    parser.add_argument('root_path', help='Filesystem path for pictures')

    return parser.parse_args()


args = parse_argv()
args.allowed_extensions = args.allowed_extensions.split(',')

if args.listen_port == 0:
    # Pick a random port
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(('localhost', 0))
    args.listen_port = sock.getsockname()[1]
    sock.close()


print('Loading images from {}'.format(args.root_path))

cs = ChromecasticSlideshow(args.root_path, args.allowed_extensions, args.host,
            args.listen_port, args.chromecast_name, args.interval_seconds)

