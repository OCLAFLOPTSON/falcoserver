from uos import stat
from sys import print_exception
from FalcoServer.server import Response
from FalcoServer import FileNotFound

def render_template(file_path, **values):
    '''
    Parses a given html file at file_path and returns a Response object 
    with a dynamically built body.\n
    Keyword Arguments are passed into the template.\n
    Supported Data Types:
        Character Strings, Integers, Floats:
            Converted to string and 
            passed as is.\n
        Boolean Values:
            Evaluated and passed according to template logic.\n
        Extended Templates:
            Evaluated first and injected into current template.\n
    API:
        {{ generic_value }}:
            Pass generic values into the document.
        {{ extends *file_path* }}:
            Extend an html file found at the given file path.
        {{ content }}:
            For use in an extended file, the location to which 
            child content will appear within the extended document.
        {{ if *conditional* }}:
            Opening conditional bracket. Conditional is boolean.
            HTML within this block will be conditionally rendered.
        {{ else }}:
            HTML within this block rendered only if parent if block
            is false.
        {{ end if }}:
            Closes the conditional block.
        {{ css *file_path* }}:
            Link to a static css file at the given file path.
        {{ script *file_path* }}:
            Link to a static javascript file at the given file path.
    '''

    try:
        def source(path):
            try:
                stat(path)
                with open(path, "r") as f:
                    for line in f:
                        yield line
            except OSError:
                raise FileNotFound(path)

        def _extends(stream):
            try:
                first = next(stream)
            except StopIteration as e:
                print_exception(e)
                first = ''
            try:
                stripped = first.strip()
                if stripped.startswith('{{ extends'):
                    path = stripped.split()[2]
                    try:
                        stat(path)
                    except OSError as e:
                        print_exception(e)
                        raise FileNotFound(path)
                    with open(path, "r") as f:
                        for line in f:
                            if "{{ content }}" in line:
                                for child_line in stream:
                                    yield child_line
                            else:
                                yield line
                else:
                    yield first
                    for line in stream:
                        yield line
            except Exception as e:
                print_exception(e)

        def _if_else(stream):
            state = False
            active = False
            try:
                for line in stream:
                    stripped = line.strip()
                    if stripped.startswith("{{ if ") and stripped.endswith(" }}"):
                        if active:
                            raise ValueError("Nested if blocks not supported.")
                        key = stripped[6:-3].strip()
                        state = bool(values.get(key, False))
                        active = True
                        continue
                    if stripped == "{{ else }}":
                        if not active:
                            raise ValueError("else without if")
                        state = not state
                        continue
                    if stripped == "{{ end if }}":
                        if not active:
                            raise ValueError("end if without if")
                        state = False
                        active = False
                        continue
                    if stripped.startswith("{{ bool ") and stripped.endswith(" }}"):
                        key = stripped[7:-3].strip()
                        emit = bool(values.get(key, False))
                        for bool_line in stream:
                            if bool_line.strip() == "{{ end bool }}":
                                break
                            if emit:
                                yield bool_line
                        continue
                    if not active:
                        yield line
                        continue
                    if state:
                        yield line
            except Exception as e:
                print_exception(e)

        def _values(stream):
            try:
                for line in stream:
                    out = ""
                    i = 0
                    while True:
                        start = line.find("{{", i)
                        if start == -1:
                            out += line[i:]
                            break
                        end = line.find("}}", start)
                        if end == -1:
                            out += line[i:]
                            break
                        out += line[i:start]
                        tag = line[start + 2:end].strip()
                        if (
                            tag.startswith("if ")
                            or tag == "else"
                            or tag == "end if"
                            or tag.startswith("extends")
                            or tag == "content"
                            or tag.startswith("bool ")
                            or tag == "end bool"
                        ):
                            out += line[start:end + 1]
                        elif tag.startswith("css "):
                            css_path = tag[4:].strip()
                            try:
                                stat(css_path)
                                with open(css_path, "r") as f:
                                    css_content = f.read()
                                out += "<style>\n"+css_content+"\n</style>"
                            except OSError as e:
                                out += f'<~ CSS file "{css_path}" not found ~>'
                        elif tag.startswith("script "):
                            script_path = tag[7:].strip()
                            try:
                                stat(script_path)
                                with open(script_path, 'r') as f:
                                    script_content = f.read()
                                out += "<script>\n"+script_content+"\n</script>"
                            except OSError:
                                out += f'<~ SCRIPT file "{script_path}" not found ~>'
                        else:
                            parts = tag.split()
                            if len(parts) == 2 and parts[0] == "value":
                                key = parts[1]
                                out += str(values.get(key, ""))
                            elif len(parts) == 1:
                                key = parts[0]
                                out += str(values.get(key, ""))
                            else:
                                out += line[start:end + 2]
                        i = end + 2
                    yield out
            except Exception as e:
                print_exception(e)

        def body():
            try:
                stream = source(file_path)
                stream = _extends(stream)
                stream = _if_else(stream)
                stream = _values(stream)
                for chunk in stream:
                    if isinstance(chunk, str):
                        yield chunk.encode("utf-8")
                    else:
                        yield chunk
            except Exception as e:
                print_exception(e)
        return Response(
            body(),
            200,
            {"Content-Type": "text/html"}
        )
    except Exception as e:
        print_exception(e)

