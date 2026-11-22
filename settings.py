"""Read one private settings file shared by local app copies."""
from functools import lru_cache
import os
from pathlib import Path
import tomllib

ROOT = Path(__file__).resolve().parent
CONFIG_FILE = Path(os.environ.get('APPDATA',os.environ.get('XDG_CONFIG_HOME',str(Path.home()/'.config')))) / 'NVE_Reservoir_App' / 'secrets.toml'


@lru_cache(maxsize=1)
def saved_settings():
    result = {}
    for path in [ROOT/'.streamlit/secrets.toml',CONFIG_FILE]:
        if path.exists():
            try:
                result.update(tomllib.loads(path.read_text(encoding='utf-8-sig')))
            except tomllib.TOMLDecodeError:
                raise ValueError('The private settings file has invalid TOML. Check its quotes.') from None
    return result


def get_secret(name):
    value = os.environ.get(name) or saved_settings().get(name)
    if not value:
        import streamlit as st
        try:
            value = st.secrets.get(name)
        except (KeyError,FileNotFoundError):
            value = None
    if not value:
        raise ValueError(f'The app owner needs to add {name} to Streamlit Secrets for electricity transfers.')
    return value
