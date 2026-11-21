"""Enter credentials once. They stay outside the app folder and ZIP."""
from getpass import getpass
import argparse
import os
import toml
import settings


def configure(ask=getpass):
    values = dict(settings.saved_settings())
    prompts = {'MONGO_URI':'MongoDB Atlas URI, including password (hidden): ',
               'ENTSOE_TOKEN':'ENTSO-E token (hidden): '}
    for name,prompt in prompts.items():
        value = values.get(name) or os.environ.get(name)
        placeholders=['<db_password>','USER:PASSWORD','YOUR_ENTSOE_TOKEN']
        if not value or any(word in str(value) for word in placeholders):
            value = ask(prompt).strip()
        if not value or any(word in str(value) for word in placeholders):
            raise ValueError(f'Provide the real {name}, then run setup again.')
        if name=='MONGO_URI' and not value.startswith(('mongodb://','mongodb+srv://')):
            raise ValueError('Use the full MongoDB connection URI.')
        values[name] = value
    path = settings.CONFIG_FILE
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(toml.dumps(values),encoding='utf-8')
    if os.name!='nt':
        temporary.chmod(0o600)
    temporary.replace(path)
    settings.saved_settings.cache_clear()
    print('Settings saved privately. All local app copies can reuse them.')
    print('Private file:',path)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        configure()
    except ValueError as error:
        parser.error(str(error))

