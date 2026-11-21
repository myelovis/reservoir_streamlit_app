from getpass import getpass
from urllib.parse import quote_plus
from pymongo import MongoClient
import toml
import settings

uri = settings.get_secret("MONGO_URI")
username = "lovisanguyen_db_user"
password = getpass("Working MongoDB password: ")

# Keep the cluster address and safely encode the login.
scheme, remainder = uri.split("://", 1)
address = remainder.rsplit("@", 1)[-1]
new_uri = (
    f"{scheme}://{quote_plus(username)}:"
    f"{quote_plus(password)}@{address}"
)

# Check the connection before saving.
with MongoClient(new_uri, serverSelectionTimeoutMS=10000) as client:
    client.admin.command("ping")

values = dict(settings.saved_settings())
values["MONGO_URI"] = new_uri
settings.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
settings.CONFIG_FILE.write_text(toml.dumps(values), encoding="utf-8")
settings.saved_settings.cache_clear()

print("Corrected MongoDB setting saved.")
