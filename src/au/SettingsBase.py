from pathlib import Path
from tomlkit import loads, dumps, TOMLDocument
from tomlkit.container import Container

class SettingsBase:
    FILENAME = 'settings.toml'

    def __init__(self, settings_doc_file: Path|str, create: bool = False):
        file = Path(settings_doc_file)
        exists = file.exists()
        if not create and not exists:
            raise FileNotFoundError(f"{file} does not exist")
        self._settings_doc_file = file
        self.is_dirty = False
        if exists:
            self.read()
        else:
            self.settings_doc = TOMLDocument()
            self.write()
            

    def __enter__(self):
        if not self.is_dirty:
            self.read()
        return self

    def __exit__(self, type, value, traceback):
        if self.is_dirty:
            self.write()

    def get(self, dotted_name: str, is_path=False) -> any:
        parts = dotted_name.split('.')
        doc = self.settings_doc
        for part in parts:
            doc = doc.get(part)
            if not doc:
                return None
        val = doc
        if is_path:
            path = Path(val)
            if not path.is_absolute():
                path = (self.settings_doc_path / path).resolve()
            val = path
        return val

    def set(self, dotted_name: str, val: any) -> any:
        parts = dotted_name.split('.')
        doc = self.settings_doc
        for part in parts[:-1]:
            doc = doc.setdefault(part, Container())
        if val is None:
            doc[parts[-1]] = ''
        elif isinstance(val, Path):
            try:
                val = val.resolve()
                doc_path = self.settings_doc_path.resolve()
                relative_path = val.relative_to(doc_path, walk_up=True).as_posix()
                doc[parts[-1]] = str(relative_path)
            except:
                doc[parts[-1]] = str(val)
        else:
            try:
                doc[parts[-1]] = val
            except:
                doc[parts[-1]] = str(val)
        self.is_dirty = True
    
    @property
    def settings_doc_path(self) -> Path:
        return self._settings_doc_file.parent

    @property
    def settings_doc(self) -> TOMLDocument:
        return self._settings_doc
    @settings_doc.setter
    def settings_doc(self, value):
        self._settings_doc = value

    def read(self):
        with open(self._settings_doc_file, 'rt') as fi:
            self.settings_doc = loads(fi.read())
            self.is_dirty = False

    def write(self):
        with open(self._settings_doc_file, 'wt') as fi:
            fi.write(dumps(self.settings_doc))
        self.is_dirty = False
