import uvicorn

# 1. Create configuration
config = uvicorn.Config(
    "saleor.asgi:application",  # ASGI app path (module:attribute)
    port=8000,  # Port to listen on
    reload=True,  # Auto-reload on code changes (dev only)
    lifespan="on",  # Enable lifespan events (startup/shutdown)
)

# 2. Create server instance with config
server = uvicorn.Server(config)

# 3. Run the server (blocking call)
server.run()
