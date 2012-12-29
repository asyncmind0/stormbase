function(doc){
    if(doc.doc_type == "Test" && doc.created)
        emit(doc.created, doc);
}

