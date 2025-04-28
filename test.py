from email.parser import HeaderParser

content_disp = 'form-data; name="fieldName"'

print(dict(
    HeaderParser()
    .parsestr(f"Content-Disposition {content_disp}")
    .get_params(header="Content-Disposition")
))