"""Shared read-only Atlas access for plot data."""
import os
import streamlit as st
from pymongo import MongoClient


class AtlasSetupError(RuntimeError):
    pass


class DatasetNotReady(RuntimeError):
    pass


@st.cache_resource
def atlas_client():
    uri = os.environ.get("MONGO_URI")
    if not uri:
        try:
            uri = st.secrets["MONGO_URI"]
        except (KeyError, FileNotFoundError):
            raise AtlasSetupError("Set MONGO_URI in Streamlit Secrets, then refresh. Do not put credentials in GitHub.") from None
    return MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=15000,
                       connectTimeoutMS=15000, socketTimeoutMS=60000, maxPoolSize=10)


def atlas_db():
    return atlas_client()["nve"]
