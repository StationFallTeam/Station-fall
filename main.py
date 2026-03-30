import asyncio
from src.main import main

try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
