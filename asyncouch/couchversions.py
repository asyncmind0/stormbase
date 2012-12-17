from diff_match_patch import diff_match_patch as dmp
from uuid import uuid4
from datetime import datetime
from couchadapter import Document


class Diff(Document):
    default = Document.add_defaults(
        original_docid='',
        date=datetime.utcnow())

    def add_diff(self, original_doc, name, value):
        _differ = dmp()
        if isinstance(value, basestring):
            old_text = original_doc.get(name, '')
            result = _differ.diff_main(old_text, value)
            self[name] = result
        original_doc[name] = value

    def get_html(self, key):
        _differ = dmp()
        return _differ.make_prettyHtml(self[key])

    def store_diff(self, old_document, new_document, keys):
        for key in keys:
            old_text = old_document.get(key, '')
            new_text = new_document.get(key, '')
            result = self._differ.compare(old_text.splitlines(1),
                                          new_text.splitlines(1))
            self[key] = result
