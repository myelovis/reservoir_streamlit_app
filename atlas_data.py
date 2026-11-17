"""Shared read-only Atlas access for plot data."""
import streamlit as st
from pymongo import MongoClient
from settings import get_secret


class AtlasSetupError(RuntimeError):
    pass


class DatasetNotReady(RuntimeError):
    pass


@st.cache_resource
def atlas_client():
    try:
        uri = get_secret('MONGO_URI')
    except ValueError as error:
        raise AtlasSetupError(str(error)) from None
    return MongoClient(uri, tz_aware=True, serverSelectionTimeoutMS=15000,
                       connectTimeoutMS=15000, socketTimeoutMS=60000, maxPoolSize=10)


def atlas_db():
    return atlas_client()["nve"]

