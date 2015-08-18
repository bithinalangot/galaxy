define([], function() {
return {
    'api/datatypes/mapping': {
        data: '{"ext_to_class_name" : {"txt" : "Text", "data":"Data","tabular":"Tabular", "binary": "Binary", "bam": "Bam" }, "class_to_classes": { "Data": { "Data": true }, "Text": { "Text": true, "Data": true }, "Tabular": { "Tabular": true, "Text": true, "Data": true }, "Binary": { "Data": true, "Binary": true }, "Bam": { "Data": true, "Binary": true, "Bam": true }}}'
    },
    'api/datatypes': {
        data: '["RData", "ab1", "affybatch", "txt"]'
    }
}
});
