from stormbase.asyncouch.couchadapter import Document
from stormbase.tuct import tuct

from diff_match_patch import diff_match_patch as dmp
from uuid import uuid4
from datetime import datetime


class Diff(Document):
    defaults = tuct(
        original_docid='',
        date=datetime.utcnow())

    def add_diff(self, original_doc, name, value):
        _differ = dmp()
        if isinstance(value, basestring):
            old_text = original_doc.get(name, '')
            #result = _differ.diff_main(old_text, value)
            result = _differ.patch_make(value, old_text)
            result = _differ.patch_toText(result)
            self[name] = result
        original_doc[name] = value

    def prev_version(self, current_doc, name):
        _differ = dmp()
        result = ''
        current_text = current_doc.get(name, '')
        patch = self[name]
        #result = _differ.diff_main(old_text, value)
        result = _differ.patch_fromText(patch)
        result = _differ.patch_apply(result, current_text)
        return result

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
