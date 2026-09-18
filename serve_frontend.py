import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit


class SPARequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory: str, **kwargs):
        self.site_directory = Path(directory).resolve()
        super().__init__(*args, directory=str(self.site_directory), **kwargs)

    def do_GET(self):
        request_path = urlsplit(self.path).path
        requested_file = (self.site_directory / request_path.lstrip("/")).resolve()
        is_site_file = requested_file == self.site_directory or self.site_directory in requested_file.parents

        if request_path != "/" and (not is_site_file or not requested_file.is_file()):
            self.path = "/index.html"

        super().do_GET()

    def end_headers(self):
        if urlsplit(self.path).path == "/index.html":
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description="Serve the built Vue SPA.")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--directory", default="dist")
    args = parser.parse_args()

    handler = lambda *handler_args, **handler_kwargs: SPARequestHandler(
        *handler_args,
        directory=args.directory,
        **handler_kwargs,
    )
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"Serving {Path(args.directory).resolve()} on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
