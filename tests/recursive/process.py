
from pyld import jsonld
from pyld.jsonld import compact, expand, frame
import json

docCache = {}

def load_document_local(url):
    if docCache.has_key(url):
        return docCache[url]

    doc = {
        'contextUrl': None,
        'documentUrl': None,
        'document': ''
    }
    if url == "http://iiif.io/api/presentation/3/context.json":
        fn = "presentation.json"
    elif url == "http://iiif.io/api/presentation/3b/context.json":
        fn = "presentation-b.json"
    elif url == "http://iiif.io/api/image/3/context.json":
    	fn = "image.json"
    elif url == "http://iiif.io/api/image/3b/context.json":
    	fn = "image-b.json"
    elif url == "http://www.w3.org/ns/anno.jsonld":
    	fn = "anno.jsonld"
    else:
    	print url

    fh = file(fn)
    data = fh.read()
    fh.close()
    doc['document'] = data;
    docCache[url] = doc
    return doc

jsonld.set_document_loader(load_document_local)

fh = file('manifest-2.json')
mfst = json.load(fh)
fh.close()

expand(mfst)

