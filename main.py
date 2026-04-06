import asyncio
import traceback
from src.main import main

try:
    asyncio.run(main())
except Exception:
    traceback.print_exc()
    raise
