# utils.py
custom_css = """
.scrollable {
    max-height: 450px;
    overflow-y: auto;
    z-index: 1;
}
.table-scroll {
    max-height: 200px;
    overflow-y: auto;
    overflow-x: hidden;
    width: 100%;
    table-layout: fixed;
    z-index: 2;
}
.table-scroll table {
    width: 100%;
    table-layout: fixed;
}
.table-scroll th, .table-scroll td {
    max-width: 100px;
    width: 11.11%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    text-align: left;
}
.table-scroll th {
    font-size: 0.9em;
}
.table-scroll td {
    font-size: 0.8em;
}
.spacer {
    margin-top: 350px;
    height: 50px;
}
.comment-stats h2 {
    font-size: 1.5em;
}
.report-content h2 {
    font-size: 1.5em;
}
"""