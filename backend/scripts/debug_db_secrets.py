
import asyncio
import asyncpg
import json
import os
from cryptography.fernet import Fernet

ENCRYPTION_KEY = "tE9cuWXrAJlSE-7Rw_4es7_YP_oyvYXFwbG8vLsUFfU="
DB_URL = "postgresql://threatvision:threatvision@127.0.0.1:55432/threatvision"

def decrypt_secret(ciphertext: str) -> str:
    if not ciphertext:
        return ""
    f = Fernet(ENCRYPTION_KEY.encode())
    return f.decrypt(ciphertext.encode()).decode()

async def check():
    conn = await asyncpg.connect(DB_URL)
    rows = await conn.fetch("SELECT * FROM user_integration_settings")
    for row in rows:
        print(f"User ID: {row['user_id']}")
        print(f"MISP URL: {row['misp_base_url']}")
        if row['secrets_ciphertext']:
            try:
                dec = decrypt_secret(row['secrets_ciphertext'])
                print(f"Secrets (Decrypted): {dec}")
            except Exception as e:
                print(f"Decryption failed: {e}")
        else:
            print("No secrets ciphertext")
        print(f"Toggles: {row['source_toggles']}")
        print("-" * 20)
    await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
