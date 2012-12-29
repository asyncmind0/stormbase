function(doc){
    if(doc.doc_type == "Test"){
        emit(doc._id, doc);
    }
}
