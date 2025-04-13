# utils.py
custom_css = """
body, * {
    font-family: Arial, sans-serif !important;
}
@font-face {
    font-family: 'ui-sans-serif';
    src: local('Arial');
}
@font-face {
    font-family: 'system-ui';
    src: local('Arial');
}
.scrollable {
    max-height: 450px;
    overflow-y: auto;
    z-index: 1;
}
.table-scroll {
    overflow-y: auto;
    overflow-x: auto;
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
    margin-top: 0px;
}
.comment-stats h2 {
    font-size: 1.5em;
}
.report-content h2 {
    font-size: 1.5em;
}
.responsive-image img {
    width: 45%;
    height: 45%;
    display: block;
    margin-left: auto;
    margin-right: auto;
}
#popup-status {
  display: none;
  margin-top: 10px;
  padding: 10px;
  font-weight: bold;
  border-radius: 5px;
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
}
"""