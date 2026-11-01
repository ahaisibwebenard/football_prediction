"""Local development launcher; production uses the documented uvicorn command."""

import os
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    args, _ = parser.parse_known_args()
    uvicorn.run("backend.main:app", host=args.host, port=args.port)
