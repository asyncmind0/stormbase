function(doc){
    if(doc.doc_type == "Test" && doc._id)
        emit(doc._id, doc);
}

